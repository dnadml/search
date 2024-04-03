import asyncio
from collections import deque

from . import client

list_update_lock = asyncio.Lock()
_text_questions_buffer = deque()


async def call_openai(messages, temperature, model, seed=1234, response_format=None):
    for attempt in range(2):
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                seed=seed,
                response_format=response_format,
            )
            response = response.choices[0].message.content
            return response

        except Exception as e:
            await asyncio.sleep(0.5)

    return None
