"""合规检查 Pipeline"""

import json
from .parser import parse_document
from ..llm.openai_compat import OpenAICompatibleLLM


async def run_compliance_check(tender_id: int, tender_path: str, bid_path: str):
    """执行合规检查，流式返回结果"""
    llm = OpenAICompatibleLLM()

    tender_doc = parse_document(tender_path)
    bid_doc = parse_document(bid_path)

    # 截断文档，避免 LLM 调用过慢
    tender_text = tender_doc.full_text[:4000]
    bid_text = bid_doc.full_text[:4000]

    yield json.dumps({"type": "status", "message": "正在解析招标文件要求...（预计需60秒，请耐心等待）"}, ensure_ascii=False) + "\n"

    # 第一步：从招标文件中提取所有要求项
    extract_prompt = f"""请从以下招标文件中提取所有对投标书的**合规要求项**，以 JSON 数组格式输出。

对每条要求必须包含以下字段：
- index: 序号（从1开始）
- desc: 要求的具体描述（一句话概括）
- category: 类别（资格/技术/商务/格式）
- risk_if_missing: 缺失风险等级（high=可能导致废标，medium=影响评分）

严格按照以下 JSON 格式输出，不要输出任何解释文字，只输出 JSON：
[{{
  "index": 1,
  "desc": "要求的具体描述",
  "category": "资格",
  "risk_if_missing": "high"
}}]

招标文件内容：
{tender_text}"""

    messages = [
        {"role": "system", "content": "你是一位招投标合规专家。请精确提取招标文件中的所有合规要求项，严格按 JSON 数组格式输出。每个元素是一个包含 index/desc/category/risk_if_missing 的对象，不是字符串！"},
        {"role": "user", "content": extract_prompt},
    ]
    requirements_text = await llm.chat_complete(messages)

    # 解析要求列表
    requirements = _parse_requirements(requirements_text)

    yield json.dumps({"type": "requirements", "count": len(requirements)}, ensure_ascii=False) + "\n"

    # 第二步：逐条检查
    results = []
    for i, req in enumerate(requirements):
        idx = req.get("index", i + 1)
        desc = req.get("desc", str(req))
        category = req.get("category", "其他")

        yield json.dumps({"type": "checking", "item_index": idx, "item_desc": desc, "total": len(requirements)}, ensure_ascii=False) + "\n"

        check_prompt = f"""请检查投标书是否满足以下要求：

**要求项**（来源：招标文件）：{desc}
**要求类别**：{category}

**投标书内容**：
{bid_text}

请判断是否满足该要求，并给出风险等级：
- 严重：完全缺失或严重不符，可能导致废标
- 高：存在重大缺陷，得分会很低
- 中：部分满足，有小问题
- 低：基本满足，有细微瑕疵

严格按 JSON 格式回复（不要代码块）：
{{"status": "已满足", "risk_level": "低", "remark": "具体判断依据"}}"""

        check_messages = [
            {"role": "system", "content": "你是一位严格的招投标合规审查专家。只输出 JSON 格式结果，不要任何其他文字。"},
            {"role": "user", "content": check_prompt},
        ]
        check_text = await llm.chat_complete(check_messages)

        try:
            check_result = json.loads(_extract_json(check_text))
        except (json.JSONDecodeError, ValueError):
            check_result = {"status": "待确认", "risk_level": "中", "remark": "无法自动判断"}

        result = {
            "item_index": idx,
            "item_desc": desc,
            "category": category,
            "risk_level": check_result.get("risk_level", "中"),
            "page_ref": "",
            "status": check_result.get("status", "待确认"),
            "remark": check_result.get("remark", ""),
        }
        results.append(result)
        yield json.dumps({"type": "item_result", "data": result}, ensure_ascii=False) + "\n"

    # 汇总
    summary = {"severe": 0, "high": 0, "medium": 0, "low": 0}
    level_map = {"严重": "severe", "高": "high", "中": "medium", "低": "low"}
    for r in results:
        key = level_map.get(r["risk_level"], "medium")
        summary[key] += 1

    yield json.dumps({"type": "summary", "data": {"summary": summary, "items": results}}, ensure_ascii=False) + "\n"
    yield json.dumps({"type": "done"}, ensure_ascii=False) + "\n"

    await llm.close()


def _parse_requirements(requirements_text: str) -> list[dict]:
    """解析 LLM 返回的要求列表，处理字符串数组和对象数组两种格式"""
    json_str = _extract_json(requirements_text)
    try:
        data = json.loads(json_str)
    except (json.JSONDecodeError, ValueError):
        return [{"index": 1, "desc": "无法解析招标要求", "category": "其他", "risk_if_missing": "high"}]

    if not isinstance(data, list):
        return [{"index": 1, "desc": "无法解析招标要求", "category": "其他", "risk_if_missing": "high"}]

    result = []
    for i, item in enumerate(data):
        if isinstance(item, dict):
            result.append(item)
        elif isinstance(item, str):
            # LLM 返回了字符串数组，自动转换为对象格式
            result.append({
                "index": i + 1,
                "desc": item,
                "category": "其他",
                "risk_if_missing": "medium",
            })
        else:
            result.append({
                "index": i + 1,
                "desc": str(item),
                "category": "其他",
                "risk_if_missing": "medium",
            })
    return result if result else [
        {"index": 1, "desc": "未提取到任何要求", "category": "其他", "risk_if_missing": "high"}
    ]


def _extract_json(text: str) -> str:
    """从 LLM 返回的文本中提取 JSON 块"""
    text = text.strip()
    # 尝试找 ```json ... ``` 代码块
    if "```json" in text:
        start = text.index("```json") + 7
        end = text.index("```", start)
        return text[start:end].strip()
    if "```" in text:
        start = text.index("```") + 3
        end = text.index("```", start)
        return text[start:end].strip()
    # 先找 [ 数组，再找 { 对象（数组优先，因为数组内可能包含对象）
    if "[" in text:
        start = text.index("[")
        end = text.rindex("]") + 1
        return text[start:end]
    if "{" in text:
        start = text.index("{")
        end = text.rindex("}") + 1
        return text[start:end]
    return text
