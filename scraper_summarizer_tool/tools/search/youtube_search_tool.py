import asyncio
from typing import Optional, Type
from langchain.callbacks.manager import CallbackManagerForToolRun
from pydantic import BaseModel, Field
from youtube_search import YoutubeSearch

from scraper_summarizer_tool.tools.base import BaseTool


class YoutubeSearchSchema(BaseModel):
    query: str = Field(
        ...,
        description="The search query for Youtube search.",
    )


class YoutubeSearchTool(BaseTool):
    """Tool for the Youtube API."""

    name = "Youtube Search"

    slug = "youtube-search"

    description = (
        "Useful for when you need to search videos on Youtube"
        "Input should be a search query."
    )

    args_schema: Type[YoutubeSearchSchema] = YoutubeSearchSchema

    tool_id = "8b7b6dad-e550-4a01-be51-aed785eda805"
    max_results = 10

    def _run(
        self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Search YouTube and return the results."""
        result = YoutubeSearch(search_terms=query, max_results=self.max_results)
        return result.videos

    async def send_event(self, send, response_streamer, data):
        pass


async def main():  # Define an asynchronous function to await the execution
    tool = YoutubeSearchTool()
    result = tool._run("Python Frameworks")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
