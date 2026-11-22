import json
import os
from pathlib import Path
from typing import Any


def _config_directory() -> Path:
    """Choose a sensible per-user config directory on Windows and Linux."""
    override = os.environ.get("ASK_CLI_CONFIG_DIR")
    if override:
        return Path(override).expanduser()

    xdg_home = os.environ.get("XDG_CONFIG_HOME")
    if xdg_home:
        return Path(xdg_home).expanduser() / "ask-cli"

    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        return base / "ask-cli"

    return Path.home() / ".config" / "ask-cli"


APP_DIR = _config_directory()
CONFIG_FILE = APP_DIR / "config.json"

DEFAULTS: dict[str, Any] = {
    "default_provider": "openai",
    "openai_model": "gpt-4.1-mini",
    "gemini_model": "gemini-3.8-flash",
    "groq_model": "openai/gpt-oss-20b",
    "openai_api_key": "",
    "gemini_api_key": "",
    "groq_api_key": "",
}


def config_path() -> Path:
    return CONFIG_FILE


def load_config() -> dict[str, Any]:
    """Load saved settings, then let environment variables override API keys."""
    cfg = DEFAULTS.copy()

    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                cfg.update(data)
        except (json.JSONDecodeError, OSError) as exc:
            # Keep defaults usable, but make a damaged config easier to diagnose.
            print(f"Warning: Could not read ASK config ({CONFIG_FILE}): {exc}")

    cfg["openai_api_key"] = os.environ.get("OPENAI_API_KEY") or cfg.get(
        "openai_api_key", ""
    )
    cfg["gemini_api_key"] = (
        os.environ.get("GEMINI_API_KEY")
        or os.environ.get("GOOGLE_API_KEY")
        or cfg.get("gemini_api_key", "")
    )
    cfg["groq_api_key"] = os.environ.get("GROQ_API_KEY") or cfg.get("groq_api_key", "")

    return cfg


def save_config(cfg: dict[str, Any]) -> None:
    """Save settings safely; restrict file permissions where supported."""
    APP_DIR.mkdir(parents=True, exist_ok=True)
    temporary_file = CONFIG_FILE.with_suffix(".tmp")
    temporary_file.write_text(
        json.dumps(cfg, indent=2),
        encoding="utf-8",
    )
    temporary_file.replace(CONFIG_FILE)

    try:
        CONFIG_FILE.chmod(0o600)
    except OSError:
        # Windows may not support POSIX permission bits.
        pass
