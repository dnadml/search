from typing import Optional, Type
import asyncio
from langchain.callbacks.manager import CallbackManagerForToolRun
from pydantic import BaseModel, Field

from scraper_summarizer_tool.tools.search.wikipedia_api_wrapper import WikipediaAPIWrapper
from scraper_summarizer_tool.tools.base import BaseTool


class WikipediaSearchSchema(BaseModel):
    query: str = Field(
        ...,
        description="The search query for Wikipedia search.",
    )


class WikipediaSearchTool(BaseTool):
    """Tool for the Wikipedia API."""

    name = "Wikipedia Search"

    slug = "wikipedia-search"

    description = (
        "A wrapper around Wikipedia. "
        "Useful for when you need to answer general questions about "
        "people, places, companies, facts, historical events, or other subjects. "
        "Input should be a search query."
    )

    args_schema: Type[WikipediaSearchSchema] = WikipediaSearchSchema

    tool_id = "eb161647-b858-4863-801f-ba7d2e380601"

    def _run(
            self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Search Wikipedia and return the results."""
        wikipedia = WikipediaAPIWrapper()
        return wikipedia.run(query)

    async def send_event(self, send, response_streamer, data):
        pass


async def main():  # Define an asynchronous function to await the execution
    tool = WikipediaSearchTool()
    result = tool._run("Python Frameworks")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
