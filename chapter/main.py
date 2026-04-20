import os
from pathlib import Path
import sys
import tempfile

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
TMP_DIR = BASE_DIR / ".tmp"
TMP_DIR.mkdir(exist_ok=True)
os.environ["TMP"] = str(TMP_DIR)
os.environ["TEMP"] = str(TMP_DIR)
os.environ["TMPDIR"] = str(TMP_DIR)
tempfile.tempdir = str(TMP_DIR)
load_dotenv(BASE_DIR / ".env")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

_original_temp_rmtree = tempfile.TemporaryDirectory._rmtree


def _safe_temp_rmtree(cls, name, ignore_errors=False, repeated=False):
    try:
        return _original_temp_rmtree(name, ignore_errors=ignore_errors, repeated=repeated)
    except PermissionError:
        return None


tempfile.TemporaryDirectory._rmtree = classmethod(_safe_temp_rmtree)

from hello_agents import HelloAgentsLLM, SimpleAgent, ToolRegistry
from hello_agents.tools import MemoryTool, RAGTool


def _disable_dead_local_proxy():
    proxy_keys = [
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "http_proxy",
        "https_proxy",
        "all_proxy",
    ]
    dead_proxy_hosts = ("127.0.0.1:9", "localhost:9")
    removed = []

    for key in proxy_keys:
        value = os.environ.get(key, "").strip()
        if any(host in value for host in dead_proxy_hosts):
            os.environ.pop(key, None)
            removed.append(key)

    if removed:
        print(f"[INFO] Disabled invalid proxy settings: {', '.join(removed)}")


def _mask_secret(value: str | None) -> str:
    if not value:
        return ""
    if len(value) <= 4:
        return "*" * len(value)
    return value[:2] + "*" * (len(value) - 4) + value[-2:]


def _print_connection_debug():
    print("=" * 40)
    print(f"[DEBUG] NEO4J_URI: '{os.environ.get('NEO4J_URI')}'")
    print(f"[DEBUG] NEO4J_USERNAME: '{os.environ.get('NEO4J_USERNAME')}'")
    print(f"[DEBUG] NEO4J_PASSWORD: '{_mask_secret(os.environ.get('NEO4J_PASSWORD'))}'")
    print("=" * 40)


def build_agent() -> SimpleAgent:
    llm = HelloAgentsLLM()
    agent = SimpleAgent(
        name="智能助手",
        llm=llm,
        system_prompt="你是一个有记忆和知识检索能力的 AI 助手。",
    )

    tool_registry = ToolRegistry()
    try:
        memory_tool = MemoryTool(user_id="user123")
    except Exception as exc:
        print(f"[WARN] Full memory backend is unavailable: {exc}")
        print("[WARN] Falling back to working + episodic memory only.")
        memory_tool = MemoryTool(
            user_id="user123",
            memory_types=["working", "episodic"],
        )
    tool_registry.register_tool(memory_tool)
    tool_registry.register_tool(
        RAGTool(knowledge_base_path=str(BASE_DIR / "knowledge_base"))
    )
    agent.tool_registry = tool_registry
    return agent


def main():
    _disable_dead_local_proxy()
    _print_connection_debug()
    agent = build_agent()
    response = agent.run("你好！请记住我叫张三，我是一名 Python 开发者。")
    print(response)


if __name__ == "__main__":
    main()
