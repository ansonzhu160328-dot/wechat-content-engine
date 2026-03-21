from __future__ import annotations

import json
from pathlib import Path

from inspect_markdown_structure import PROJECT_ROOT, FAIL_PREFIX, OK_PREFIX, inspect_document, load_rag_paths


OUTPUT_PATH = (PROJECT_ROOT / "rag_engine" / "output" / "rag_data.json").resolve()


def build_chunk_id(file_name: str, index: int) -> str:
    doc_code = file_name.split("-", 1)[0].strip()
    return f"{doc_code}_{index:03d}"


def build_chunks() -> tuple[list[dict[str, object]], dict[str, int]]:
    knowledge_base_dir, pilot_paths = load_rag_paths()
    if not knowledge_base_dir.is_dir():
        raise RuntimeError(f"知识库目录不存在: {knowledge_base_dir}")

    chunks: list[dict[str, object]] = []
    doc_chunk_counts: dict[str, int] = {}

    for markdown_path in pilot_paths:
        parsed = inspect_document(markdown_path)
        sections = parsed["sections"]
        file_name = str(parsed["file_name"])
        doc_title = str(parsed["document_title"])

        doc_chunk_counts[file_name] = len(sections)
        for index, section in enumerate(sections, start=1):
            section_title = str(section["title"])
            section_body = str(section["body"])
            content = f"{section_title}\n{section_body}".strip()

            chunks.append(
                {
                    "chunk_id": build_chunk_id(file_name, index),
                    "doc_name": file_name,
                    "doc_title": doc_title,
                    "section_title": section_title,
                    "content": content,
                    "char_count": len(content),
                }
            )

    return chunks, doc_chunk_counts


def main() -> int:
    try:
        chunks, doc_chunk_counts = build_chunks()
    except Exception as exc:
        print(f"{FAIL_PREFIX} {exc}")
        return 1

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"项目根目录: {PROJECT_ROOT}")
    print(f"输出文件: {OUTPUT_PATH}")
    for file_name, chunk_count in doc_chunk_counts.items():
        print(f"- {file_name}: {chunk_count} 个 chunk")
    print(f"{OK_PREFIX} 共生成 {len(chunks)} 个 chunk")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
