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



def _normalize_section_labels(article_json: dict, defaults: dict) -> dict:
    labels = dict(defaults)
    raw_labels = article_json.get("section_labels", {})
    if isinstance(raw_labels, dict):
        for key, default_val in defaults.items():
            labels[key] = normalize_text(raw_labels.get(key, default_val)) or default_val
    return labels

def format_industry_news(article_json: dict) -> tuple[str, str]:
    title = normalize_text(article_json.get("title")) or "行业新闻"
    intro = normalize_text(article_json.get("intro"))
    event_summary = normalize_text(article_json.get("event_summary"))
    industry_background = normalize_text(article_json.get("industry_background"))
    impact_analysis = normalize_text(article_json.get("impact_analysis"))
    industry_insight = normalize_text(article_json.get("industry_insight"))

    labels = _normalize_section_labels(article_json, {
        "intro": "【导语】",
        "event_summary": "【事件概述】",
        "industry_background": "【行业背景】",
        "impact_analysis": "【影响分析】",
        "industry_insight": "【行业启示】",
    })

    lines = []

    if intro:
        lines.append(labels["intro"])
        lines.append(intro)
        lines.append("")

    if event_summary:
        lines.append(labels["event_summary"])
        lines.append(event_summary)
        lines.append("")

    if industry_background:
        lines.append(labels["industry_background"])
        lines.append(industry_background)
        lines.append("")

    if impact_analysis:
        lines.append(labels["impact_analysis"])
        lines.append(impact_analysis)
        lines.append("")

    if industry_insight:
        lines.append(labels["industry_insight"])
        lines.append(industry_insight)

    body = "\n".join(lines).strip()
    return title, body

