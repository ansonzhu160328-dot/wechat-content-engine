from __future__ import annotations

from pathlib import Path

from build_rag_context import _SimpleSession, format_context
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


OUTPUT_PATH = (PROJECT_ROOT / "rag_engine" / "output" / "enhanced_prompt.txt").resolve()


def build_prompt(rag_context: str) -> str:
    return f"""你是一名专业的公众号文章写作助手，擅长将行业知识、投资逻辑和企业实践转化为清晰、专业、适合传播的公众号文章。

现在请围绕以下主题进行写作：
主题：{QUERY}

以下是企业知识库中检索到的参考内容，请优先吸收其核心观点与逻辑，但不要逐句照抄，也不要机械拼接：
{rag_context.strip()}

请基于以上主题和参考知识，写出一篇逻辑清晰、观点明确、适合公众号发布的文章。
要求：
1. 语言专业、自然，不要像资料堆砌
2. 结构完整，建议包含引入、分析、总结
3. 突出投资逻辑、收益逻辑和成本逻辑
4. 可以适当补充必要的过渡句，但不要脱离参考知识
5. 吸收观点，不要生硬照抄
6. 不要输出提示词说明，只输出最终文章
"""


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

    rag_context = format_context(top_rows)
    prompt_text = build_prompt(rag_context)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(prompt_text, encoding="utf-8")
    print(prompt_text, end="")
    print(f"[OK] 已输出增强版 Prompt 到: {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
