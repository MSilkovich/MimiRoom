import os

from openai import OpenAI

from src.schemas.llm import LLMResponse


class OpenaiClient:
    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        *,
        temperature: float | None = None,
    ) -> LLMResponse:
        ...


# api_key = "NDE2OTgyOWEtNTAxOS00MzA3LWEzYmItZWI3YjM4MWM5Mjk5.0dde5178ad34a0d2fc8ef186a0388eb3"
# url = "https://foundation-models.api.cloud.ru/v1"

# client = OpenAI(
#     api_key=api_key,
#     base_url=url
# )

# response = client.chat.completions.create(
#     model="ai-sage/GigaChat3-10B-A1.8B",
#     max_tokens=2500,
#     temperature=0.5,
#     presence_penalty=0,
#     top_p=0.95,
#     messages=[
#         {
#             "role": "user",
#             "content": "Как написать хороший код?"
#         }
#     ]
# )

# print(response.choices[0].message.content)
