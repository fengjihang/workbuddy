"""10 模块招标文件解读 Pipeline — 支持断点续传"""

import json
from sqlalchemy.orm import Session
from .parser import parse_document, ParsedDocument
from ..llm.openai_compat import OpenAICompatibleLLM
from ..models.tender import AnalysisModule

ANALYSIS_MODULES = [
    {"index": 1, "name": "项目基本信息"},
    {"index": 2, "name": "采购背景与需求分析"},
    {"index": 3, "name": "控标风险分析"},
    {"index": 4, "name": "合标要求"},
    {"index": 5, "name": "废标要求"},
    {"index": 6, "name": "评审项要求"},
    {"index": 7, "name": "关键项要求"},
    {"index": 8, "name": "商务条款要求"},
    {"index": 9, "name": "报价要求"},
    {"index": 10, "name": "标书检查清单"},
]


def get_done_indices(db: Session, tender_id: int) -> set[int]:
    rows = db.query(AnalysisModule).filter(
        AnalysisModule.tender_id == tender_id,
        AnalysisModule.status == "已完成",
    ).all()
    return {r.module_index for r in rows}


def need_resume(db: Session, tender_id: int) -> bool:
    """是否有已完成的模块（说明之前解读过但被中断）"""
    return len(get_done_indices(db, tender_id)) > 0


async def run_analysis(tender_id: int, file_path: str, db: Session):
    """逐模块执行解读，已完成模块跳过，每完成一个即入库"""
    llm = OpenAICompatibleLLM()
    doc: ParsedDocument = parse_document(file_path)
    done_indices = get_done_indices(db, tender_id)

    for module in ANALYSIS_MODULES:
        idx = module["index"]
        name = module["name"]

        if idx in done_indices:
            # 跳过已完成的模块，直接通知前端
            existing = db.query(AnalysisModule).filter(
                AnalysisModule.tender_id == tender_id,
                AnalysisModule.module_index == idx,
            ).first()
            yield _sse("module_done", {
                "module_index": idx,
                "module_name": name,
                "content": existing.content if existing else "",
                "skipped": True,
            })
            continue

        yield _sse("module_start", {"module_index": idx, "module_name": name})

        # 创建或更新模块记录
        module_record = db.query(AnalysisModule).filter(
            AnalysisModule.tender_id == tender_id,
            AnalysisModule.module_index == idx,
        ).first()
        if not module_record:
            module_record = AnalysisModule(
                tender_id=tender_id,
                module_index=idx,
                module_name=name,
                status="进行中",
            )
            db.add(module_record)
        else:
            module_record.status = "进行中"
        db.commit()

        prompt = _build_analysis_prompt(module_name=name, doc_text=doc.full_text, module_index=idx)
        messages = [
            {"role": "system", "content": "你是一位资深的招投标分析专家。请对招标文件进行专业解读，内容详尽、条理清晰。"},
            {"role": "user", "content": prompt},
        ]

        full_content = ""
        try:
            async for token in llm.chat(messages, stream=True):
                full_content += token
                yield _sse("module_chunk", {"module_index": idx, "delta": token})
        except Exception as e:
            module_record.status = "等待中"
            module_record.content = full_content or None
            db.commit()
            yield _sse("module_error", {"module_index": idx, "message": str(e)})
            continue

        # 完成后立即入库
        module_record.content = full_content
        module_record.status = "已完成"
        db.commit()

        yield _sse("module_done", {"module_index": idx, "module_name": name, "content": full_content})

    yield _sse("done", {"status": "completed", "modules_count": len(ANALYSIS_MODULES)})
    await llm.close()


