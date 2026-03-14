# -*- coding: utf-8 -*-
import json
import re
import requests

from prompt_builder import build_prompt, normalize_text


def clean_model_json_text(text: str) -> str:
    if not text:
        return ""

    text = text.strip()

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

    def render_item(item: dict, section_key: str, item_key: str) -> str:
        if not isinstance(item, dict):
            return ""

        subtitle = normalize_text(item.get("subtitle"))
        body = normalize_text(item.get("body"))
        image_hint = normalize_text(item.get("image_hint"))

        parts = []

        if subtitle:
            parts.append(
                f'<div class="sub-title" contenteditable="true" data-section="{section_key}" data-item="{item_key}" data-field="subtitle">{subtitle}</div>'
            )

        if body:
            parts.append(
                f'<div class="paragraph" contenteditable="true" data-section="{section_key}" data-item="{item_key}" data-field="body">{body}</div>'
            )

        if image_hint:
            parts.append(
                f'<div class="image-hint" contenteditable="true" data-section="{section_key}" data-item="{item_key}" data-field="image_hint">配图建议：{image_hint}</div>'
            )

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
            block_parts.append(
                f'<div class="section-title" contenteditable="true" data-section="{sec_key}" data-field="section_title">{sec_title}</div>'
            )

        item1_html = render_item(item1, sec_key, "item1")
        if item1_html:
            block_parts.append(item1_html)

        item2_html = render_item(item2, sec_key, "item2")
        if item2_html:
            block_parts.append(item2_html)

        if block_parts:
            section_html_list.append(f'<div class="section-block" data-section="{sec_key}">{"".join(block_parts)}</div>')

    intro_html = (
        f'<div class="intro-box" contenteditable="true" data-field="intro">{intro}</div>'
        if intro else ""
    )
    summary_html = f'''
    <div class="summary-box">
        <div class="summary-title">总结</div>
        <div class="paragraph" contenteditable="true" data-field="summary">{summary}</div>
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
            .action-bar {{
                display: flex;
                justify-content: flex-end;
                margin-bottom: 16px;
            }}
            .copy-btn {{
                border: none;
                background: #2f7cf6;
                color: #fff;
                padding: 10px 16px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 14px;
                font-weight: bold;
            }}
            .copy-btn:hover {{
                background: #2563eb;
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
            <div class="action-bar">
                <button type="button" class="copy-btn" id="copyPublishBtn">复制发布稿</button>
            </div>

            <div class="article-title" contenteditable="true" data-field="title">{title}</div>
            {intro_html}
            {''.join(section_html_list)}
            {summary_html}           
        </div>
        <script>
            function getNodeText(selector, root) {{
                const node = (root || document).querySelector(selector);
                return node ? node.innerText.trim() : "";
            }}

            function buildPublishText() {{
                const lines = [];
           

                const page = document.querySelector(".page");
                if (!page) {
                    console.log("[copy-publish] page node not found");
                    return "";
                }

                const currentTitle = getNodeText('[data-field="title"]', page);
                if (currentTitle) {
                    lines.push("标题：" + currentTitle);
                    lines.push("");
                }

                const currentIntro = getNodeText('[data-field="intro"]', page); 
                if (currentIntro) {{
                    lines.push("【导语】");
                    lines.push(currentIntro);
                    lines.push("");
                }}

                const sectionOrder = ["section1", "section2", "section3"];
                sectionOrder.forEach(function (sectionKey, sectionIdx) {{
                    const section = page.querySelector('.section-block[data-section="' + sectionKey + '"]');
                    if (!section) {{
                        return;
                    }}

                    const sectionTitle = getNodeText('[data-field="section_title"]', section);
                    if (sectionTitle) {{
                        lines.push("【模块" + (sectionIdx + 1) + "】" + sectionTitle);
                        lines.push("");
                    }}

                    const itemOrder = ["item1", "item2"];
                    let itemCounter = 1;
                    itemOrder.forEach(function (itemKey) {{
                        const subtitle = getNodeText('[data-item="' + itemKey + '"][data-field="subtitle"]', section);
                        const body = getNodeText('[data-item="' + itemKey + '"][data-field="body"]', section);
                        const imageHintRaw = getNodeText('[data-item="' + itemKey + '"][data-field="image_hint"]', section);
                        const imageHint = imageHintRaw.replace(/^配图建议：?\s*/, "").trim();

                        if (!subtitle && !body && !imageHint) {{
                            return;
                        }}

                        if (subtitle) {{
                            lines.push(itemCounter + ". " + subtitle);
                        }}
                        if (body) {{
                            lines.push(body);
                        }}
                        if (imageHint) {{
                            lines.push("【配图建议】" + imageHint);
                        }}
                        lines.push("");
                        itemCounter += 1;
                    }});
                }});

                const currentSummary = getNodeText('[data-field="summary"]', page);
                if (currentSummary) {{
                    lines.push("【总结】");
                    lines.push(currentSummary);
                }}

                const publishText = lines.join("\n").trim();
                console.log("[copy-publish] publish text length:", publishText.length);
                return publishText;
            }

            function fallbackCopyText(text) {
                const textarea = document.createElement("textarea");
                textarea.value = text;
                textarea.setAttribute("readonly", "readonly");
                textarea.style.position = "fixed";
                textarea.style.left = "-9999px";
                document.body.appendChild(textarea);
                textarea.focus();
                textarea.select();

                let copied = false;
                try {
                    copied = document.execCommand("copy");
                } catch (err) {
                    copied = false;
                }

                document.body.removeChild(textarea);
                return copied;
            }

            async function copyPublishText() {
                console.log("[copy-publish] copy button clicked");
                const text = buildPublishText();
                if (!text) {
                    alert("页面暂不可复制内容");
                    return;
                }

                try {
                    if (navigator.clipboard && navigator.clipboard.writeText) {
                        await navigator.clipboard.writeText(text);
                    } else {
                        const copied = fallbackCopyText(text);
                        if (!copied) {
                            throw new Error("fallback copy failed");
                        }
                    }
                    alert("已复制到剪贴板");
                } catch (err) {
                    console.log("[copy-publish] navigator copy failed, try fallback:", err);
                    const copied = fallbackCopyText(text);
                    if (copied) {
                        alert("已复制到剪贴板");
                        return;
                    }
                    alert("复制失败，请手动复制");
                }
            }

            document.getElementById("copyPublishBtn").addEventListener("click", copyPublishText);
        </script>
    </body>
    </html>
    """
    return html


def render_article_html_by_template(template: str, article_json: dict) -> str:
    if template == "技术科普":
        return render_tech_pop_html(article_json)

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
        title = f"[AI写稿]{template}"

    if not body:
        body = content.strip()

    return title, body


def call_doubao_generate(form_data: dict, ark_api_key: str, ark_base_url: str, ark_model: str) -> dict:
    prompt = build_prompt(form_data)
    url = f"{ark_base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {ark_api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": ark_model,
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

    resp = requests.post(url, headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()

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
    except Exception:
        title, body = split_title_and_body(content, form_data)
        return {
            "raw_content": content,
            "title": title,
            "body": body
        }
