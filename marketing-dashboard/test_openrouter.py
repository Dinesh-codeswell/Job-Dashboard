"""Test OpenRouter API: see what the free model actually returns."""
import requests, os, json
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path("..") / ".env")
load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")
model = os.getenv("OPENROUTER_MODEL", "google/gemma-4-31b-it:free")

print(f"=== Testing model: {model} ===")
print(f"API key present: {bool(api_key)}")

user_content = """John Doe
555-0100 | john@email.com | linkedin.com/in/johndoe | github.com/johndoe

EDUCATION
University of Tech, Boston, MA
BS Computer Science, 2018-2022

EXPERIENCE
Software Engineer, TechCorp, San Francisco, CA
June 2022 - Present
- Built REST APIs with Python/Flask
- Designed React dashboards

SKILLS
Python, JavaScript, React, Flask, Docker, Git"""

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://roleboard.app",
    "X-OpenRouter-Title": "Test",
}

payload = {
    "model": model,
    "messages": [
        {"role": "user", "content": "Convert this resume to LaTeX. Output ONLY the latex code in a ```latex ... ``` block. Keep it simple:\n\n" + user_content},
    ],
    "temperature": 0.3,
    "max_tokens": 2048,
}

try:
    resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=120)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        print("\n=== RAW RESPONSE (repr) ===")
        print(repr(content[:3000]))
        print("\n=== FIRST 200 CHARS ===")
        print(content[:200])
        print("\n=== Has 'begin{document}':", "begin{document}" in content)
        print("=== Has '```latex':", "```latex" in content)
        print("=== Has '```':", "```" in content)
        print("=== Total length:", len(content), "chars ===")
    else:
        print(f"Error body: {resp.text[:1000]}")
except Exception as e:
    print(f"Exception: {e}")
