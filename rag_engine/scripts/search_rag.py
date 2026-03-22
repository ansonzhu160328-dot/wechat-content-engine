from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import requests


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config_loader import load_config


VECTOR_PATH = (PROJECT_ROOT / "rag_engine" / "output" / "rag_vectors.json").resolve()
ENDPOINT_ID = "ep-20260322001504-7hlz2"
QUERY = "重卡充电站投资逻辑是什么？"
TIMEOUT_SECONDS = 60
TOP_K = 3
PREVIEW_LENGTH = 120


def load_client_config() -> tuple[str, str]:
    try:
        config = load_config()
    except Exception as exc:
        raise RuntimeError(f"读取配置失败: {exc}") from exc

    doubao_config = config.get("doubao")
    if not isinstance(doubao_config, dict):
        raise RuntimeError("配置缺少 doubao 节点")

    api_key = doubao_config.get("api_key")
    base_url = doubao_config.get("base_url")
    if not isinstance(api_key, str) or not api_key.strip():
        raise RuntimeError("doubao.api_key 配置无效")
    if not isinstance(base_url, str) or not base_url.strip():
        raise RuntimeError("doubao.base_url 配置无效")

    return api_key, base_url.rstrip("/")


def load_vectors() -> list[dict[str, object]]:
    if not VECTOR_PATH.is_file():
        raise RuntimeError(f"向量文件不存在: {VECTOR_PATH}")

    try:
        rows = json.loads(VECTOR_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"向量文件 JSON 解析失败: {exc}") from exc

    if not isinstance(rows, list):
        raise RuntimeError("rag_vectors.json 格式无效，期望为 list")

    valid_rows: list[dict[str, object]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        embedding = row.get("embedding")
        if isinstance(embedding, list) and embedding:
            valid_rows.append(row)

    return valid_rows


def fetch_query_embedding(session: requests.Session, endpoint: str, api_key: str, text: str) -> list[float]:
    payload = {
        "model": ENDPOINT_ID,
        "input": [
            {
                "type": "text",
                "text": text,
            }
        ],
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    response = session.post(endpoint, headers=headers, json=payload, timeout=TIMEOUT_SECONDS)
    response.raise_for_status()
    result = response.json()

    data = result.get("data")
    if not isinstance(data, dict):
        raise RuntimeError(f"响应缺少 data: {result}")

    embedding = data.get("embedding")
    if not isinstance(embedding, list) or not embedding:
        raise RuntimeError(f"响应缺少 embedding 向量: {result}")

    return embedding


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        raise ValueError(f"向量维度不一致: {len(left)} != {len(right)}")

    dot = sum(float(a) * float(b) for a, b in zip(left, right))
    left_norm = math.sqrt(sum(float(value) * float(value) for value in left))
    right_norm = math.sqrt(sum(float(value) * float(value) for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


def main() -> int:
    try:
        api_key, base_url = load_client_config()
        rows = load_vectors()
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    if not rows:
        print(f"Query: {QUERY}")
        print(f"[FAIL] 可检索向量为空: {VECTOR_PATH}")
        return 1

    endpoint = f"{base_url}/embeddings/multimodal"
    try:
        with requests.Session() as session:
            query_embedding = fetch_query_embedding(session, endpoint, api_key, QUERY)
    except requests.RequestException as exc:
        detail = exc.response.text if exc.response is not None else str(exc)
        print(f"[FAIL] query embedding 调用失败: {detail}")
        return 1
    except Exception as exc:
        print(f"[FAIL] query embedding 解析失败: {exc}")
        return 1

    scored_rows: list[tuple[float, dict[str, object]]] = []
    for row in rows:
        embedding = row.get("embedding")
        if not isinstance(embedding, list) or not embedding:
            continue
        try:
            score = cosine_similarity(query_embedding, embedding)
        except ValueError:
            continue
        scored_rows.append((score, row))

    top_rows = sorted(scored_rows, key=lambda item: item[0], reverse=True)[:TOP_K]
    print(f"Query: {QUERY}")
    if not top_rows:
        print("[FAIL] 未找到可用检索结果")
        return 1

    for index, (score, row) in enumerate(top_rows, start=1):
        content = str(row.get("content", ""))
        preview = content[:PREVIEW_LENGTH]
        print("-" * 60)
        print(f"Top {index}")
        print(f"chunk_id: {row.get('chunk_id', '')}")
        print(f"doc_title: {row.get('doc_title', '')}")
        print(f"section_title: {row.get('section_title', '')}")
        print(f"score: {score:.6f}")
        print(f"content: {preview}")

    print(f"[OK] 返回 top {len(top_rows)} 结果")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
