# -*- coding: utf-8 -*-

import sys
from pathlib import Path

from config_loader import load_config


def normalize_text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def article_json_schema_for_template(template: str) -> str:
    if template == "行业新闻":
        return """
{
  "title": "标题",
  "intro": "导语",
  "event_summary": "事件概述",
  "industry_background": "行业背景",
  "impact_analysis": "影响分析",
  "industry_insight": "行业启示"
}
""".strip()

    if template == "技术科普":
        return """
{
  "title": "标题",
  "intro": "导语",
  "section1": {
    "title": "模块1标题",
    "item1": {
      "subtitle": "小标题1",
      "body": "正文1",
      "image_hint": "图片建议1"
    },
    "item2": {
      "subtitle": "小标题2",
      "body": "正文2",
      "image_hint": "图片建议2"
    }
  },
  "section2": {
    "title": "模块2标题",
    "item1": {
      "subtitle": "小标题1",
      "body": "正文1",
      "image_hint": "图片建议1"
    },
    "item2": {
      "subtitle": "小标题2",
      "body": "正文2",
      "image_hint": "图片建议2"
    }
  },
  "section3": {
    "title": "模块3标题",
    "item1": {
      "subtitle": "小标题1",
      "body": "正文1",
      "image_hint": "图片建议1"
    }
  },
  "summary": "总结"
}
""".strip()

    if template == "政策解读":
        return """
{
  "title": "标题",
  "intro": "导语",
  "policy_background": "政策背景",
  "core_content": "政策核心内容",
  "industry_impact": "对行业的影响",
  "advice": "对企业或用户的建议",
  "summary": "总结"
}
""".strip()

    if template == "产品介绍":
        return """
{
  "title": "标题",
  "intro": "导语",
  "product_positioning": "产品背景或定位",
  "core_highlights": [
    "亮点1",
    "亮点2",
    "亮点3"
  ],
  "application_scenarios": "应用场景",
  "customer_value": "客户价值",
  "summary": "总结"
}
""".strip()

    if template == "案例分析":
        return """
{
  "title": "标题",
  "intro": "导语",
  "project_background": "项目背景",
  "pain_points": "项目难点或痛点",
  "solution": "解决方案",
  "result": "实施效果",
  "insight": "总结与启示"
}
""".strip()

    return """
{
  "title": "标题",
  "intro": "导语",
  "body": "正文",
  "summary": "总结"
}
""".strip()


def _build_original_prompt(form_data: dict) -> str:
    template = normalize_text(form_data.get("template", "行业新闻"))
    requirement = normalize_text(form_data.get("requirement", ""))
    content1 = normalize_text(form_data.get("content1", ""))
    content2 = normalize_text(form_data.get("content2", ""))
    content3 = normalize_text(form_data.get("content3", ""))

    materials = []
    if content1:
        materials.append(f"素材1：{content1}")
    if content2:
        materials.append(f"素材2：{content2}")
    if content3:
        materials.append(f"素材3：{content3}")

    materials_text = "\n".join(materials).strip()
    if not materials_text:
        materials_text = "暂无素材，请基于新能源、充电桩、重卡充电、电力市场、储能、能源政策等方向生成一篇适合微信公众号发布的文章。"

    common_requirement = requirement or "写成一篇约800字的专业公众号文章，结构清晰，语言专业但不生硬，适合公众号阅读。"

    schema = article_json_schema_for_template(template)

    template_requirements = {
        "行业新闻": """
【行业新闻写作要求】
1. 文章要体现“新闻性 + 行业分析性”
2. 先交代发生了什么，再解释为什么重要
3. 可适当补充行业背景和趋势判断
4. 结尾给出行业启示，提升文章价值
5. 适合公众号阅读，不要写成新闻通稿
""".strip(),

        "技术科普": """
【技术科普写作要求】
1. 文章应采用“导语 + 分模块 + 小标题 + 总结”的公众号常见结构
2. 特别适合指南类、科普类、使用提示类、安全提醒类内容
3. 每段正文尽量控制在80~150字
4. 小标题要清晰、简洁，适合公众号快速阅读
5. 图片建议只写图片类型或图片内容描述，不要写链接
6. 如果素材不足，可以基于行业常识做合理补充，但不要脱离新能源和充电场景
""".strip(),

        "政策解读": """
【政策解读写作要求】
1. 先讲政策背景，再讲政策内容，再讲影响和建议
2. 不要只复述文件，要体现解读价值
3. 要站在行业企业和用户视角分析影响
4. 结尾要给出清晰的判断或建议
5. 语言要平实，不要官话堆砌
""".strip(),

        "产品介绍": """
【产品介绍写作要求】
1. 突出产品定位、核心亮点、适用场景和客户价值
2. 不要写成生硬广告，要让读者理解产品解决了什么问题
3. 可以适当写产品优势，但不要空洞吹嘘
4. 结尾强调产品价值和应用前景
5. 适合做公众号对外宣传材料
""".strip(),

        "案例分析": """
【案例分析写作要求】
1. 文章要围绕“背景—问题—方案—效果—启示”展开
2. 要体现真实场景感和解决问题的逻辑
3. 要突出案例价值，不要只写流水账
4. 总结部分要提炼可复用经验或行业启示
5. 语言既专业又有现场感
""".strip(),
    }

    template_requirement = template_requirements.get(
        template,
        "请生成一篇适合微信公众号发布的专业文章。"
    )

    prompt = f"""
你是一名资深新能源行业公众号写作助手，请根据以下要求生成内容。

【文章类型】
{template}

【写作要求】
{common_requirement}

【素材】
{materials_text}

【通用内容要求】
1. 文章必须贴合新能源、充电桩、重卡充电、电力市场、储能、能源政策等行业语境
2. 内容要专业、准确、可读，不要写成学术论文
3. 语言要专业但不生硬，要让普通行业从业者也能读懂
4. 不要输出“作为AI”“以下是”之类的废话
5. 不要输出任何解释、说明、前言、结语
6. 不要输出 markdown 代码块，不要输出 ```json
7. 你必须只输出一个完整、合法的 JSON 对象

{template_requirement}

【最重要要求】
请严格按下面的 JSON 结构输出，字段名必须完全一致，所有字段都必须存在；如果素材不足，也要基于合理行业常识补全，不允许漏字段。

【JSON结构】
{schema}
""".strip()

    return prompt