def _build_analysis_prompt(module_name: str, doc_text: str, module_index: int) -> str:
    prompts = {
        "项目基本信息": (
            "请根据以下招标文件内容，提取并整理**项目基本信息**，包括但不限于：\n"
            "- 项目名称、编号\n- 采购单位\n- 采购代理机构\n- 预算金额/最高限价\n"
            "- 项目地点\n- 资金来源\n- 采购方式\n- 是否接受联合体\n\n"
            f"招标文件内容：\n{doc_text[:8000]}"
        ),
        "采购背景与需求分析": (
            "请根据以下招标文件内容，深入分析**采购背景与需求**：\n"
            "- 项目背景与建设目标\n- 采购需求概述\n- 技术/服务需求要点\n"
            "- 商务需求要点\n- 需求中的特殊关注点\n\n"
            f"招标文件内容：\n{doc_text[:8000]}"
        ),
        "控标风险分析": (
            "请仔细审查以下招标文件，识别潜在的**控标风险**，包括但不限于：\n"
            "- 资格条件是否指向特定供应商\n- 技术参数是否有排他性\n"
            "- 评分标准是否存在倾向性\n- 是否存在不合理的时间安排\n"
            "- 是否存在其他限制竞争的条款\n\n"
            "对每个风险点说明风险等级（高/中/低）和理由。\n\n"
            f"招标文件内容：\n{doc_text[:8000]}"
        ),
        "合标要求": (
            "请根据招标文件内容，逐条列出**合标要求**（投标人必须满足的资格条件）：\n"
            "- 基本资格要求（营业执照、纳税、社保等）\n- 特定资格要求（资质证书等）\n"
            "- 业绩要求\n- 人员要求\n- 财务要求\n- 其他门槛条件\n\n"
            f"招标文件内容：\n{doc_text[:8000]}"
        ),
        "废标要求": (
            "请根据招标文件内容，逐条列出**废标条款**（导致投标被否决的情形）：\n"
            "- 形式审查废标项\n- 资格审查废标项\n"
            "- 响应性审查废标项\n- 低于成本价废标项\n"
            "- 其他废标情形\n\n对每个条款标注原文位置和风险严重程度。\n\n"
            f"招标文件内容：\n{doc_text[:8000]}"
        ),
        "评审项要求": (
            "请根据招标文件内容，逐条列出**评审项要求**（评分标准）：\n"
            "- 价格评分项及分值\n- 技术评分项及分值\n- 商务评分项及分值\n"
            "- 其他评分项\n- 评分规则与计算方法\n\n"
            f"招标文件内容：\n{doc_text[:8000]}"
        ),
        "关键项要求": (
            "请根据招标文件内容，列出**关键项要求**（必须满分或高分的关键评审点）：\n"
            "- 技术方案关键点\n- 项目实施方案关键点\n- 人员配置关键点\n"
            "- 售后服务关键点\n- 其他决定性因素\n\n"
            f"招标文件内容：\n{doc_text[:8000]}"
        ),
        "商务条款要求": (
            "请根据招标文件内容，逐条列出**商务条款要求**：\n"
            "- 合同主要条款\n- 付款方式\n- 交付/工期要求\n"
            "- 质保期要求\n- 售后服务要求\n- 违约责任\n- 其他商务条款\n\n"
            f"招标文件内容：\n{doc_text[:8000]}"
        ),
        "报价要求": (
            "请根据招标文件内容，逐条列出**报价要求**：\n"
            "- 报价方式（总价/单价/下浮率等）\n- 报价包含范围\n"
            "- 最高限价\n- 报价得分计算公式\n- 报价注意事项\n\n"
            f"招标文件内容：\n{doc_text[:8000]}"
        ),
        "标书检查清单": (
            "请根据招标文件内容，生成一份完整的**标书检查清单**，格式如下：\n"
            "每个检查项按以下结构输出：\n"
            "序号 | 检查项描述 | 类别（格式/资格/技术/商务/报价） | 优先级（高/中/低） | 备注\n\n"
            "要求覆盖所有可能遗漏的文件和签字盖章要求。\n\n"
            f"招标文件内容：\n{doc_text[:8000]}"
        ),
    }
    return prompts.get(module_name, f"请分析以下招标文件的「{module_name}」相关内容：\n\n{doc_text[:8000]}")


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
