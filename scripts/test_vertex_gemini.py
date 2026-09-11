import asyncio

from google import genai

client = genai.Client(vertexai=True, project="capstone-506616", location="us-central1")

async def test_gen():
    resp = await client.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents="Explain what an aneurysm is in 2 sentences.",
    )
    print("Response from Vertex AI Gemini:")
    print(resp.text)

asyncio.run(test_gen())
