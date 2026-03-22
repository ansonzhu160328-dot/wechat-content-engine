from __future__ import annotations

from pathlib import Path

import requests

from search_rag import (
    PROJECT_ROOT,
    QUERY,
    TOP_K,
    VECTOR_PATH,
    collect_ranked_rows,
    fetch_query_embedding,
    load_client_config,
    load_vectors,
)


OUTPUT_PATH = (PROJECT_ROOT / "rag_engine" / "output" / "rag_context.txt").resolve()


def format_context(top_rows: list[dict[str, object]]) -> str:
    sections = [f"Query: {QUERY}", "", "以下为可用于写稿的 RAG 知识上下文："]
    for index, row in enumerate(top_rows, start=1):
        sections.extend(
            [
                f"知识片段 {index}",
                f"来源文档：{row.get('doc_title', '')}",
                f"章节：{row.get('section_title', '')}",
                f"相似度：{float(row.get('rerank_score', 0.0)):.4f}",
                f"内容：{row.get('content', '')}",
                "",
            ]
        )
    return "\n".join(sections).rstrip() + "\n"


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

    top_rows = collect_ranked_rows(query_embedding, rows)[:TOP_K]
    if not top_rows:
        print(f"Query: {QUERY}")
        print("[FAIL] 未找到可用检索结果")
        return 1

    context_text = format_context(top_rows)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(context_text, encoding="utf-8")
    print(context_text, end="")
    print(f"[OK] 已输出上下文到: {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
