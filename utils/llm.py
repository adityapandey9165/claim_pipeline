import requests
import json
import re

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = "qwen2.5-coder:3b"   # or mistral


def call_llm(prompt: str) -> dict:
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0}
        },
        timeout=300
    )

    response.raise_for_status()
    text = response.json()["response"].strip()

    # Clean markdown
    if text.startswith("```"):
        parts = text.split("```")
        if len(parts) >= 2:
            text = parts[1]
            if text.startswith("json"):
                text = text[4:]

    text = text.strip()

    # Try parse
    try:
        return json.loads(text)
    except:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))

    raise ValueError(f"Invalid JSON from model: {text[:300]}")