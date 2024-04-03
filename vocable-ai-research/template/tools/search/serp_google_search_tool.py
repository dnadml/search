import os
import json
import logging
import asyncio  # Import asyncio module to use async features
from typing import Type
from pydantic import BaseModel, Field
from template.tools.base import BaseTool
from starlette.types import Send
from template.tools.search.serp_api_wrapper import SerpAPIWrapper


SERPAPI_API_KEY = os.environ.get("SERPAPI_API_KEY")

if not SERPAPI_API_KEY:
    raise ValueError(
        "Please set the SERPAPI_API_KEY environment variable. See here: https://github.com/surcyf123/smart-scrape/blob/main/docs/env_variables.md"
    )


class SerpGoogleSearchSchema(BaseModel):
    query: str = Field(
        ...,
        description="The search query for Google search.",
    )


class SerpGoogleSearchTool(BaseTool):
    name = "Web Search"

    slug = "serp_google_search"

    description = (
        "This tool performs Google searches and extracts relevant snippets and webpages. "
        "It's particularly useful for staying updated with current events and finding quick answers to your queries."
    )

    args_schema: Type[SerpGoogleSearchSchema] = SerpGoogleSearchSchema

    tool_id = "a66b3b20-d0a2-4b53-a775-197bc492e816"

    def _run(self):
        pass

    async def _arun(
        self,
        query: str,
    ):
        """Search Google and return the results."""

        search = SerpAPIWrapper(serpapi_api_key=SERPAPI_API_KEY)

        try:
            return await search.arun(query)
        except Exception as err:
            if "Invalid API key" in str(err):
                return "Serp API Key is invalid"

            return "Could not search Google. Please try again later."

    async def send_event(self, send: Send, response_streamer, data):
        if not data:
            return

        search_results_response_body = {
            "type": "search",
            "content": data,
        }

        response_streamer.more_body = False

        await send(
            {
                "type": "http.response.body",
                "body": json.dumps(search_results_response_body).encode("utf-8"),
                "more_body": False,
            }
        )

        logging.info("Web search results data sent")


async def main():  # Define an asynchronous function to await the execution
    tool = SerpGoogleSearchTool()
    result = await tool._arun("Best Web Python Frameworks")  # Await the _arun method
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
