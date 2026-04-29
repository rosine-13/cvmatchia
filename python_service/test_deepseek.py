import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("DEEPSEEK_API_KEY")

if not api_key:
    print("❌ Clé API manquante dans .env")
    exit()

url = "https://api.deepseek.com/v1/chat/completions"
headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
payload = {
    "model": "deepseek-chat",
    "messages": [{"role": "user", "content": "Dis bonjour"}],
    "max_tokens": 10
}

try:
    r = requests.post(url, json=payload, headers=headers, timeout=10)
    print("Statut:", r.status_code)
    print("Réponse:", r.json())
except Exception as e:
    print("Erreur:", e)