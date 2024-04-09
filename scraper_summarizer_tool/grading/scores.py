# The MIT License (MIT)
# Copyright © 2023 Yuma Rao
# Copyright © 2023 Opentensor Foundation

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
import asyncio
import time
from scraper_summarizer_tool.utils import call_openai


async def get_score_by_openai(messages):
    try:
        start_time = time.time()  # Start timing for query execution
        query_tasks = []
        for message_dict in messages:  # Iterate over each dictionary in the list
            ((key, message_list),) = message_dict.items()

            async def query_openai(message):
                try:
                    return await call_openai(
                        messages=message,
                        temperature=0.2,
                        model="gpt-3.5-turbo-16k",
                    )
                except Exception as e:
                    print(f"Error sending message to OpenAI: {e}")
                    return ""  # Return an empty string to indicate failure

            task = query_openai(message_list)
            query_tasks.append(task)

        query_responses = await asyncio.gather(*query_tasks, return_exceptions=True)

        result = {}
        for response, message_dict in zip(query_responses, messages):
            if isinstance(response, Exception):
                print(f"Query failed with exception: {response}")
                response = (
                    ""  # Replace the exception with an empty string in the result
                )
            ((key, message_list),) = message_dict.items()
            result[key] = response

        execution_time = time.time() - start_time  # Calculate execution time
        print(f"Execution time for OpenAI queries: {execution_time} seconds")
        return result
    except Exception as e:
        print(f"Error processing OpenAI queries: {e}")
        return None
