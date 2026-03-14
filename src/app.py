# -*- coding: utf-8 -*-
import os
import json
import threading
import traceback
from datetime import datetime

import requests
from flask import Flask, request, jsonify, render_template_string

from prompt_builder import normalize_text
from doubao_client import call_doubao_generate, format_tech_pop, render_tech_pop_html
from config_loader import load_config

CONFIG = load_config()

app = Flask(__name__)
ARTICLE_HTML_CACHE = {}
ARTICLE_META_CACHE = {}

# =========================
# 从 config.yaml 读取配置
# =========================

APP_NAME = CONFIG["app"]["name"]
DEBUG = CONFIG["app"]["debug"]
HOST = CONFIG["app"]["host"]
PORT = CONFIG["app"]["port"]

ARK_API_KEY = CONFIG["doubao"]["api_key"]
ARK_BASE_URL = CONFIG["doubao"]["base_url"]
ARK_MODEL = CONFIG["doubao"]["model"]

FEISHU_APP_ID = CONFIG["feishu"]["app_id"]
FEISHU_APP_SECRET = CONFIG["feishu"]["app_secret"]
BITABLE_APP_TOKEN = CONFIG["feishu"]["app_token"]
BITABLE_TABLE_ID = CONFIG["feishu"]["table_id"]

LOG_DIR = CONFIG["paths"]["logs_dir"]
DATA_DIR = CONFIG["paths"]["data_dir"]

# 自动创建目录
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)


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




def update_bitable_record(record_id: str, title: str, body: str) -> dict:
    token = get_feishu_tenant_access_token()

    url = (
        f"https://open.feishu.cn/open-apis/bitable/v1/apps/{BITABLE_APP_TOKEN}"
        f"/tables/{BITABLE_TABLE_ID}/records/{record_id}"
    )
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "fields": {
            "news_title_raw": title,
            "article_body": body,
        }
    }

    log(f"开始更新飞书多维表格记录，record_id = {record_id}")
    resp = requests.put(url, headers=headers, json=payload, timeout=60)
    log("飞书更新状态码：", resp.status_code)
    log("飞书更新返回：", resp.text)

    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise Exception(f"更新多维表格失败: {data}")

    log("飞书多维表格更新成功")
    return data

def background_generate_job(form_data: dict):
    try:
        log("后台任务启动，form_data =", json.dumps(form_data, ensure_ascii=False))

        article_data = call_doubao_generate(
            form_data=form_data,
            ark_api_key=ARK_API_KEY,
            ark_base_url=ARK_BASE_URL,
            ark_model=ARK_MODEL,
        )
        log("文章生成成功，标题 =", article_data["title"])

        write_result = write_to_bitable(form_data, article_data)
        log("写表成功：", json.dumps(write_result, ensure_ascii=False))

        record_id = (
            write_result.get("data", {})
            .get("record", {})
            .get("record_id", "")
        )

        if record_id and article_data.get("html"):
            cached_html = article_data["html"].replace("/article//save", f"/article/{record_id}/save")
            ARTICLE_HTML_CACHE[record_id] = cached_html
            ARTICLE_META_CACHE[record_id] = {
                "template": normalize_text(form_data.get("template", "")),
            }
            log(f"HTML预览已缓存，record_id = {record_id}")
            log(f"预览地址：http://127.0.0.1:{PORT}/article/{record_id}")

    except Exception as e:
        log("后台任务失败：", repr(e))
        traceback.print_exc()


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


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "ok": True,
        "message": f"{APP_NAME} is running"
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


@app.route("/article/<record_id>/save", methods=["POST"])
def save_tech_pop_article(record_id):
    try:
        payload = request.get_json(force=True, silent=True) or {}

        if record_id not in ARTICLE_HTML_CACHE:
            return jsonify({"ok": False, "message": "未找到文章记录"}), 404

        template = normalize_text(ARTICLE_META_CACHE.get(record_id, {}).get("template", "技术科普"))

        if template != "技术科普":
            return jsonify({"ok": False, "message": "仅支持技术科普模板保存"}), 400

        if not isinstance(payload, dict):
            return jsonify({"ok": False, "message": "请求体格式错误"}), 400

        title, body = format_tech_pop(payload)
        html = render_tech_pop_html(payload, record_id=record_id)

        ARTICLE_HTML_CACHE[record_id] = html
        ARTICLE_META_CACHE[record_id] = {"template": "技术科普"}

        update_bitable_record(record_id=record_id, title=title, body=body)

        return jsonify({"ok": True, "message": "保存成功"})
    except Exception as e:
        log("save_tech_pop_article 异常：", repr(e))
        traceback.print_exc()
        return jsonify({"ok": False, "message": "保存失败，请稍后重试"}), 500


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
    app.run(host=HOST, port=PORT, debug=DEBUG)