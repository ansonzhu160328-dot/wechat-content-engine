import requests
import yaml
import os

from prompt_builder import build_prompt

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


