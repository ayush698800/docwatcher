import json
import os

CONFIG_DIR = ".docdrift"
LEGACY_CONFIG_DIR = ".docwatcher"
CONFIG_FILE = "config.json"


def _config_path(repo_path: str, config_dir: str) -> str:
    return os.path.join(repo_path, config_dir, CONFIG_FILE)


def get_config(repo_path: str) -> dict:
    for config_dir in (CONFIG_DIR, LEGACY_CONFIG_DIR):
        config_path = _config_path(repo_path, config_dir)
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as handle:
                return json.load(handle)
    return {}


def save_config(repo_path: str, config: dict):
    config_path = _config_path(repo_path, CONFIG_DIR)
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as handle:
        json.dump(config, handle, indent=2)


def is_configured(repo_path: str) -> bool:
    config = get_config(repo_path)
    return "llm_endpoint" in config


def setup_config(repo_path: str):
    print()
    print("DocDrift first-time setup")
    print("-" * 27)
    print("Enter your AI endpoint URL.")
    print("LM Studio default: http://localhost:1234/v1/chat/completions")
    print("Ollama default   : http://localhost:11434/v1/chat/completions")
    print()

    endpoint = input("Endpoint URL: ").strip() or "http://localhost:1234/v1/chat/completions"
    model = input("Model name (leave blank to auto-detect): ").strip()

    config = {
        "llm_endpoint": endpoint,
        "model": model if model else "auto",
    }
    save_config(repo_path, config)

    print()
    print("Saved config to .docdrift/config.json")
    print("Delete that file any time to reconfigure.")
    print()
    return config