def format_tech_pop(article_json: dict) -> tuple[str, str]:
    title = normalize_text(article_json.get("title")) or "技术科普"
    intro = normalize_text(article_json.get("intro"))
    summary = normalize_text(article_json.get("summary"))

    labels = _normalize_section_labels(article_json, {
        "intro": "【导语】",
        "section1": "【模块1】",
        "section2": "【模块2】",
        "section3": "【模块3】",
        "summary": "【总结】",
    })

    lines = []

    if intro:
        lines.append(labels["intro"])
        lines.append(intro)
        lines.append("")

    section_labels = {
        "section1": labels["section1"],
        "section2": labels["section2"],
        "section3": labels["section3"],
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
        lines.append(labels["summary"])
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

    labels = _normalize_section_labels(article_json, {
        "intro": "【导语】",
        "policy_background": "【政策背景】",
        "core_content": "【政策核心内容】",
        "industry_impact": "【对行业的影响】",
        "advice": "【对企业/用户的建议】",
        "summary": "【总结】",
    })

    lines = []

    if intro:
        lines.append(labels["intro"])
        lines.append(intro)
        lines.append("")

    if policy_background:
        lines.append(labels["policy_background"])
        lines.append(policy_background)
        lines.append("")

    if core_content:
        lines.append(labels["core_content"])
        lines.append(core_content)
        lines.append("")

    if industry_impact:
        lines.append(labels["industry_impact"])
        lines.append(industry_impact)
        lines.append("")

    if advice:
        lines.append(labels["advice"])
        lines.append(advice)
        lines.append("")

    if summary:
        lines.append(labels["summary"])
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

    labels = _normalize_section_labels(article_json, {
        "intro": "【导语】",
        "product_positioning": "【产品背景/定位】",
        "core_highlights": "【核心亮点】",
        "application_scenarios": "【应用场景】",
        "customer_value": "【客户价值】",
        "summary": "【总结】",
    })

    if not isinstance(highlights, list):
        highlights = [normalize_text(highlights)]

    lines = []

    if intro:
        lines.append(labels["intro"])
        lines.append(intro)
        lines.append("")

    if product_positioning:
        lines.append(labels["product_positioning"])
        lines.append(product_positioning)
        lines.append("")

    lines.append(labels["core_highlights"])
    has_highlight = False
    for idx, item in enumerate(highlights, start=1):
        item_text = normalize_text(item)
        if item_text:
            lines.append(f"{idx}. {item_text}")
            has_highlight = True
    if has_highlight:
        lines.append("")

    if application_scenarios:
        lines.append(labels["application_scenarios"])
        lines.append(application_scenarios)
        lines.append("")

    if customer_value:
        lines.append(labels["customer_value"])
        lines.append(customer_value)
        lines.append("")

    if summary:
        lines.append(labels["summary"])
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

    labels = _normalize_section_labels(article_json, {
        "intro": "【导语】",
        "project_background": "【项目背景】",
        "pain_points": "【项目难点/痛点】",
        "solution": "【解决方案】",
        "result": "【实施效果】",
        "insight": "【总结与启示】",
    })

    lines = []

    if intro:
        lines.append(labels["intro"])
        lines.append(intro)
        lines.append("")

    if project_background:
        lines.append(labels["project_background"])
        lines.append(project_background)
        lines.append("")

    if pain_points:
        lines.append(labels["pain_points"])
        lines.append(pain_points)
        lines.append("")

    if solution:
        lines.append(labels["solution"])
        lines.append(solution)
        lines.append("")

    if result:
        lines.append(labels["result"])
        lines.append(result)
        lines.append("")

    if insight:
        lines.append(labels["insight"])
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


def render_tech_pop_html(article_json: dict, record_id: str = "") -> str:
    title = normalize_text(article_json.get("title")) or "技术科普"
    intro = normalize_text(article_json.get("intro"))
    summary = normalize_text(article_json.get("summary"))
    labels = _normalize_section_labels(article_json, {
        "intro": "【导语】",
        "section1": "【模块1】",
        "section2": "【模块2】",
        "section3": "【模块3】",
        "summary": "【总结】",
    })

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
        f'<div class="intro-title" contenteditable="true" data-label="intro">{labels["intro"]}</div>'
        f'<div class="intro-box" contenteditable="true" data-field="intro">{intro}</div>'
        if intro else ""
    )
    summary_html = f'''
    <div class="summary-box">
        <div class="summary-title" contenteditable="true" data-label="summary">{labels["summary"]}</div>
        <div class="paragraph" contenteditable="true" data-field="summary">{summary}</div>
    </div>
    ''' if summary else ""

    section_html = "".join(section_html_list)

    html = """
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
            .save-btn {{
                border: none;
                background: #16a34a;
                color: #fff;
                padding: 10px 16px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 14px;
                font-weight: bold;
                margin-left: 10px;
            }}
            .save-btn:hover {{
                background: #15803d;
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
            .intro-title {{
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 8px;
                color: #111827;
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
                <button type="button" class="save-btn" id="saveArticleBtn">保存修改</button>
            </div>
            <div class="article-title" contenteditable="true" data-field="title">{title}</div>
            {intro_html}
            {section_html}
            {summary_html}
        </div>
        <script>
            const labels = {labels};

            function getNodeText(selector, root) {{
                const node = (root || document).querySelector(selector);
                return node ? node.innerText.trim() : "";
            }}

            function buildPublishText() {{
                const lines = [];
                const page = document.querySelector(".page");

                if (!page) {{
                    console.log("[copy-publish] page node not found");
                    return "";
                }}

                const currentTitle = getNodeText('[data-field="title"]', page);
                if (currentTitle) {{
                    lines.push("标题：" + currentTitle);
                    lines.push("");
                }}

                const introTitle = getNodeText('[data-label="intro"]', page);
                const currentIntro = getNodeText('[data-field="intro"]', page);
                if (currentIntro) {{
                    lines.push(introTitle || "【导语】");
                    lines.push(currentIntro);
                    lines.push("");
                }}

                const sectionOrder = ["section1", "section2", "section3"];
                sectionOrder.forEach(function (sectionKey) {{
                    const section = page.querySelector('.section-block[data-section="' + sectionKey + '"]');
                    if (!section) {{
                        return;
                    }}

                    const sectionTitle = getNodeText('[data-field="section_title"]', section);
                    if (sectionTitle) {{
                        lines.push(sectionTitle);
                        lines.push("");
                    }}

                    const itemOrder = ["item1", "item2"];
                    let itemCounter = 1;
                    itemOrder.forEach(function (itemKey) {{
                        const subtitle = getNodeText('[data-item="' + itemKey + '"][data-field="subtitle"]', section);
                        const body = getNodeText('[data-item="' + itemKey + '"][data-field="body"]', section);
                        const imageHintRaw = getNodeText('[data-item="' + itemKey + '"][data-field="image_hint"]', section);
                        const imageHint = imageHintRaw.replace(/^配图建议：?\\s*/, "").trim();

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

                const summaryTitle = getNodeText('[data-label="summary"]', page);
                const currentSummary = getNodeText('[data-field="summary"]', page);
                if (currentSummary) {{
                    lines.push(summaryTitle || "【总结】");
                    lines.push(currentSummary);
                }}

                const publishText = lines.join("\\n").trim();
                console.log("[copy-publish] publish text length:", publishText.length);
                return publishText;
            }}

            function fallbackCopyText(text) {{
                const textarea = document.createElement("textarea");
                textarea.value = text;
                textarea.setAttribute("readonly", "readonly");
                textarea.style.position = "fixed";
                textarea.style.left = "-9999px";
                document.body.appendChild(textarea);
                textarea.focus();
                textarea.select();

                let copied = false;
                try {{
                    copied = document.execCommand("copy");
                }} catch (err) {{
                    copied = false;
                }}

                document.body.removeChild(textarea);
                return copied;
            }}


            function buildEditablePayload() {{
                const page = document.querySelector(".page");
                const payload = {{
                    title: getNodeText('[data-field="title"]', page),
                    section_labels: {{
                        intro: getNodeText('[data-label="intro"]', page),
                        section1: labels.section1,
                        section2: labels.section2,
                        section3: labels.section3,
                        summary: getNodeText('[data-label="summary"]', page)
                    }},
                    intro: getNodeText('[data-field="intro"]', page),
                    section1: {{ title: "", item1: {{ subtitle: "", body: "", image_hint: "" }}, item2: {{ subtitle: "", body: "", image_hint: "" }} }},
                    section2: {{ title: "", item1: {{ subtitle: "", body: "", image_hint: "" }}, item2: {{ subtitle: "", body: "", image_hint: "" }} }},
                    section3: {{ title: "", item1: {{ subtitle: "", body: "", image_hint: "" }}, item2: {{ subtitle: "", body: "", image_hint: "" }} }},
                    summary: getNodeText('[data-field="summary"]', page)
                }};

                ["section1", "section2", "section3"].forEach(function (sectionKey) {{
                    const section = page.querySelector('.section-block[data-section="' + sectionKey + '"]');
                    if (!section) {{
                        return;
                    }}

                    payload[sectionKey].title = getNodeText('[data-field="section_title"]', section);

                    ["item1", "item2"].forEach(function (itemKey) {{
                        payload[sectionKey][itemKey].subtitle = getNodeText('[data-item="' + itemKey + '"][data-field="subtitle"]', section);
                        payload[sectionKey][itemKey].body = getNodeText('[data-item="' + itemKey + '"][data-field="body"]', section);
                        const hintRaw = getNodeText('[data-item="' + itemKey + '"][data-field="image_hint"]', section);
                        payload[sectionKey][itemKey].image_hint = hintRaw.replace(/^配图建议：?\\s*/, "").trim();
                    }});
                }});

                return payload;
            }}

            async function saveArticle() {{
                const payload = buildEditablePayload();
                try {{
                    const resp = await fetch("/article/{record_id}/save", {{
                        method: "POST",
                        headers: {{ "Content-Type": "application/json" }},
                        body: JSON.stringify(payload)
                    }});

                    if (!resp.ok) {{
                        throw new Error("save request failed");
                    }}

                    const data = await resp.json();
                    if (!data.ok) {{
                        throw new Error(data.message || "save failed");
                    }}

                    alert("保存成功");
                }} catch (err) {{
                    console.log("[save-article] save failed:", err);
                    alert("保存失败，请稍后重试");
                }}
            }}

            async function copyPublishText() {{
                console.log("[copy-publish] copy button clicked");
                const text = buildPublishText();
                if (!text) {{
                    alert("页面暂无可复制内容");
                    return;
                }}

                try {{
                    if (navigator.clipboard && navigator.clipboard.writeText) {{
                        await navigator.clipboard.writeText(text);
                    }} else {{
                        const copied = fallbackCopyText(text);
                        if (!copied) {{
                            throw new Error("fallback copy failed");
                        }}
                    }}
                    alert("已复制到剪贴板");
                }} catch (err) {{
                    console.log("[copy-publish] navigator copy failed, try fallback:", err);
                    const copied = fallbackCopyText(text);
                    if (copied) {{
                        alert("已复制到剪贴板");
                        return;
                    }}
                    alert("复制失败，请手动复制");
                }}
            }}

            document.getElementById("copyPublishBtn").addEventListener("click", copyPublishText);
            document.getElementById("saveArticleBtn").addEventListener("click", saveArticle);
        </script>
    </body>
    </html>
    """.format(
        title=title,
        labels=json.dumps({
            "section1": labels["section1"],
            "section2": labels["section2"],
            "section3": labels["section3"],
        }, ensure_ascii=False),
        intro_html=intro_html,
        section_html=section_html,
        summary_html=summary_html,
        record_id=record_id
    )
    return html


