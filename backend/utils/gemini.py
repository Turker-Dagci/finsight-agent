from google import genai
from google.genai import types
import os
from dotenv import load_dotenv

load_dotenv()

def get_client():
    return genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def generate(prompt: str, model: str = "gemini-2.5-flash") -> str:
    client = get_client()
    response = client.models.generate_content(
        model=model,
        contents=prompt
    )
    return response.text

def generate_vision(prompt: str, image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
    client = get_client()
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            prompt
        ]
    )
    return response.text

def get_embedding(text: str) -> list:
    client = get_client()
    response = client.models.embed_content(
        model="gemini-embedding-exp-03-07",
        contents=text
    )
    return response.embeddings[0].values

if __name__ == "__main__":
    response = generate("Merhaba, tek cümleyle kendini tanıt.")
    print("Gemini OK:", response[:120])