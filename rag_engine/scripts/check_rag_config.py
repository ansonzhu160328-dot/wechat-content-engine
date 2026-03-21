from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config_loader import load_config


OK_PREFIX = "[OK]"
FAIL_PREFIX = "[FAIL]"


def _resolve_project_path(project_root: Path, configured_path: str) -> Path:
    return (project_root / configured_path).resolve()


def main() -> int:
    try:
        config = load_config()
    except Exception as exc:
        print(f"{FAIL_PREFIX} 读取配置失败: {exc}")
        return 1

    rag_config = config.get("rag")
    if not isinstance(rag_config, dict):
        print(f"{FAIL_PREFIX} 配置缺少 rag 节点")
        return 1

    enabled = rag_config.get("enabled")
    knowledge_base_dir_value = rag_config.get("knowledge_base_dir")
    chunk_output_file_value = rag_config.get("chunk_output_file")
    pilot_files = rag_config.get("pilot_files")

    if not isinstance(knowledge_base_dir_value, str) or not knowledge_base_dir_value.strip():
        print(f"{FAIL_PREFIX} rag.knowledge_base_dir 配置无效")
        return 1

    if not isinstance(chunk_output_file_value, str) or not chunk_output_file_value.strip():
        print(f"{FAIL_PREFIX} rag.chunk_output_file 配置无效")
        return 1

    if not isinstance(pilot_files, list):
        print(f"{FAIL_PREFIX} rag.pilot_files 配置无效")
        return 1

    knowledge_base_dir = _resolve_project_path(PROJECT_ROOT, knowledge_base_dir_value)
    chunk_output_file = _resolve_project_path(PROJECT_ROOT, chunk_output_file_value)

    print(f"项目根目录: {PROJECT_ROOT}")
    print(f"配置文件路径: {(PROJECT_ROOT / 'config' / 'config.yaml').resolve()}")
    print(f"RAG 是否启用: {enabled}")
    print(f"知识库目录绝对路径: {knowledge_base_dir}")
    print(f"Chunk 输出文件绝对路径: {chunk_output_file}")

    knowledge_base_exists = knowledge_base_dir.is_dir()
    print(f"知识库目录是否存在: {'是' if knowledge_base_exists else '否'}")

    all_ok = knowledge_base_exists
    expected_pilot_count = 3
    if len(pilot_files) != expected_pilot_count:
        print(f"{FAIL_PREFIX} pilot_files 数量不符合预期: 期望 {expected_pilot_count} 个，实际 {len(pilot_files)} 个")
        all_ok = False

    print("Pilot files 检查结果:")
    for pilot_file in pilot_files:
        pilot_path = knowledge_base_dir / pilot_file
        exists = pilot_path.is_file()
        status = OK_PREFIX if exists else FAIL_PREFIX
        print(f"- {status} {pilot_file}: {pilot_path}")
        all_ok = all_ok and exists

    if all_ok:
        print(f"{OK_PREFIX} RAG 配置检查通过")
        return 0

    print(f"{FAIL_PREFIX} RAG 配置检查未通过")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
