"""标书完整性检查 — 对比招标文件分析结果找缺失信息"""

import json
import re
from datetime import datetime
from sqlalchemy.orm import Session
from ..models.bid import Bid, BidChapter
from ..models.tender import AnalysisModule
from ..llm.openai_compat import OpenAICompatibleLLM


INSPECT_MODULES = [4, 5, 7, 8, 9, 10]  # 合标要求、废标要求、关键项要求、商务条款要求、报价要求、标书检查清单


def _extract_json(text: str) -> list:
    """从 LLM 返回中提取 JSON 数组"""
    text = text.strip()
    # 去掉 markdown 代码块
    m = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
    if m:
        text = m.group(1).strip()
    # 找最外层方括号
    start = text.find('[')
    end = text.rfind(']')
    if start != -1 and end > start:
        text = text[start:end + 1]
    return json.loads(text)


async def inspect_bid(bid_id: int, db: Session) -> list[dict]:
    """分析标书，返回缺失信息列表"""
    bid = db.query(Bid).filter(Bid.id == bid_id).first()
    if not bid:
        raise ValueError("标书不存在")

    chapters = db.query(BidChapter).filter(
        BidChapter.bid_id == bid_id
    ).order_by(BidChapter.chapter_index).all()

    tender_context = ""
    if bid.tender_id:
        modules = db.query(AnalysisModule).filter(
            AnalysisModule.tender_id == bid.tender_id,
            AnalysisModule.module_index.in_(INSPECT_MODULES),
        ).order_by(AnalysisModule.module_index).all()
        tender_context = "\n\n".join([
            f"### {m.module_name}（模块{m.module_index}）\n{m.content}"
            for m in modules if m.content
        ])

    if not tender_context:
        return []

    # 构建标书全文
    bid_text_parts = []
    for ch in chapters:
        content = ch.content or "（无内容）"
        # 截断过长章节
        if len(content) > 3000:
            content = content[:3000] + "\n...（内容过长已截断）"
        bid_text_parts.append(f"### 第{ch.chapter_index}章 {ch.title}\n{content}")
    bid_full_text = "\n\n".join(bid_text_parts)

    llm = OpenAICompatibleLLM()

    prompt = f"""## 招标文件分析结果（关键要求）

{tender_context}

## 标书完整内容

{bid_full_text}

## 任务

请逐条比对招标文件分析结果与标书内容，找出所有**标书中缺失、不完整或仅用占位符未填写**的关键信息。

重点关注以下类型的问题：
1. 合标要求（资格条件）：标书中是否包含了所有要求的资质证明、业绩证明、人员证书等
2. 废标要求：标书中是否避免了所有可能导致废标的格式/内容缺陷
3. 关键项要求：评分中的关键得分点是否在标书中有充分体现
4. 商务条款：付款方式、工期、质保期等是否明确响应
5. 报价要求：报价方式、明细、计算等是否完整
6. 格式与签字盖章：是否说明了需要的签字盖章位置

对于每个缺失项，输出以下信息：
- field_name: 缺失项的简明名称（中文，不超过20字）
- description: 详细说明，包括为什么重要、应该填写什么内容
- suggested_chapter_index: 建议在哪个章节补充（对应标书的章节序号）
- suggested_chapter_title: 建议章节的名称
- priority: "必须"（缺失可能导致废标）、"重要"（影响得分）、"建议"（锦上添花）
- category: "资格"、"商务"、"技术"、"报价"、"格式"

输出格式（纯 JSON 数组，不要代码块标记）：
[
  {{
    "field_name": "...",
    "description": "...",
    "suggested_chapter_index": N,
    "suggested_chapter_title": "...",
    "priority": "必须|重要|建议",
    "category": "资格|商务|技术|报价|格式"
  }}
]

重要规则：
1. 不要报告已经在标书中明确出现了 {{占位符}} 的字段（这些由占位符扫描处理）
2. 只报告在标书正文中完全缺失的关键信息
3. 每个缺失项必须是具体的、可操作的
4. 如果标书中某一项已经充分满足，不要报告
5. 每个 field_name 不超过20个中文字符"""

    messages = [
        {"role": "system", "content": "你是一位资深招投标专家，擅长将标书与招标文件要求进行比对，发现标书中缺失、不完整或不满足要求的关键信息。直接输出 JSON 数组，不要任何解释。"},
        {"role": "user", "content": prompt},
    ]

    result = await llm.chat_complete(messages)
    await llm.close()

    try:
        return _extract_json(result)
    except (json.JSONDecodeError, ValueError):
        return []


async def fill_missing_fields_stream(
    bid_id: int,
    missing_fields: list[dict],
    field_values: dict[str, str],
    db: Session,
):
    """将用户填写的信息融入各章节，SSE 流式返回进度"""
    chapters = db.query(BidChapter).filter(
        BidChapter.bid_id == bid_id
    ).order_by(BidChapter.chapter_index).all()

    # 按章节归组
    chapter_fields: dict[int, list[dict]] = {}
    for f in missing_fields:
        fname = f.get("field_name", "")
        if fname in field_values:
            ci = f.get("suggested_chapter_index", 1)
            if ci not in chapter_fields:
                chapter_fields[ci] = []
            chapter_fields[ci].append({**f, "filled_value": field_values[fname]})

    if not chapter_fields:
        yield f"event: done\ndata: {json.dumps({'status': 'no_fields', 'message': '没有需要填写的信息'}, ensure_ascii=False)}\n\n"
        return

    llm = OpenAICompatibleLLM()

    for ci, fields in chapter_fields.items():
        chapter = next((c for c in chapters if c.chapter_index == ci), None)
        if not chapter or not chapter.content:
            continue

        yield f"event: chapter_start\ndata: {json.dumps({'chapter_index': ci, 'chapter_title': chapter.title, 'fields_count': len(fields)}, ensure_ascii=False)}\n\n"

        # 构建补充信息列表
        supplements = "\n".join([
            f"- **{f['field_name']}**：{f['filled_value']}\n  （说明：{f.get('description', '')}）"
            for f in fields
        ])

        prompt = f"""## 当前章节内容

{chapter.content}

## 需要补充的信息

{supplements}

## 任务

请将上述"需要补充的信息"自然地融入当前章节内容中。要求：
1. **严格保留**原有内容的所有文字、结构和格式，不得删除或缩减任何已有内容
2. 在适当的位置插入补充信息，使其读起来自然流畅
3. 如果某个信息在原文中已有类似占位符，替换它
4. 如果某个信息是全新的，在相关段落末尾或合适位置新增
5. 保持标书的正式、专业语气
6. 直接输出修改后的完整章节内容，不要任何解释、开场白或总结"""

        messages = [
            {"role": "system", "content": "你是标书撰写专家，擅长在不破坏原有内容结构的前提下，将补充信息自然地融入标书章节中。直接输出修改后的章节正文，不输出任何对话性内容。"},
            {"role": "user", "content": prompt},
        ]

        new_content = await llm.chat_complete(messages)
        chapter.content = new_content
        chapter.last_modified = datetime.now()
        db.commit()

        yield f"event: chapter_done\ndata: {json.dumps({'chapter_index': ci, 'chapter_title': chapter.title, 'status': 'done'}, ensure_ascii=False)}\n\n"

    await llm.close()
    yield f"event: done\ndata: {json.dumps({'status': 'completed', 'chapters_updated': len(chapter_fields)}, ensure_ascii=False)}\n\n"
