import asyncio
import re
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


def clean_text(self, text):
    # Remove newline characters and replace with a space
    text = text.replace("\n", " ")

    # Remove URLs
    text = re.sub(
        r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
        "",
        text,
    )
    # Keep hashtags, alphanumeric characters, and spaces
    # Remove other special characters but ensure to keep structured elements like <Question>, <Answer>, etc., intact
    text = re.sub(r"(?<![\w<>#])[^\w\s#<>]+", "", text)

    return text
