# -*- coding: utf-8 -*-

import os
import json
import threading
import traceback
from datetime import datetime

import requests
import yaml
from flask import Flask, request, jsonify, render_template_string

from doubao_client import call_doubao_generate

app = Flask(__name__)

ARTICLE_HTML_CACHE = {}

HOST = "0.0.0.0"
PORT = 7001


def log(*args):
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), *args, flush=True)


def load_config():
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "config",
        "config.yaml"
    )

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


config = load_config()

FEISHU_APP_ID = config["feishu"]["app_id"]
FEISHU_APP_SECRET = config["feishu"]["app_secret"]

BITABLE_APP_TOKEN = config["bitable"]["app_token"]
BITABLE_TABLE_ID = config["bitable"]["table_id"]


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

    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()

    data = resp.json()

    if data.get("code") != 0:
        raise Exception(f"写入多维表格失败: {data}")

    return data


def background_generate_job(form_data: dict):
    try:

        log("开始生成文章")

        article_data = call_doubao_generate(form_data)

        write_result = write_to_bitable(form_data, article_data)

        record_id = (
            write_result.get("data", {})
            .get("record", {})
            .get("record_id", "")
        )

        if record_id and article_data.get("html"):
            ARTICLE_HTML_CACHE[record_id] = article_data["html"]

        log("文章生成成功")

    except Exception as e:
        log("后台任务失败：", repr(e))
        traceback.print_exc()


PAGE_HTML = """
<html>
<body>

<h2>AI写稿助手</h2>

<form method="post" action="/submit_generate">

模板：
<select name="template">
<option value="行业新闻">行业新闻</option>
<option value="技术科普">技术科普</option>
<option value="政策解读">政策解读</option>
<option value="产品介绍">产品介绍</option>
<option value="案例分析">案例分析</option>
</select>

<br><br>

<textarea name="requirement" placeholder="写作要求"></textarea>

<br><br>

<textarea name="content1" placeholder="素材1"></textarea>

<br><br>

<textarea name="content2" placeholder="素材2"></textarea>

<br><br>

<textarea name="content3" placeholder="素材3"></textarea>

<br><br>

<button type="submit">生成文章</button>

</form>

</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(PAGE_HTML)


@app.route("/submit_generate", methods=["POST"])
def submit_generate():
    try:

        form_data = {
            "template": request.form.get("template"),
            "requirement": request.form.get("requirement"),
            "content1": request.form.get("content1"),
            "content2": request.form.get("content2"),
            "content3": request.form.get("content3"),
        }

        t = threading.Thread(
            target=background_generate_job,
            args=(form_data,),
            daemon=True
        )

        t.start()

        return "任务已提交"

    except Exception as e:

        traceback.print_exc()

        return str(e), 500


@app.route("/article/<record_id>")
def article_preview(record_id):

    html = ARTICLE_HTML_CACHE.get(record_id)

    if not html:
        return "未找到文章"

    return html


if __name__ == "__main__":
    app.run(host=HOST, port=PORT)
