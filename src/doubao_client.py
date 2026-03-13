import os
import json
import requests
import yaml

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


def call_doubao_generate(form_data: dict):

    prompt = build_prompt(form_data)

    url = f"{DOUBAO_BASE_URL}/chat/completions"

    headers = {
        "Authorization": f"Bearer {DOUBAO_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": DOUBAO_MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    resp = requests.post(url, headers=headers, json=payload)

    resp.raise_for_status()

    data = resp.json()

    content = data["choices"][0]["message"]["content"]

    return {
        "title": "AI生成文章",
        "body": content,
        "html": f"<html><body><pre>{content}</pre></body></html>"
    }
