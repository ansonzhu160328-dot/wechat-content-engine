from __future__ import annotations

import json
import sys
from pathlib import Path

import requests


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config_loader import load_config


INPUT_PATH = (PROJECT_ROOT / "rag_engine" / "output" / "rag_data.json").resolve()
OUTPUT_PATH = (PROJECT_ROOT / "rag_engine" / "output" / "rag_vectors.json").resolve()
ENDPOINT_ID = "ep-20260322001504-7hlz2"
TIMEOUT_SECONDS = 60


def load_embedding_client_config() -> tuple[str, str]:
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


def load_chunks() -> list[dict[str, object]]:
    if not INPUT_PATH.is_file():
        raise RuntimeError(f"输入文件不存在: {INPUT_PATH}")

    try:
        chunks = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"输入 JSON 解析失败: {exc}") from exc

    if not isinstance(chunks, list):
        raise RuntimeError("rag_data.json 格式无效，期望为 list")

    return chunks


def fetch_embedding(session: requests.Session, endpoint: str, api_key: str, content: str) -> list[float]:
    payload = {
        "model": ENDPOINT_ID,
        "input": [
            {
                "type": "text",
                "text": content,
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


def main() -> int:
    try:
        api_key, base_url = load_embedding_client_config()
        chunks = load_chunks()
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    endpoint = f"{base_url}/embeddings/multimodal"
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    print(f"项目根目录: {PROJECT_ROOT}")
    print(f"输入文件路径: {INPUT_PATH}")
    print(f"输出文件路径: {OUTPUT_PATH}")

    total_chunks = len(chunks)
    vector_rows: list[dict[str, object]] = []

    with requests.Session() as session:
        for index, chunk in enumerate(chunks, start=1):
            chunk_id = chunk.get("chunk_id", f"unknown_{index}")
            content = chunk.get("content")
            print(f"[{index}/{total_chunks}] 处理 chunk: {chunk_id}")

            if not isinstance(content, str) or not content.strip():
                print(f"[FAIL] 跳过 {chunk_id}: content 无效")
                continue

            try:
                embedding = fetch_embedding(session, endpoint, api_key, content)
            except (requests.RequestException, RuntimeError, ValueError) as exc:
                detail = exc.response.text if isinstance(exc, requests.RequestException) and exc.response is not None else str(exc)
                print(f"[FAIL] 跳过 {chunk_id}: {detail}")
                continue

            row = dict(chunk)
            row["embedding"] = embedding
            vector_rows.append(row)

    OUTPUT_PATH.write_text(json.dumps(vector_rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"总 chunk 数: {total_chunks}")
    print(f"[OK] 共处理 {len(vector_rows)} 个 chunk")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
