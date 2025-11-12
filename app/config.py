import json
from pathlib import Path


config_path = Path(__file__).parent.parent / "config.json"

if not config_path.exists():
    raise FileNotFoundError(f"Файл конфигурации не найден: {config_path}")

with open(config_path, encoding="utf-8") as f:
    _config = json.load(f)

OPENAI_API_KEY = _config.get("openai_api_key")

if not OPENAI_API_KEY:
    raise ValueError("OpenAI API ключ не найден в config.json")
