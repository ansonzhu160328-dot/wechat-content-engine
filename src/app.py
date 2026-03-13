
# -*- coding: utf-8 -*-
import os
import json
import re
import threading
import traceback
from datetime import datetime
import yaml

import requests
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)
ARTICLE_HTML_CACHE = {}
def load_config():
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "config",
        "config.yaml"
    )

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

config = load_config()
DOUBAO_API_KEY = config["doubao"]["api_key"]
DOUBAO_BASE_URL = config["doubao"]["base_url"]
DOUBAO_MODEL = config["doubao"]["model"]
# =========================
# 配置区
# =========================

# 建议优先用环境变量；如果你暂时不会配，就把默认值改成你自己的现有值

ARK_API_KEY = os.getenv("ARK_API_KEY", "51271bc4-601f-4f80-93ba-3725a971b0c1")
ARK_BASE_URL = os.getenv("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
ARK_MODEL = os.getenv("ARK_MODEL", "doubao-1-5-pro-32k-250115")

FEISHU_APP_ID = os.getenv("FEISHU_APP_ID", "cli_a922531157ba9bcb")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET", "xmubydlGmOkSg2J0XjJybbNf0fHXrNrS")

BITABLE_APP_TOKEN = os.getenv("BITABLE_APP_TOKEN", "UHI4b4izma1E5SsYGP9cQ9KHnXz")
BITABLE_TABLE_ID = os.getenv("BITABLE_TABLE_ID", "tblFUuB0ICxpylvM")

HOST = "0.0.0.0"
PORT = 7001


# =========================
# 工具函数
# =========================

def log(*args):
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), *args, flush=True)


def get_feishu_tenant_access_token() -> str:
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    payload = {
        "app_id": FEISHU_APP_ID,
        "app_secret": FEISHU_APP_SECRET
    }
    resp = requests.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise Exception(f"获取 tenant_access_token 失败: {data}")
    return data["tenant_access_token"]


def normalize_text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def clean_model_json_text(text: str) -> str:
    """
    清理模型可能返回的 ```json ... ``` 包裹
    """
    if not text:
        return ""

    text = text.strip()

    # 去掉 markdown code fence
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text.strip(), flags=re.IGNORECASE).strip()
        text = re.sub(r"```$", "", text.strip()).strip()

    return text.strip()


def parse_model_json(content: str) -> dict:
    cleaned = clean_model_json_text(content)
    try:
        return json.loads(cleaned)
    except Exception as e:
        raise Exception(f"模型输出不是合法JSON：{e}；原始输出：{content}")


def article_json_schema_for_template(template: str) -> str:
    """
    给不同模板返回严格 JSON schema 示例
    """
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

def format_industry_news(article_json: dict) -> tuple[str, str]:
    title = normalize_text(article_json.get("title")) or "行业新闻"
    intro = normalize_text(article_json.get("intro"))
    event_summary = normalize_text(article_json.get("event_summary"))
    industry_background = normalize_text(article_json.get("industry_background"))
    impact_analysis = normalize_text(article_json.get("impact_analysis"))
    industry_insight = normalize_text(article_json.get("industry_insight"))

    lines = []

    if intro:
        lines.append("【导语】")
        lines.append(intro)
        lines.append("")

    if event_summary:
        lines.append("【事件概述】")
        lines.append(event_summary)
        lines.append("")

    if industry_background:
        lines.append("【行业背景】")
        lines.append(industry_background)
        lines.append("")

    if impact_analysis:
        lines.append("【影响分析】")
        lines.append(impact_analysis)
        lines.append("")

    if industry_insight:
        lines.append("【行业启示】")
        lines.append(industry_insight)

    body = "\n".join(lines).strip()
    return title, body


