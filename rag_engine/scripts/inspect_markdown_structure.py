from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config_loader import load_config


FAIL_PREFIX = "[FAIL]"
OK_PREFIX = "[OK]"
SECTION_PREFIXES = ("## ", "### ")
TITLE_PREFIX = "# "
EXPECTED_PILOT_COUNT = 3


def load_rag_paths() -> tuple[Path, list[Path]]:
    try:
        config = load_config()
    except Exception as exc:
        raise RuntimeError(f"读取配置失败: {exc}") from exc

    rag_config = config.get("rag")
    if not isinstance(rag_config, dict):
        raise RuntimeError("配置缺少 rag 节点")

    knowledge_base_dir_value = rag_config.get("knowledge_base_dir")
    pilot_files = rag_config.get("pilot_files")

    if not isinstance(knowledge_base_dir_value, str) or not knowledge_base_dir_value.strip():
        raise RuntimeError("rag.knowledge_base_dir 配置无效")
    if not isinstance(pilot_files, list) or not all(isinstance(item, str) and item.strip() for item in pilot_files):
        raise RuntimeError("rag.pilot_files 配置无效")
    if len(pilot_files) != EXPECTED_PILOT_COUNT:
        raise RuntimeError(f"pilot_files 数量不符合预期: 期望 {EXPECTED_PILOT_COUNT} 个，实际 {len(pilot_files)} 个")

    knowledge_base_dir = (PROJECT_ROOT / knowledge_base_dir_value).resolve()
    pilot_paths = [knowledge_base_dir / pilot_file for pilot_file in pilot_files]
    return knowledge_base_dir, pilot_paths


def extract_title(lines: Iterable[str], fallback_title: str) -> str:
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(TITLE_PREFIX):
            title = stripped[len(TITLE_PREFIX) :].strip()
            if title:
                return title
    return fallback_title


def parse_sections(lines: list[str]) -> list[dict[str, str]]:
    sections: list[dict[str, str]] = []
    current_title: str | None = None
    current_body: list[str] = []

    def flush_section() -> None:
        nonlocal current_title, current_body
        if current_title is None:
            return

        body = "\n".join(line.rstrip() for line in current_body).strip()
        if body:
            sections.append({"title": current_title, "body": body})

        current_title = None
        current_body = []

    for raw_line in lines:
        line = raw_line.rstrip("\n")
        stripped = line.strip()

        if any(stripped.startswith(prefix) for prefix in SECTION_PREFIXES):
            flush_section()
            current_title = stripped.lstrip("#").strip()
            current_body = []
            continue

        if current_title is not None:
            current_body.append(line)

    flush_section()
    return sections


def inspect_document(markdown_path: Path) -> dict[str, object]:
    if not markdown_path.is_file():
        raise RuntimeError(f"试点文档不存在: {markdown_path}")

    content = markdown_path.read_text(encoding="utf-8")
    lines = content.splitlines()
    title = extract_title(lines, markdown_path.stem)
    sections = parse_sections(lines)

    return {
        "file_name": markdown_path.name,
        "document_title": title,
        "sections": sections,
    }


def main() -> int:
    try:
        knowledge_base_dir, pilot_paths = load_rag_paths()
    except Exception as exc:
        print(f"{FAIL_PREFIX} {exc}")
        return 1

    if not knowledge_base_dir.is_dir():
        print(f"{FAIL_PREFIX} 知识库目录不存在: {knowledge_base_dir}")
        return 1

    print(f"项目根目录: {PROJECT_ROOT}")
    print(f"配置文件路径: {(PROJECT_ROOT / 'config' / 'config.yaml').resolve()}")
    print(f"知识库目录: {knowledge_base_dir}")

    total_sections = 0
    parsed_count = 0

    for markdown_path in pilot_paths:
        try:
            result = inspect_document(markdown_path)
        except Exception as exc:
            print(f"{FAIL_PREFIX} {exc}")
            return 1

        sections = result["sections"]
        section_count = len(sections)
        total_sections += section_count
        parsed_count += 1

        print("-" * 60)
        print(f"文件名: {result['file_name']}")
        print(f"文档标题: {result['document_title']}")
        print(f"section 数量: {section_count}")

        for index, section in enumerate(sections, start=1):
            print(f"  {index}. {section['title']} ({len(section['body'])} 字符)")

    print("-" * 60)
    print(f"{OK_PREFIX} 共解析 {parsed_count} 篇文档，合计 {total_sections} 个 section")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