def render_industry_news_html(article_json: dict, record_id: str = "") -> str:
    title = normalize_text(article_json.get("title")) or "行业新闻"
    intro = normalize_text(article_json.get("intro"))
    event_summary = normalize_text(article_json.get("event_summary"))
    industry_background = normalize_text(article_json.get("industry_background"))
    impact_analysis = normalize_text(article_json.get("impact_analysis"))
    industry_insight = normalize_text(article_json.get("industry_insight"))
    labels = _normalize_section_labels(article_json, {
        "intro": "【导语】",
        "event_summary": "【事件概述】",
        "industry_background": "【行业背景】",
        "impact_analysis": "【影响分析】",
        "industry_insight": "【行业启示】",
    })

    html = """
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
            .save-btn {{
                border: none;
                background: #16a34a;
                color: #fff;
                padding: 10px 16px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 14px;
                font-weight: bold;
                margin-left: 10px;
            }}
            .save-btn:hover {{
                background: #15803d;
            }}
            .article-title {{
                font-size: 30px;
                font-weight: bold;
                line-height: 1.4;
                margin-bottom: 24px;
                color: #111;
                text-align: center;
            }}
            .section {{
                margin-top: 20px;
            }}
            .section-title {{
                font-size: 20px;
                font-weight: bold;
                color: #111827;
                margin-bottom: 10px;
            }}
            .paragraph {{
                font-size: 16px;
                line-height: 1.9;
                color: #2f3a4a;
                white-space: pre-wrap;
            }}
            [contenteditable="true"]:focus {{
                outline: 2px solid #93c5fd;
                border-radius: 6px;
                background: #f8fbff;
            }}
        </style>
    </head>
    <body>
        <div class="page" id="industryNewsPage">
            <div class="action-bar">
                <button type="button" class="copy-btn" id="copyPublishBtn">复制发布稿</button>
                <button type="button" class="save-btn" id="saveArticleBtn">保存修改</button>
            </div>

            <div class="article-title" contenteditable="true" data-field="title">{title}</div>

            <div class="section">
                <div class="section-title" contenteditable="true" data-label="intro">{intro_label}</div>
                <div class="paragraph" contenteditable="true" data-field="intro">{intro}</div>
            </div>

            <div class="section">
                <div class="section-title" contenteditable="true" data-label="event_summary">{event_summary_label}</div>
                <div class="paragraph" contenteditable="true" data-field="event_summary">{event_summary}</div>
            </div>

            <div class="section">
                <div class="section-title" contenteditable="true" data-label="industry_background">{industry_background_label}</div>
                <div class="paragraph" contenteditable="true" data-field="industry_background">{industry_background}</div>
            </div>

            <div class="section">
                <div class="section-title" contenteditable="true" data-label="impact_analysis">{impact_analysis_label}</div>
                <div class="paragraph" contenteditable="true" data-field="impact_analysis">{impact_analysis}</div>
            </div>

            <div class="section">
                <div class="section-title" contenteditable="true" data-label="industry_insight">{industry_insight_label}</div>
                <div class="paragraph" contenteditable="true" data-field="industry_insight">{industry_insight}</div>
            </div>
        </div>

        <script>
            function getNodeText(selector) {{
                const el = document.querySelector(selector);
                if (!el) {{
                    return "";
                }}
                return (el.innerText || "").replace(/\s+$/g, "").trim();
            }}

            function fallbackCopyText(text) {{
                const textarea = document.createElement("textarea");
                textarea.value = text;
                textarea.style.position = "fixed";
                textarea.style.opacity = "0";
                textarea.style.left = "-9999px";
                document.body.appendChild(textarea);
                textarea.focus();
                textarea.select();
                let copied = false;
                try {{
                    copied = document.execCommand("copy");
                }} catch (e) {{
                    copied = false;
                }}
                document.body.removeChild(textarea);
                return copied;
            }}

            function buildEditablePayload() {{
                return {{
                    title: getNodeText('[data-field="title"]'),
                    section_labels: {{
                        intro: getNodeText('[data-label="intro"]'),
                        event_summary: getNodeText('[data-label="event_summary"]'),
                        industry_background: getNodeText('[data-label="industry_background"]'),
                        impact_analysis: getNodeText('[data-label="impact_analysis"]'),
                        industry_insight: getNodeText('[data-label="industry_insight"]')
                    }},
                    intro: getNodeText('[data-field="intro"]'),
                    event_summary: getNodeText('[data-field="event_summary"]'),
                    industry_background: getNodeText('[data-field="industry_background"]'),
                    impact_analysis: getNodeText('[data-field="impact_analysis"]'),
                    industry_insight: getNodeText('[data-field="industry_insight"]')
                }};
            }}

            function buildPublishText() {{
                const payload = buildEditablePayload();
                const lines = [];

                lines.push('标题：' + (payload.title || ''));
                lines.push('');

                lines.push(payload.section_labels.intro || '【导语】');
                lines.push(payload.intro || '');
                lines.push('');

                lines.push(payload.section_labels.event_summary || '【事件概述】');
                lines.push(payload.event_summary || '');
                lines.push('');

                lines.push(payload.section_labels.industry_background || '【行业背景】');
                lines.push(payload.industry_background || '');
                lines.push('');

                lines.push(payload.section_labels.impact_analysis || '【影响分析】');
                lines.push(payload.impact_analysis || '');
                lines.push('');

                lines.push(payload.section_labels.industry_insight || '【行业启示】');
                lines.push(payload.industry_insight || '');

                return lines.join('\\n').trim();
            }}

            async function copyPublishText() {{
                const text = buildPublishText();
                if (!text) {{
                    alert('页面暂无可复制内容');
                    return;
                }}

                try {{
                    if (navigator.clipboard && navigator.clipboard.writeText) {{
                        await navigator.clipboard.writeText(text);
                    }} else {{
                        const copied = fallbackCopyText(text);
                        if (!copied) {{
                            throw new Error('fallback copy failed');
                        }}
                    }}
                    alert('已复制到剪贴板');
                }} catch (err) {{
                    const copied = fallbackCopyText(text);
                    if (copied) {{
                        alert('已复制到剪贴板');
                        return;
                    }}
                    alert('复制失败，请手动复制');
                }}
            }}

            async function saveArticle() {{
                const payload = buildEditablePayload();

                try {{
                    const resp = await fetch('/article/{record_id}/save', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify(payload)
                    }});

                    if (!resp.ok) {{
                        throw new Error('save request failed');
                    }}

                    const data = await resp.json();
                    if (!data.ok) {{
                        throw new Error(data.message || 'save failed');
                    }}

                    alert('保存成功');
                }} catch (err) {{
                    alert('保存失败，请稍后重试');
                }}
            }}

            document.getElementById('copyPublishBtn').addEventListener('click', copyPublishText);
            document.getElementById('saveArticleBtn').addEventListener('click', saveArticle);
        </script>
    </body>
    </html>
    """.format(
        title=title,
        intro_label=labels["intro"],
        event_summary_label=labels["event_summary"],
        industry_background_label=labels["industry_background"],
        impact_analysis_label=labels["impact_analysis"],
        industry_insight_label=labels["industry_insight"],
        intro=intro,
        event_summary=event_summary,
        industry_background=industry_background,
        impact_analysis=impact_analysis,
        industry_insight=industry_insight,
        record_id=record_id,
    )
    return html