def format_tech_pop(article_json: dict) -> tuple[str, str]:
    title = normalize_text(article_json.get("title")) or "技术科普"
    intro = normalize_text(article_json.get("intro"))
    summary = normalize_text(article_json.get("summary"))

    lines = []

    if intro:
        lines.append("【导语】")
        lines.append(intro)
        lines.append("")

    section_labels = {
        "section1": "【模块1】",
        "section2": "【模块2】",
        "section3": "【模块3】"
    }

    for sec_key in ["section1", "section2", "section3"]:
        sec = article_json.get(sec_key, {})
        if not isinstance(sec, dict):
            continue

        sec_title = normalize_text(sec.get("title"))
        if sec_title:
            lines.append(f"{section_labels.get(sec_key, '【模块】')}{sec_title}")
            lines.append("")

        item_index = 1
        for item_key in ["item1", "item2"]:
            item = sec.get(item_key, {})
            if not isinstance(item, dict):
                continue

            subtitle = normalize_text(item.get("subtitle"))
            body = normalize_text(item.get("body"))
            image_hint = normalize_text(item.get("image_hint"))

            if subtitle:
                lines.append(f"{item_index}. {subtitle}")
            if body:
                lines.append(body)
            if image_hint:
                lines.append(f"【配图建议】{image_hint}")
            if subtitle or body or image_hint:
                lines.append("")
                item_index += 1

    if summary:
        lines.append("【总结】")
        lines.append(summary)

    body = "\n".join(lines).strip()
    return title, body


def format_policy_interpretation(article_json: dict) -> tuple[str, str]:
    title = normalize_text(article_json.get("title")) or "政策解读"
    intro = normalize_text(article_json.get("intro"))
    policy_background = normalize_text(article_json.get("policy_background"))
    core_content = normalize_text(article_json.get("core_content"))
    industry_impact = normalize_text(article_json.get("industry_impact"))
    advice = normalize_text(article_json.get("advice"))
    summary = normalize_text(article_json.get("summary"))

    lines = []

    if intro:
        lines.append("【导语】")
        lines.append(intro)
        lines.append("")

    if policy_background:
        lines.append("【政策背景】")
        lines.append(policy_background)
        lines.append("")

    if core_content:
        lines.append("【政策核心内容】")
        lines.append(core_content)
        lines.append("")

    if industry_impact:
        lines.append("【对行业的影响】")
        lines.append(industry_impact)
        lines.append("")

    if advice:
        lines.append("【对企业/用户的建议】")
        lines.append(advice)
        lines.append("")

    if summary:
        lines.append("【总结】")
        lines.append(summary)

    body = "\n".join(lines).strip()
    return title, body


def format_product_intro(article_json: dict) -> tuple[str, str]:
    title = normalize_text(article_json.get("title")) or "产品介绍"
    intro = normalize_text(article_json.get("intro"))
    product_positioning = normalize_text(article_json.get("product_positioning"))
    highlights = article_json.get("core_highlights", [])
    application_scenarios = normalize_text(article_json.get("application_scenarios"))
    customer_value = normalize_text(article_json.get("customer_value"))
    summary = normalize_text(article_json.get("summary"))

    if not isinstance(highlights, list):
        highlights = [normalize_text(highlights)]

    lines = []

    if intro:
        lines.append("【导语】")
        lines.append(intro)
        lines.append("")

    if product_positioning:
        lines.append("【产品背景/定位】")
        lines.append(product_positioning)
        lines.append("")

    lines.append("【核心亮点】")
    has_highlight = False
    for idx, item in enumerate(highlights, start=1):
        item_text = normalize_text(item)
        if item_text:
            lines.append(f"{idx}. {item_text}")
            has_highlight = True
    if has_highlight:
        lines.append("")

    if application_scenarios:
        lines.append("【应用场景】")
        lines.append(application_scenarios)
        lines.append("")

    if customer_value:
        lines.append("【客户价值】")
        lines.append(customer_value)
        lines.append("")

    if summary:
        lines.append("【总结】")
        lines.append(summary)

    body = "\n".join(lines).strip()
    return title, body


def format_case_analysis(article_json: dict) -> tuple[str, str]:
    title = normalize_text(article_json.get("title")) or "案例分析"
    intro = normalize_text(article_json.get("intro"))
    project_background = normalize_text(article_json.get("project_background"))
    pain_points = normalize_text(article_json.get("pain_points"))
    solution = normalize_text(article_json.get("solution"))
    result = normalize_text(article_json.get("result"))
    insight = normalize_text(article_json.get("insight"))

    lines = []

    if intro:
        lines.append("【导语】")
        lines.append(intro)
        lines.append("")

    if project_background:
        lines.append("【项目背景】")
        lines.append(project_background)
        lines.append("")

    if pain_points:
        lines.append("【项目难点/痛点】")
        lines.append(pain_points)
        lines.append("")

    if solution:
        lines.append("【解决方案】")
        lines.append(solution)
        lines.append("")

    if result:
        lines.append("【实施效果】")
        lines.append(result)
        lines.append("")

    if insight:
        lines.append("【总结与启示】")
        lines.append(insight)

    body = "\n".join(lines).strip()
    return title, body


