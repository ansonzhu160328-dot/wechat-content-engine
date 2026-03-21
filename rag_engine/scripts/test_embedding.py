from __future__ import annotations

import sys
from pathlib import Path

import requests


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config_loader import load_config


MODEL_NAME = "ep-20260322001504-7hlz2"
TEST_INPUT = "重卡充电站投资逻辑是什么？"
TIMEOUT_SECONDS = 60


def main() -> int:
    try:
        config = load_config()
    except Exception as exc:
        print(f"[FAIL] 读取配置失败: {exc}")
        return 1

    doubao_config = config.get("doubao")
    if not isinstance(doubao_config, dict):
        print("[FAIL] 配置缺少 doubao 节点")
        return 1

    api_key = doubao_config.get("api_key")
    base_url = doubao_config.get("base_url")
    if not isinstance(api_key, str) or not api_key.strip():
        print("[FAIL] doubao.api_key 配置无效")
        return 1
    if not isinstance(base_url, str) or not base_url.strip():
        print("[FAIL] doubao.base_url 配置无效")
        return 1

    endpoint = f"{base_url.rstrip('/')}/embeddings"
    payload = {
        "model": MODEL_NAME,
        "input": TEST_INPUT,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    print(f"请求地址: {endpoint}")
    print(f"模型: {MODEL_NAME}")
    print(f"输入文本: {TEST_INPUT}")

    try:
        response = requests.post(endpoint, headers=headers, json=payload, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        result = response.json()
    except requests.RequestException as exc:
        detail = exc.response.text if exc.response is not None else str(exc)
        print(f"[FAIL] embedding 接口调用失败: {detail}")
        return 1
    except ValueError as exc:
        print(f"[FAIL] 响应 JSON 解析失败: {exc}")
        return 1

    data = result.get("data")
    if not isinstance(data, list) or not data:
        print(f"[FAIL] 响应缺少 data: {result}")
        return 1

    first_item = data[0]
    if not isinstance(first_item, dict):
        print(f"[FAIL] data[0] 格式无效: {first_item}")
        return 1

    embedding = first_item.get("embedding")
    if not isinstance(embedding, list) or not embedding:
        print(f"[FAIL] 响应缺少 embedding 向量: {first_item}")
        return 1

    print(f"向量长度: {len(embedding)}")
    print(f"前5个数值: {embedding[:5]}")
    print("[OK] embedding 接口连通")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