def _load_rag_helpers():
    project_root = Path(__file__).resolve().parents[1]
    rag_scripts_dir = project_root / "rag_engine" / "scripts"
    if str(rag_scripts_dir) not in sys.path:
        sys.path.insert(0, str(rag_scripts_dir))

    from build_rag_context import _SimpleSession, format_context
    from search_rag import collect_ranked_rows, fetch_query_embedding, load_vectors

    return _SimpleSession, format_context, collect_ranked_rows, fetch_query_embedding, load_vectors


def build_enhanced_prompt(user_query: str, original_prompt_inputs: dict | str, config: dict) -> str:
    original_prompt = (
        original_prompt_inputs
        if isinstance(original_prompt_inputs, str)
        else _build_original_prompt(original_prompt_inputs)
    )

    rag_config = config.get("rag") if isinstance(config, dict) else {}
    if not isinstance(rag_config, dict) or not rag_config.get("enabled", False):
        print("[RAG] disabled")
        return original_prompt

    try:
        _SimpleSession, format_context, collect_ranked_rows, fetch_query_embedding, load_vectors = _load_rag_helpers()
        rows = load_vectors()
        if not rows:
            raise RuntimeError("向量文件为空")

        doubao_config = config.get("doubao") if isinstance(config, dict) else {}
        api_key = normalize_text(doubao_config.get("api_key", ""))
        base_url = normalize_text(doubao_config.get("base_url", "")).rstrip("/")
        top_k = int(rag_config.get("top_k", 3))
        if not api_key or not base_url:
            raise RuntimeError("doubao 配置缺失")

        endpoint = f"{base_url}/embeddings/multimodal"
        query_embedding = fetch_query_embedding(_SimpleSession(), endpoint, api_key, user_query)
        top_rows = collect_ranked_rows(user_query, query_embedding, rows)[:top_k]
        if not top_rows:
            raise RuntimeError("未检索到可用 RAG 上下文")

        rag_context = format_context(top_rows).strip()
        enhanced_prompt = f"""
{original_prompt}

【用户主题】
{user_query}

【企业知识库参考内容】
以下内容来自企业知识库检索结果，请优先吸收其核心观点与逻辑，但不要逐句照抄，也不要机械拼接：
{rag_context}

【增强输出要求】
1. 请在保留原有写稿任务要求的前提下，优先吸收上述企业知识库中的核心观点
2. 强调逻辑清晰、语言专业、适合公众号发布
3. 可以整合参考知识，但不要生硬照抄
4. RAG 内容仅作为补充知识上下文，不可脱离用户主题
""".strip()
        print("[RAG] enabled")
        print("[RAG] context built successfully")
        return enhanced_prompt
    except Exception as exc:
        print(f"[RAG] fallback to original prompt: {exc}")
        return original_prompt


def build_prompt(form_data: dict) -> str:
    original_prompt = _build_original_prompt(form_data)
    config = load_config()
    user_query = normalize_text(form_data.get("requirement", "")) or normalize_text(form_data.get("content1", "")) or "新能源行业公众号文章"
    return build_enhanced_prompt(user_query=user_query, original_prompt_inputs=original_prompt, config=config)
