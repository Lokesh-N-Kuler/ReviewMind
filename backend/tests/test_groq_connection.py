from pathlib import Path
from dotenv import dotenv_values
from groq import Groq

env = dotenv_values(Path(__file__).resolve().parent.parent / ".env")

api_key = env.get("GROQ_API_KEY")
model = env.get("GROQ_MODEL", "llama-3.3-70b-versatile")

if not api_key or "your_" in api_key.lower():
    raise SystemExit("FAIL: Add your real GROQ_API_KEY to backend/.env")

client = Groq(api_key=api_key)

response = client.chat.completions.create(
    model=model,
    messages=[
        {
            "role": "system",
            "content": "You are a code security reviewer."
        },
        {
            "role": "user",
            "content": "Explain this Python vulnerability in one sentence: query = 'SELECT * FROM users WHERE name=' + username"
        }
    ],
    temperature=0.2,
    max_completion_tokens=200
)

print("\nGROQ CONNECTION SUCCESSFUL")
print("Model:", response.model)
print("AI response:")
print(response.choices[0].message.content)

client.close()
