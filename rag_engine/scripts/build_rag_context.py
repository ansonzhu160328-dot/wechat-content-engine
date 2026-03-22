from __future__ import annotations

import json
from pathlib import Path
from urllib import error, request

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


class _SimpleResponse:
    def __init__(self, status_code: int, body: str):
        self.status_code = status_code
        self._body = body

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(self._body)

    def json(self) -> dict[str, object]:
        return json.loads(self._body)


class _SimpleSession:
    def post(self, url: str, headers: dict[str, str], json: dict[str, object], timeout: int) -> _SimpleResponse:
        payload = __import__("json").dumps(json).encode("utf-8")
        req = request.Request(url, data=payload, headers=headers, method="POST")
        try:
            with request.urlopen(req, timeout=timeout) as response:
                body = response.read().decode("utf-8")
                return _SimpleResponse(response.status, body)
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            return _SimpleResponse(exc.code, body)


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
        query_embedding = fetch_query_embedding(_SimpleSession(), endpoint, api_key, QUERY)
    except Exception as exc:
        print(f"[FAIL] query embedding 获取失败: {exc}")
        return 1

    top_rows = collect_ranked_rows(QUERY, query_embedding, rows)[:TOP_K]
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