def render_policy_interpretation_html(article_json: dict, record_id: str = "") -> str:
    title = normalize_text(article_json.get("title")) or "政策解读"
    intro = normalize_text(article_json.get("intro"))
    policy_background = normalize_text(article_json.get("policy_background"))
    core_content = normalize_text(article_json.get("core_content"))
    industry_impact = normalize_text(article_json.get("industry_impact"))
    advice = normalize_text(article_json.get("advice"))
    summary = normalize_text(article_json.get("summary"))
    labels = _normalize_section_labels(article_json, {
        "intro": "【导语】",
        "policy_background": "【政策背景】",
        "core_content": "【政策核心内容】",
        "industry_impact": "【对行业的影响】",
        "advice": "【对企业/用户的建议】",
        "summary": "【总结】",
    })

    html = """
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
            .save-btn {{
                border: none;
                background: #16a34a;
                color: #fff;
                padding: 10px 16px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 14px;
                font-weight: bold;
                margin-left: 10px;
            }}
            .save-btn:hover {{
                background: #15803d;
            }}
            .article-title {{
                font-size: 30px;
                font-weight: bold;
                line-height: 1.4;
                margin-bottom: 24px;
                color: #111;
                text-align: center;
            }}
            .section {{
                margin-top: 20px;
            }}
            .section-title {{
                font-size: 20px;
                font-weight: bold;
                color: #111827;
                margin-bottom: 10px;
            }}
            .paragraph {{
                font-size: 16px;
                line-height: 1.9;
                color: #2f3a4a;
                white-space: pre-wrap;
            }}
            [contenteditable="true"]:focus {{
                outline: 2px solid #93c5fd;
                border-radius: 6px;
                background: #f8fbff;
            }}
        </style>
    </head>
    <body>
        <div class="page" id="policyPage">
            <div class="action-bar">
                <button type="button" class="copy-btn" id="copyPublishBtn">复制发布稿</button>
                <button type="button" class="save-btn" id="saveArticleBtn">保存修改</button>
            </div>

            <div class="article-title" contenteditable="true" data-field="title">{title}</div>

            <div class="section">
                <div class="section-title" contenteditable="true" data-label="intro">{intro_label}</div>
                <div class="paragraph" contenteditable="true" data-field="intro">{intro}</div>
            </div>

            <div class="section">
                <div class="section-title" contenteditable="true" data-label="policy_background">{policy_background_label}</div>
                <div class="paragraph" contenteditable="true" data-field="policy_background">{policy_background}</div>
            </div>

            <div class="section">
                <div class="section-title" contenteditable="true" data-label="core_content">{core_content_label}</div>
                <div class="paragraph" contenteditable="true" data-field="core_content">{core_content}</div>
            </div>

            <div class="section">
                <div class="section-title" contenteditable="true" data-label="industry_impact">{industry_impact_label}</div>
                <div class="paragraph" contenteditable="true" data-field="industry_impact">{industry_impact}</div>
            </div>

            <div class="section">
                <div class="section-title" contenteditable="true" data-label="advice">{advice_label}</div>
                <div class="paragraph" contenteditable="true" data-field="advice">{advice}</div>
            </div>

            <div class="section">
                <div class="section-title" contenteditable="true" data-label="summary">{summary_label}</div>
                <div class="paragraph" contenteditable="true" data-field="summary">{summary}</div>
            </div>
        </div>

        <script>
            function getNodeText(selector) {{
                const el = document.querySelector(selector);
                return el ? (el.innerText || "").trim() : "";
            }}

            function fallbackCopyText(text) {{
                const textarea = document.createElement("textarea");
                textarea.value = text;
                textarea.style.position = "fixed";
                textarea.style.opacity = "0";
                textarea.style.left = "-9999px";
                document.body.appendChild(textarea);
                textarea.focus();
                textarea.select();
                let copied = false;
                try {{
                    copied = document.execCommand("copy");
                }} catch (e) {{
                    copied = false;
                }}
                document.body.removeChild(textarea);
                return copied;
            }}

            function buildEditablePayload() {{
                return {{
                    title: getNodeText('[data-field="title"]'),
                    section_labels: {{
                        intro: getNodeText('[data-label="intro"]'),
                        policy_background: getNodeText('[data-label="policy_background"]'),
                        core_content: getNodeText('[data-label="core_content"]'),
                        industry_impact: getNodeText('[data-label="industry_impact"]'),
                        advice: getNodeText('[data-label="advice"]'),
                        summary: getNodeText('[data-label="summary"]')
                    }},
                    intro: getNodeText('[data-field="intro"]'),
                    policy_background: getNodeText('[data-field="policy_background"]'),
                    core_content: getNodeText('[data-field="core_content"]'),
                    industry_impact: getNodeText('[data-field="industry_impact"]'),
                    advice: getNodeText('[data-field="advice"]'),
                    summary: getNodeText('[data-field="summary"]')
                }};
            }}

            function buildPublishText() {{
                const payload = buildEditablePayload();
                const lines = [];

                lines.push('标题：' + (payload.title || ''));
                lines.push('');

                lines.push(payload.section_labels.intro || '【导语】');
                lines.push(payload.intro || '');
                lines.push('');

                lines.push(payload.section_labels.policy_background || '【政策背景】');
                lines.push(payload.policy_background || '');
                lines.push('');

                lines.push(payload.section_labels.core_content || '【政策核心内容】');
                lines.push(payload.core_content || '');
                lines.push('');

                lines.push(payload.section_labels.industry_impact || '【对行业的影响】');
                lines.push(payload.industry_impact || '');
                lines.push('');

                lines.push(payload.section_labels.advice || '【对企业/用户的建议】');
                lines.push(payload.advice || '');
                lines.push('');

                lines.push(payload.section_labels.summary || '【总结】');
                lines.push(payload.summary || '');

                return lines.join('\\n').trim();
            }}

            async function copyPublishText() {{
                const text = buildPublishText();
                if (!text) {{
                    alert('页面暂无可复制内容');
                    return;
                }}

                try {{
                    if (navigator.clipboard && navigator.clipboard.writeText) {{
                        await navigator.clipboard.writeText(text);
                    }} else {{
                        const copied = fallbackCopyText(text);
                        if (!copied) {{
                            throw new Error('fallback copy failed');
                        }}
                    }}
                    alert('已复制到剪贴板');
                }} catch (err) {{
                    const copied = fallbackCopyText(text);
                    if (copied) {{
                        alert('已复制到剪贴板');
                        return;
                    }}
                    alert('复制失败，请手动复制');
                }}
            }}

            async function saveArticle() {{
                const payload = buildEditablePayload();

                try {{
                    const resp = await fetch('/article/{record_id}/save', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify(payload)
                    }});

                    if (!resp.ok) {{
                        throw new Error('save request failed');
                    }}

                    const data = await resp.json();
                    if (!data.ok) {{
                        throw new Error(data.message || 'save failed');
                    }}

                    alert('保存成功');
                }} catch (err) {{
                    alert('保存失败，请稍后重试');
                }}
            }}

            document.getElementById('copyPublishBtn').addEventListener('click', copyPublishText);
            document.getElementById('saveArticleBtn').addEventListener('click', saveArticle);
        </script>
    </body>
    </html>
    """.format(
        title=title,
        intro_label=labels["intro"],
        policy_background_label=labels["policy_background"],
        core_content_label=labels["core_content"],
        industry_impact_label=labels["industry_impact"],
        advice_label=labels["advice"],
        summary_label=labels["summary"],
        intro=intro,
        policy_background=policy_background,
        core_content=core_content,
        industry_impact=industry_impact,
        advice=advice,
        summary=summary,
        record_id=record_id,
    )
    return html


