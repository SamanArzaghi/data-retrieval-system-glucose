import asyncio
from openai import AsyncOpenAI
from config import API_KEY
import json

async def openai_async_wrapper(
    model_name: str = "gpt-4o",
    sys_prompt: str = "",
    user_prompt: str = "",
    temp: float = 0,
    max_token: int = 2000,
    output: str = "text",
    user_client: AsyncOpenAI = None
):

    if user_client is None:
        aclient = AsyncOpenAI(api_key=API_KEY,)
    else:
        aclient = user_client

    if output == "text":
        chat_completion = await aclient.chat.completions.create(
            temperature=temp,
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": str(sys_prompt),
                },
                {
                    "role": "user",
                    "content": str(user_prompt),
                }
            ],
        )
        chat_completion = chat_completion.choices[0].message.content


    elif output == "json":
        chat_completion = await aclient.chat.completions.create(
            temperature=temp,
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": str(sys_prompt),
                },
                {
                    "role": "user",
                    "content": str(user_prompt),
                }
            ],
            response_format={ "type":"json_object"}
        )

        chat_completion = chat_completion.choices[0].message.content
        chat_completion = json.loads(chat_completion)

    return chat_completion