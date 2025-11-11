"""
Конфигурация приложения.
"""
import json
from pathlib import Path


def load_config():
    """Загрузка конфигурации из config.json файла."""
    config_path = Path(__file__).parent.parent / "config.json"

    if not config_path.exists():
        raise FileNotFoundError(
            f"Файл конфигурации не найден: {config_path}. "
            "Создайте config.json на основе config.json.example",
        )

    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    return config


# Загрузка конфигурации
_config = load_config()

# OpenAI API ключ
OPENAI_API_KEY = _config.get("openai_api_key")

if not OPENAI_API_KEY:
    raise ValueError("OpenAI API ключ не найден в config.json")

# Валидация формата ключа
if not OPENAI_API_KEY.startswith("sk-proj-"):
    raise ValueError("Неверный формат OpenAI API ключа")