def render_product_intro_html(article_json: dict, record_id: str = "") -> str:
    title = normalize_text(article_json.get("title")) or "产品介绍"
    intro = normalize_text(article_json.get("intro"))
    product_positioning = normalize_text(article_json.get("product_positioning"))
    highlights = article_json.get("core_highlights", [])
    application_scenarios = normalize_text(article_json.get("application_scenarios"))
    customer_value = normalize_text(article_json.get("customer_value"))
    summary = normalize_text(article_json.get("summary"))
    labels = _normalize_section_labels(article_json, {
        "intro": "【导语】",
        "product_positioning": "【产品背景/定位】",
        "core_highlights": "【核心亮点】",
        "application_scenarios": "【应用场景】",
        "customer_value": "【客户价值】",
        "summary": "【总结】",
    })

    if not isinstance(highlights, list):
        highlights = [normalize_text(highlights)]

    highlight_html_parts = []
    for item in highlights:
        item_text = normalize_text(item)
        if not item_text:
            continue
        highlight_html_parts.append('<li class="highlight-item" contenteditable="true" data-highlight-item="1">{}</li>'.format(item_text))

    if not highlight_html_parts:
        highlight_html_parts.append('<li class="highlight-item" contenteditable="true" data-highlight-item="1"></li>')

    highlights_html = "".join(highlight_html_parts)

    html = """
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
            .save-btn {{
                border: none;
                background: #16a34a;
                color: #fff;
                padding: 10px 16px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 14px;
                font-weight: bold;
                margin-left: 10px;
            }}
            .save-btn:hover {{
                background: #15803d;
            }}
            .article-title {{
                font-size: 30px;
                font-weight: bold;
                line-height: 1.4;
                margin-bottom: 24px;
                color: #111;
                text-align: center;
            }}
            .section {{
                margin-top: 20px;
            }}
            .section-title {{
                font-size: 20px;
                font-weight: bold;
                color: #111827;
                margin-bottom: 10px;
            }}
            .paragraph {{
                font-size: 16px;
                line-height: 1.9;
                color: #2f3a4a;
                white-space: pre-wrap;
            }}
            .highlight-list {{
                margin: 0;
                padding-left: 22px;
            }}
            .highlight-item {{
                font-size: 16px;
                line-height: 1.9;
                color: #2f3a4a;
                margin-bottom: 6px;
            }}
            [contenteditable="true"]:focus {{
                outline: 2px solid #93c5fd;
                border-radius: 6px;
                background: #f8fbff;
            }}
        </style>
    </head>
    <body>
        <div class="page" id="productIntroPage">
            <div class="action-bar">
                <button type="button" class="copy-btn" id="copyPublishBtn">复制发布稿</button>
                <button type="button" class="save-btn" id="saveArticleBtn">保存修改</button>
            </div>

            <div class="article-title" contenteditable="true" data-field="title">{title}</div>

            <div class="section">
                <div class="section-title" contenteditable="true" data-label="intro">{intro_label}</div>
                <div class="paragraph" contenteditable="true" data-field="intro">{intro}</div>
            </div>

            <div class="section">
                <div class="section-title" contenteditable="true" data-label="product_positioning">{product_positioning_label}</div>
                <div class="paragraph" contenteditable="true" data-field="product_positioning">{product_positioning}</div>
            </div>

            <div class="section">
                <div class="section-title" contenteditable="true" data-label="core_highlights">{core_highlights_label}</div>
                <ol class="highlight-list" id="highlightList">{highlights_html}</ol>
            </div>

            <div class="section">
                <div class="section-title" contenteditable="true" data-label="application_scenarios">{application_scenarios_label}</div>
                <div class="paragraph" contenteditable="true" data-field="application_scenarios">{application_scenarios}</div>
            </div>

            <div class="section">
                <div class="section-title" contenteditable="true" data-label="customer_value">{customer_value_label}</div>
                <div class="paragraph" contenteditable="true" data-field="customer_value">{customer_value}</div>
            </div>

            <div class="section">
                <div class="section-title" contenteditable="true" data-label="summary">{summary_label}</div>
                <div class="paragraph" contenteditable="true" data-field="summary">{summary}</div>
            </div>
        </div>

        <script>
            function getNodeText(selector) {{
                const el = document.querySelector(selector);
                return el ? (el.innerText || "").trim() : "";
            }}

            function getHighlightList() {{
                const list = [];
                document.querySelectorAll('#highlightList .highlight-item').forEach(function (el) {{
                    const text = (el.innerText || '').trim();
                    if (text) {{
                        list.push(text);
                    }}
                }});
                return list;
            }}

            function fallbackCopyText(text) {{
                const textarea = document.createElement("textarea");
                textarea.value = text;
                textarea.style.position = "fixed";
                textarea.style.opacity = "0";
                textarea.style.left = "-9999px";
                document.body.appendChild(textarea);
                textarea.focus();
                textarea.select();
                let copied = false;
                try {{
                    copied = document.execCommand("copy");
                }} catch (e) {{
                    copied = false;
                }}
                document.body.removeChild(textarea);
                return copied;
            }}

            function buildEditablePayload() {{
                return {{
                    title: getNodeText('[data-field="title"]'),
                    section_labels: {{
                        intro: getNodeText('[data-label="intro"]'),
                        product_positioning: getNodeText('[data-label="product_positioning"]'),
                        core_highlights: getNodeText('[data-label="core_highlights"]'),
                        application_scenarios: getNodeText('[data-label="application_scenarios"]'),
                        customer_value: getNodeText('[data-label="customer_value"]'),
                        summary: getNodeText('[data-label="summary"]')
                    }},
                    intro: getNodeText('[data-field="intro"]'),
                    product_positioning: getNodeText('[data-field="product_positioning"]'),
                    core_highlights: getHighlightList(),
                    application_scenarios: getNodeText('[data-field="application_scenarios"]'),
                    customer_value: getNodeText('[data-field="customer_value"]'),
                    summary: getNodeText('[data-field="summary"]')
                }};
            }}

            function buildPublishText() {{
                const payload = buildEditablePayload();
                const lines = [];

                lines.push('标题：' + (payload.title || ''));
                lines.push('');

                lines.push(payload.section_labels.intro || '【导语】');
                lines.push(payload.intro || '');
                lines.push('');

                lines.push(payload.section_labels.product_positioning || '【产品背景/定位】');
                lines.push(payload.product_positioning || '');
                lines.push('');

                lines.push(payload.section_labels.core_highlights || '【核心亮点】');
                if (payload.core_highlights && payload.core_highlights.length > 0) {{
                    payload.core_highlights.forEach(function (item, idx) {{
                        lines.push((idx + 1) + '. ' + item);
                    }});
                }}
                lines.push('');

                lines.push(payload.section_labels.application_scenarios || '【应用场景】');
                lines.push(payload.application_scenarios || '');
                lines.push('');

                lines.push(payload.section_labels.customer_value || '【客户价值】');
                lines.push(payload.customer_value || '');
                lines.push('');

                lines.push(payload.section_labels.summary || '【总结】');
                lines.push(payload.summary || '');

                return lines.join('\\n').trim();
            }}

            async function copyPublishText() {{
                const text = buildPublishText();
                if (!text) {{
                    alert('页面暂无可复制内容');
                    return;
                }}

                try {{
                    if (navigator.clipboard && navigator.clipboard.writeText) {{
                        await navigator.clipboard.writeText(text);
                    }} else {{
                        const copied = fallbackCopyText(text);
                        if (!copied) {{
                            throw new Error('fallback copy failed');
                        }}
                    }}
                    alert('已复制到剪贴板');
                }} catch (err) {{
                    const copied = fallbackCopyText(text);
                    if (copied) {{
                        alert('已复制到剪贴板');
                        return;
                    }}
                    alert('复制失败，请手动复制');
                }}
            }}

            async function saveArticle() {{
                const payload = buildEditablePayload();

                try {{
                    const resp = await fetch('/article/{record_id}/save', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify(payload)
                    }});

                    if (!resp.ok) {{
                        throw new Error('save request failed');
                    }}

                    const data = await resp.json();
                    if (!data.ok) {{
                        throw new Error(data.message || 'save failed');
                    }}

                    alert('保存成功');
                }} catch (err) {{
                    alert('保存失败，请稍后重试');
                }}
            }}

            document.getElementById('copyPublishBtn').addEventListener('click', copyPublishText);
            document.getElementById('saveArticleBtn').addEventListener('click', saveArticle);
        </script>
    </body>
    </html>
    """.format(
        title=title,
        intro_label=labels["intro"],
        product_positioning_label=labels["product_positioning"],
        core_highlights_label=labels["core_highlights"],
        application_scenarios_label=labels["application_scenarios"],
        customer_value_label=labels["customer_value"],
        summary_label=labels["summary"],
        intro=intro,
        product_positioning=product_positioning,
        highlights_html=highlights_html,
        application_scenarios=application_scenarios,
        customer_value=customer_value,
        summary=summary,
        record_id=record_id,
    )
    return html