def format_default(article_json: dict) -> tuple[str, str]:
    title = normalize_text(article_json.get("title")) or "AI写稿"
    intro = normalize_text(article_json.get("intro"))
    body_text = normalize_text(article_json.get("body"))
    summary = normalize_text(article_json.get("summary"))

    lines = []

    if intro:
        lines.append("【导语】")
        lines.append(intro)
        lines.append("")

    if body_text:
        lines.append("【正文】")
        lines.append(body_text)
        lines.append("")

    if summary:
        lines.append("【总结】")
        lines.append(summary)

    body = "\n".join(lines).strip()
    return title, body

def render_tech_pop_html(article_json: dict) -> str:
    title = normalize_text(article_json.get("title")) or "技术科普"
    intro = normalize_text(article_json.get("intro"))
    summary = normalize_text(article_json.get("summary"))

    def render_item(item: dict) -> str:
        if not isinstance(item, dict):
            return ""

        subtitle = normalize_text(item.get("subtitle"))
        body = normalize_text(item.get("body"))
        image_hint = normalize_text(item.get("image_hint"))

        parts = []

        if subtitle:
            parts.append(f'<div class="sub-title">{subtitle}</div>')

        if body:
            parts.append(f'<div class="paragraph">{body}</div>')

        if image_hint:
            parts.append(f'<div class="image-hint">配图建议：{image_hint}</div>')

        return "\n".join(parts)

    section_html_list = []

    for sec_key in ["section1", "section2", "section3"]:
        sec = article_json.get(sec_key, {})
        if not isinstance(sec, dict):
            continue

        sec_title = normalize_text(sec.get("title"))
        item1 = sec.get("item1", {})
        item2 = sec.get("item2", {})

        block_parts = []

        if sec_title:
            block_parts.append(f'<div class="section-title">{sec_title}</div>')

        item1_html = render_item(item1)
        if item1_html:
            block_parts.append(item1_html)

        item2_html = render_item(item2)
        if item2_html:
            block_parts.append(item2_html)

        if block_parts:
            section_html_list.append(f'<div class="section-block">{"".join(block_parts)}</div>')

    intro_html = f'<div class="intro-box">{intro}</div>' if intro else ""
    summary_html = f'''
    <div class="summary-box">
        <div class="summary-title">总结</div>
        <div class="paragraph">{summary}</div>
    </div>
    ''' if summary else ""

    html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <title>{title}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                margin: 0;
                padding: 0;
                background: #f5f6f8;
                font-family: "Microsoft YaHei", Arial, sans-serif;
                color: #222;
            }}
            .page {{
                max-width: 860px;
                margin: 30px auto;
                background: #fff;
                padding: 36px 32px 48px;
                box-shadow: 0 6px 20px rgba(0,0,0,0.08);
                border-radius: 12px;
            }}
            .article-title {{
                font-size: 30px;
                font-weight: bold;
                line-height: 1.4;
                margin-bottom: 24px;
                color: #111;
                text-align: center;
            }}
            .intro-box {{
                background: #f7fbff;
                border-left: 5px solid #2f7cf6;
                padding: 18px 18px;
                line-height: 1.9;
                font-size: 16px;
                margin-bottom: 28px;
                color: #333;
            }}
            .section-block {{
                margin-bottom: 30px;
            }}
            .section-title {{
                font-size: 22px;
                font-weight: bold;
                color: #fff;
                background: linear-gradient(90deg, #ff9f2f, #ff7f2a);
                display: inline-block;
                padding: 8px 16px;
                border-radius: 6px;
                margin-bottom: 16px;
            }}
            .sub-title {{
                font-size: 18px;
                font-weight: bold;
                color: #1f4fa3;
                margin: 18px 0 10px;
                line-height: 1.6;
            }}
            .paragraph {{
                font-size: 16px;
                line-height: 1.95;
                color: #333;
                margin-bottom: 10px;
                white-space: pre-wrap;
            }}
            .image-hint {{
                margin: 12px 0 18px;
                padding: 10px 14px;
                background: #fff7e8;
                border: 1px dashed #f0b24a;
                color: #9a6410;
                border-radius: 8px;
                font-size: 14px;
                line-height: 1.7;
            }}
            .summary-box {{
                margin-top: 34px;
                padding: 18px;
                background: #f9fafb;
                border: 1px solid #e5e7eb;
                border-radius: 10px;
            }}
            .summary-title {{
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 12px;
                color: #111827;
            }}
        </style>
    </head>
    <body>
        <div class="page">
            <div class="article-title">{title}</div>
            {intro_html}
            {''.join(section_html_list)}
            {summary_html}
        </div>
    </body>
    </html>
    """
    return html

def render_article_html_by_template(template: str, article_json: dict) -> str:
    if template == "技术科普":
        return render_tech_pop_html(article_json)

    # 其他模板暂时先用简单预览
    title, body = format_article_by_template(template, article_json)
    simple_html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <title>{title}</title>
        <style>
            body {{
                font-family: "Microsoft YaHei", Arial, sans-serif;
                background: #f5f6f8;
                margin: 0;
                padding: 30px;
            }}
            .page {{
                max-width: 860px;
                margin: 0 auto;
                background: white;
                padding: 36px;
                border-radius: 12px;
                box-shadow: 0 6px 20px rgba(0,0,0,0.08);
            }}
            .title {{
                font-size: 30px;
                font-weight: bold;
                margin-bottom: 24px;
                text-align: center;
            }}
            .body {{
                white-space: pre-wrap;
                line-height: 1.95;
                font-size: 16px;
                color: #333;
            }}
        </style>
    </head>
    <body>
        <div class="page">
            <div class="title">{title}</div>
            <div class="body">{body}</div>
        </div>
    </body>
    </html>
    """
    return simple_html

def format_article_by_template(template: str, article_json: dict) -> tuple[str, str]:
    if template == "行业新闻":
        return format_industry_news(article_json)
    if template == "技术科普":
        return format_tech_pop(article_json)
    if template == "政策解读":
        return format_policy_interpretation(article_json)
    if template == "产品介绍":
        return format_product_intro(article_json)
    if template == "案例分析":
        return format_case_analysis(article_json)
    return format_default(article_json)


def split_title_and_body(content: str, form_data: dict) -> tuple[str, str]:
    """
    兜底：如果模型没有按 JSON 返回，仍尝试按旧逻辑解析
    """
    lines = content.splitlines()
    title = ""
    body = content.strip()

    for i, line in enumerate(lines):
        if line.strip().startswith("标题"):
            parts = line.split("：", 1)
            if len(parts) == 2 and parts[1].strip():
                title = parts[1].strip()

            rest = lines[i + 1:]
            body = "\n".join(rest).strip()
            break

    if not title:
        template = normalize_text(form_data.get("template", "行业新闻"))
        now_tag = datetime.now().strftime("%m%d_%H%M")
        title = f"[AI写稿]{template}_{now_tag}"

    if not body:
        body = content.strip()

    return title, body


def call_doubao_generate(form_data: dict) -> dict:
    prompt = build_prompt(form_data)
    url = f"{DOUBAO_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {DOUBAO_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": DOUBAO_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "你是一名新能源行业公众号写作助手，擅长行业新闻、技术科普、政策解读、产品介绍、案例分析等内容写作。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.4,
        "max_tokens": 3000
    }

    log("开始调用豆包...")
    resp = requests.post(url, headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    log("豆包返回成功")

    content = (
        data.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
        .strip()
    )

    if not content:
        raise Exception(f"豆包返回为空：{data}")

    template = normalize_text(form_data.get("template", "行业新闻"))

    try:
        article_json = parse_model_json(content)
        title, body = format_article_by_template(template, article_json)
        html = render_article_html_by_template(template, article_json)
        return {
            "raw_content": content,
            "title": title,
            "body": body,
            "html": html
        }
    except Exception as json_err:
        # 兜底：如果 JSON 失败，仍尝试旧版文本解析，避免整条链路完全中断
        log("JSON解析失败，启用兜底文本解析：", repr(json_err))
        title, body = split_title_and_body(content, form_data)
        return {
            "raw_content": content,
            "title": title,
            "body": body
        }


def write_to_bitable(form_data: dict, article_data: dict) -> dict:
    token = get_feishu_tenant_access_token()

    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{BITABLE_APP_TOKEN}/tables/{BITABLE_TABLE_ID}/records"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    editor_notes = []
    if form_data.get("template"):
        editor_notes.append(f"模板：{form_data['template']}")
    if form_data.get("requirement"):
        editor_notes.append(f"要求：{form_data['requirement']}")
    if form_data.get("content1"):
        editor_notes.append(f"素材1：{form_data['content1']}")
    if form_data.get("content2"):
        editor_notes.append(f"素材2：{form_data['content2']}")
    if form_data.get("content3"):
        editor_notes.append(f"素材3：{form_data['content3']}")

    fields = {
        "news_title_raw": article_data["title"],
        "article_body": article_data["body"],
        "editor_notes": "\n".join(editor_notes),
    }

    payload = {"fields": fields}

    log("开始写入飞书多维表格...")
    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise Exception(f"写入多维表格失败: {data}")

    log("飞书多维表格写入成功")
    return data


def background_generate_job(form_data: dict):
    try:
        log("后台任务启动，form_data =", json.dumps(form_data, ensure_ascii=False))
        article_data = call_doubao_generate(form_data)
        log("文章生成成功，标题 =", article_data["title"])

        write_result = write_to_bitable(form_data, article_data)
        log("写表成功：", json.dumps(write_result, ensure_ascii=False))

        record_id = (
            write_result.get("data", {})
            .get("record", {})
            .get("record_id", "")
        )

        if record_id and article_data.get("html"):
            ARTICLE_HTML_CACHE[record_id] = article_data["html"]
            log(f"HTML预览已缓存，record_id = {record_id}")
            log(f"预览地址：http://127.0.0.1:{PORT}/article/{record_id}")

    except Exception as e:
        log("后台任务失败：", repr(e))
        traceback.print_exc()


# =========================
# 页面 HTML
# =========================

PAGE_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>AI写稿助手</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { box-sizing: border-box; }
        body {
            margin: 0;
            padding: 0;
            font-family: "Microsoft YaHei", Arial, sans-serif;
            background: #f5f7fb;
            color: #1f2329;
        }
        .container {
            max-width: 900px;
            margin: 40px auto;
            background: #ffffff;
            border-radius: 18px;
            box-shadow: 0 8px 24px rgba(15, 32, 56, 0.08);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #1f5eff, #1746c8);
            color: white;
            padding: 28px 32px 24px;
        }
        .header h1 {
            margin: 0 0 10px;
            font-size: 30px;
        }
        .header p {
            margin: 0;
            font-size: 15px;
            opacity: 0.95;
        }
        .content {
            padding: 28px 32px 36px;
        }
        .section-title {
            font-size: 20px;
            font-weight: bold;
            margin: 0 0 20px;
        }
        .form-group {
            margin-bottom: 22px;
        }
        label {
            display: block;
            font-weight: bold;
            margin-bottom: 8px;
            font-size: 15px;
        }
        input[type="text"], select, textarea {
            width: 100%;
            padding: 14px 16px;
            border: 1px solid #d0d7e2;
            border-radius: 12px;
            font-size: 15px;
            outline: none;
            transition: all 0.2s ease;
            background: #fff;
        }
        input[type="text"]:focus, select:focus, textarea:focus {
            border-color: #1f5eff;
            box-shadow: 0 0 0 3px rgba(31, 94, 255, 0.10);
        }
        textarea {
            min-height: 120px;
            resize: vertical;
            line-height: 1.6;
        }
        .hint {
            color: #6b7785;
            font-size: 13px;
            margin-top: 6px;
        }
        .actions {
            display: flex;
            gap: 12px;
            margin-top: 30px;
        }
        button, .btn-secondary {
            border: none;
            border-radius: 12px;
            padding: 14px 22px;
            font-size: 15px;
            font-weight: bold;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
        }
        button {
            background: #1f5eff;
            color: white;
        }
        button:hover {
            background: #184fd9;
        }
        .btn-secondary {
            background: #edf2ff;
            color: #1f5eff;
        }
        .success-box {
            margin-top: 24px;
            padding: 18px 20px;
            background: #ecfdf3;
            border: 1px solid #b7ebc6;
            border-radius: 14px;
            color: #146c43;
        }
        .footer-note {
            margin-top: 24px;
            color: #6b7785;
            font-size: 13px;
            line-height: 1.7;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>AI写稿助手</h1>
            <p>上传素材或粘贴需求，快速生成公众号草稿，适用于新能源、充电桩、重卡充电、电力市场等内容场景。</p>
        </div>

        <div class="content">
            <div class="section-title">填写写稿需求</div>

            <form method="post" action="/submit_generate">
                <div class="form-group">
                    <label for="template">文章模板</label>
                    <select name="template" id="template">
                        <option value="行业新闻">行业新闻</option>
                        <option value="技术科普">技术科普</option>
                        <option value="政策解读">政策解读</option>
                        <option value="产品介绍">产品介绍</option>
                        <option value="案例分析">案例分析</option>
                    </select>
                    <div class="hint">当前按五类模板分别生成，后续可继续扩展。</div>
                </div>

                <div class="form-group">
                    <label for="requirement">写作要求</label>
                    <textarea name="requirement" id="requirement" placeholder="例如：控制在800字左右，语气专业但不生硬，适合公众号阅读，结尾给出行业启示。"></textarea>
                </div>

                <div class="form-group">
                    <label for="content1">素材正文（第一部分）</label>
                    <textarea name="content1" id="content1" placeholder="请粘贴主要素材，例如行业新闻、政策内容、项目背景等。"></textarea>
                </div>

                <div class="form-group">
                    <label for="content2">素材正文（第二部分）</label>
                    <textarea name="content2" id="content2" placeholder="请粘贴补充素材，例如专家观点、市场数据、补充背景等。"></textarea>
                </div>

                <div class="form-group">
                    <label for="content3">素材正文（第三部分）</label>
                    <textarea name="content3" id="content3" placeholder="请粘贴补充要求，例如希望强调的观点、结尾方向、行业启示等。"></textarea>
                </div>

                <div class="actions">
                    <button type="submit">生成文章</button>
                    <a class="btn-secondary" href="/">重置</a>
                </div>
            </form>

            {% if success %}
            <div class="success-box">
                <strong>已提交成功。</strong><br>
                系统正在后台生成文章，并写入飞书草稿库。请稍后到草稿库中查看结果。
            </div>
            {% endif %}

            <div class="footer-note">
                提示：当前版本已切到“五类模板 + JSON结构化输出”模式。后续再往公众号 HTML 排版方向升级。
            </div>
        </div>
    </div>
</body>
</html>
"""


# =========================
# 路由
# =========================

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "ok": True,
        "message": "ai_writer_server is running"
    })


@app.route("/", methods=["GET"])
def index():
    return render_template_string(PAGE_HTML, success=False)


@app.route("/submit_generate", methods=["POST"])
def submit_generate():
    try:
        form_data = {
            "template": normalize_text(request.form.get("template", "行业新闻")),
            "requirement": normalize_text(request.form.get("requirement", "")),
            "content1": normalize_text(request.form.get("content1", "")),
            "content2": normalize_text(request.form.get("content2", "")),
            "content3": normalize_text(request.form.get("content3", "")),
        }

        log("收到网页表单提交：", json.dumps(form_data, ensure_ascii=False))

        t = threading.Thread(
            target=background_generate_job,
            args=(form_data,),
            daemon=True
        )
        t.start()

        return render_template_string(PAGE_HTML, success=True)

    except Exception as e:
        log("submit_generate 异常：", repr(e))
        traceback.print_exc()
        return f"提交失败：{str(e)}", 500

@app.route("/article/<record_id>", methods=["GET"])
def article_preview(record_id):
    html = ARTICLE_HTML_CACHE.get(record_id)
    if not html:
        return "未找到文章预览内容，请先生成文章，或服务已重启导致缓存丢失。", 404
    return html

@app.route("/feishu_callback", methods=["POST"])
def feishu_callback():
    payload = request.get_json(force=True, silent=True) or {}
    log("收到 /feishu_callback 请求：", json.dumps(payload, ensure_ascii=False))
    return jsonify({
        "toast": {
            "type": "success",
            "content": "已收到请求。当前主线建议使用 open_url 网页入口。"
        }
    })


if __name__ == "__main__":
    log(f"启动 Flask 服务：http://{HOST}:{PORT}")
    app.run(host=HOST, port=PORT, debug=False)
