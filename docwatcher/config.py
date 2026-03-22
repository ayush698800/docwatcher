import json
import os

CONFIG_FILE = '.docwatcher/config.json'

def get_config(repo_path: str) -> dict:
    config_path = os.path.join(repo_path, CONFIG_FILE)
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return json.load(f)
    return {}

def save_config(repo_path: str, config: dict):
    config_path = os.path.join(repo_path, CONFIG_FILE)
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

def is_configured(repo_path: str) -> bool:
    config = get_config(repo_path)
    return 'llm_endpoint' in config

def setup_config(repo_path: str):
    print()
    print("DocWatcher first time setup")
    print("-" * 30)
    print("Enter your local AI endpoint URL")
    print("LM Studio default  : http://localhost:1234/v1/chat/completions")
    print("Ollama default     : http://localhost:11434/v1/chat/completions")
    print()
    
    endpoint = input("Your endpoint URL: ").strip()
    
    if not endpoint:
        endpoint = "http://localhost:1234/v1/chat/completions"
    
    model = input("Model name (leave blank to auto-detect): ").strip()
    
    config = {
        'llm_endpoint': endpoint,
        'model': model if model else 'auto'
    }
    
    save_config(repo_path, config)
    print()
    print("Config saved to .docwatcher/config.json")
    print("Delete that file anytime to reconfigure")
    print()
    
    return config