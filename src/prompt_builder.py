# -*- coding: utf-8 -*-

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


def build_prompt(form_data: dict) -> str:
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
