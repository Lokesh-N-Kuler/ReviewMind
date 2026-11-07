from pathlib import Path
from dotenv import dotenv_values
from groq import Groq

env = dotenv_values(Path(__file__).resolve().parent.parent / ".env")
key = env.get("GROQ_API_KEY")

if not key or "your_" in key.lower():
    raise SystemExit("GROQ_API_KEY is missing or still a placeholder")

client = Groq(api_key=key)

print("\nAVAILABLE GROQ MODELS:\n")
for model in client.models.list().data:
    if getattr(model, "active", True):
        print(model.id)

client.close()