def render_case_analysis_html(article_json: dict, record_id: str = "") -> str:
    title = normalize_text(article_json.get("title")) or "案例分析"
    intro = normalize_text(article_json.get("intro"))
    project_background = normalize_text(article_json.get("project_background"))
    pain_points = normalize_text(article_json.get("pain_points"))
    solution = normalize_text(article_json.get("solution"))
    result = normalize_text(article_json.get("result"))
    insight = normalize_text(article_json.get("insight"))
    labels = _normalize_section_labels(article_json, {
        "intro": "【导语】",
        "project_background": "【项目背景】",
        "pain_points": "【项目难点/痛点】",
        "solution": "【解决方案】",
        "result": "【实施效果】",
        "insight": "【总结与启示】",
    })

    html = """
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
            .save-btn {{
                border: none;
                background: #16a34a;
                color: #fff;
                padding: 10px 16px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 14px;
                font-weight: bold;
                margin-left: 10px;
            }}
            .save-btn:hover {{
                background: #15803d;
            }}
            .article-title {{
                font-size: 30px;
                font-weight: bold;
                line-height: 1.4;
                margin-bottom: 24px;
                color: #111;
                text-align: center;
            }}
            .section {{
                margin-top: 20px;
            }}
            .section-title {{
                font-size: 20px;
                font-weight: bold;
                color: #111827;
                margin-bottom: 10px;
            }}
            .paragraph {{
                font-size: 16px;
                line-height: 1.9;
                color: #2f3a4a;
                white-space: pre-wrap;
            }}
            [contenteditable="true"]:focus {{
                outline: 2px solid #93c5fd;
                border-radius: 6px;
                background: #f8fbff;
            }}
        </style>
    </head>
    <body>
        <div class="page" id="caseAnalysisPage">
            <div class="action-bar">
                <button type="button" class="copy-btn" id="copyPublishBtn">复制发布稿</button>
                <button type="button" class="save-btn" id="saveArticleBtn">保存修改</button>
            </div>

            <div class="article-title" contenteditable="true" data-field="title">{title}</div>

            <div class="section">
                <div class="section-title" contenteditable="true" data-label="intro">{intro_label}</div>
                <div class="paragraph" contenteditable="true" data-field="intro">{intro}</div>
            </div>

            <div class="section">
                <div class="section-title" contenteditable="true" data-label="project_background">{project_background_label}</div>
                <div class="paragraph" contenteditable="true" data-field="project_background">{project_background}</div>
            </div>

            <div class="section">
                <div class="section-title" contenteditable="true" data-label="pain_points">{pain_points_label}</div>
                <div class="paragraph" contenteditable="true" data-field="pain_points">{pain_points}</div>
            </div>

            <div class="section">
                <div class="section-title" contenteditable="true" data-label="solution">{solution_label}</div>
                <div class="paragraph" contenteditable="true" data-field="solution">{solution}</div>
            </div>

            <div class="section">
                <div class="section-title" contenteditable="true" data-label="result">{result_label}</div>
                <div class="paragraph" contenteditable="true" data-field="result">{result}</div>
            </div>

            <div class="section">
                <div class="section-title" contenteditable="true" data-label="insight">{insight_label}</div>
                <div class="paragraph" contenteditable="true" data-field="insight">{insight}</div>
            </div>
        </div>

        <script>
            function getNodeText(selector) {{
                const el = document.querySelector(selector);
                return el ? (el.innerText || "").trim() : "";
            }}

            function fallbackCopyText(text) {{
                const textarea = document.createElement("textarea");
                textarea.value = text;
                textarea.style.position = "fixed";
                textarea.style.opacity = "0";
                textarea.style.left = "-9999px";
                document.body.appendChild(textarea);
                textarea.focus();
                textarea.select();
                let copied = false;
                try {{
                    copied = document.execCommand("copy");
                }} catch (e) {{
                    copied = false;
                }}
                document.body.removeChild(textarea);
                return copied;
            }}

            function buildEditablePayload() {{
                return {{
                    title: getNodeText('[data-field="title"]'),
                    section_labels: {{
                        intro: getNodeText('[data-label="intro"]'),
                        project_background: getNodeText('[data-label="project_background"]'),
                        pain_points: getNodeText('[data-label="pain_points"]'),
                        solution: getNodeText('[data-label="solution"]'),
                        result: getNodeText('[data-label="result"]'),
                        insight: getNodeText('[data-label="insight"]')
                    }},
                    intro: getNodeText('[data-field="intro"]'),
                    project_background: getNodeText('[data-field="project_background"]'),
                    pain_points: getNodeText('[data-field="pain_points"]'),
                    solution: getNodeText('[data-field="solution"]'),
                    result: getNodeText('[data-field="result"]'),
                    insight: getNodeText('[data-field="insight"]')
                }};
            }}

            function buildPublishText() {{
                const payload = buildEditablePayload();
                const lines = [];

                lines.push('标题：' + (payload.title || ''));
                lines.push('');

                lines.push(payload.section_labels.intro || '【导语】');
                lines.push(payload.intro || '');
                lines.push('');

                lines.push(payload.section_labels.project_background || '【项目背景】');
                lines.push(payload.project_background || '');
                lines.push('');

                lines.push(payload.section_labels.pain_points || '【项目难点/痛点】');
                lines.push(payload.pain_points || '');
                lines.push('');

                lines.push(payload.section_labels.solution || '【解决方案】');
                lines.push(payload.solution || '');
                lines.push('');

                lines.push(payload.section_labels.result || '【实施效果】');
                lines.push(payload.result || '');
                lines.push('');

                lines.push(payload.section_labels.insight || '【总结与启示】');
                lines.push(payload.insight || '');

                return lines.join('\\n').trim();
            }}

            async function copyPublishText() {{
                const text = buildPublishText();
                if (!text) {{
                    alert('页面暂无可复制内容');
                    return;
                }}

                try {{
                    if (navigator.clipboard && navigator.clipboard.writeText) {{
                        await navigator.clipboard.writeText(text);
                    }} else {{
                        const copied = fallbackCopyText(text);
                        if (!copied) {{
                            throw new Error('fallback copy failed');
                        }}
                    }}
                    alert('已复制到剪贴板');
                }} catch (err) {{
                    const copied = fallbackCopyText(text);
                    if (copied) {{
                        alert('已复制到剪贴板');
                        return;
                    }}
                    alert('复制失败，请手动复制');
                }}
            }}

            async function saveArticle() {{
                const payload = buildEditablePayload();

                try {{
                    const resp = await fetch('/article/{record_id}/save', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify(payload)
                    }});

                    if (!resp.ok) {{
                        throw new Error('save request failed');
                    }}

                    const data = await resp.json();
                    if (!data.ok) {{
                        throw new Error(data.message || 'save failed');
                    }}

                    alert('保存成功');
                }} catch (err) {{
                    alert('保存失败，请稍后重试');
                }}
            }}

            document.getElementById('copyPublishBtn').addEventListener('click', copyPublishText);
            document.getElementById('saveArticleBtn').addEventListener('click', saveArticle);
        </script>
    </body>
    </html>
    """.format(
        title=title,
        intro_label=labels["intro"],
        project_background_label=labels["project_background"],
        pain_points_label=labels["pain_points"],
        solution_label=labels["solution"],
        result_label=labels["result"],
        insight_label=labels["insight"],
        intro=intro,
        project_background=project_background,
        pain_points=pain_points,
        solution=solution,
        result=result,
        insight=insight,
        record_id=record_id,
    )
    return html


def render_article_html_by_template(template: str, article_json: dict, record_id: str = "") -> str:
    if template == "技术科普":
        return render_tech_pop_html(article_json, record_id=record_id)
    if template == "行业新闻":
        return render_industry_news_html(article_json, record_id=record_id)
    if template == "政策解读":
        return render_policy_interpretation_html(article_json, record_id=record_id)
    if template == "产品介绍":
        return render_product_intro_html(article_json, record_id=record_id)
    if template == "案例分析":
        return render_case_analysis_html(article_json, record_id=record_id)

    title, body = format_article_by_template(template, article_json)
    simple_html = """
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
    """.format(title=title, body=body)
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
