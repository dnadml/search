import asyncio
import json
from typing import Type
from pydantic import BaseModel, Field
from starlette.types import Send
from scraper_summarizer_tool.tools.base import BaseTool
from scraper_summarizer_tool.services.twitter_prompt_analyzer import TwitterPromptAnalyzer
import logging


class GetRecentTweetsToolSchema(BaseModel):
    query: str = Field(
        ...,
        description="The search query for tweets.",
    )


class GetRecentTweetsTool(BaseTool):
    """Tool that gets recent tweets from Twitter."""

    name = "Recent Tweets"

    slug = "get_recent_tweets"

    description = "Get recent tweets for a given query."

    args_schema: Type[GetRecentTweetsToolSchema] = GetRecentTweetsToolSchema

    tool_id = "6e57b718-8953-448b-98db-fd19c1d1469c"

    def _run(self):
        pass

    async def _arun(
        self,
        query: str,  # run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Tweet message and return."""
        openai_query_model = "gpt-3.5-turbo-0125"
        openai_fix_query_model = "gpt-4-1106-preview"

        client = TwitterPromptAnalyzer(
            openai_query_model=openai_query_model,
            openai_fix_query_model=openai_fix_query_model,
        )

        result, prompt_analysis = await client.analyse_prompt_and_fetch_tweets(
            query, is_recent_tweets=True
        )

        logging.info(
            "================================== Prompt analysis ==================================="
        )
        logging.info(prompt_analysis)
        logging.info(
            "================================== Prompt analysis ===================================="
        )

        if self.tool_manager:
            self.tool_manager.twitter_data = result
            self.tool_manager.twitter_prompt_analysis = prompt_analysis

        return (result, prompt_analysis)

    async def send_event(self, send: Send, response_streamer, data):
        if not data:
            return

        tweets, prompt_analysis = data

        # Send prompt_analysis
        if prompt_analysis:
            prompt_analysis_response_body = {
                "type": "prompt_analysis",
                "content": prompt_analysis.dict(),
            }

            await send(
                {
                    "type": "http.response.body",
                    "body": json.dumps(prompt_analysis_response_body).encode("utf-8"),
                    "more_body": True,
                }
            )
            logging.info("Prompt Analysis sent")

        if tweets:
            tweets_amount = tweets.get("meta", {}).get("result_count", 0)

            tweets_response_body = {"type": "tweets", "content": tweets}
            response_streamer.more_body = False

            await send(
                {
                    "type": "http.response.body",
                    "body": json.dumps(tweets_response_body).encode("utf-8"),
                    "more_body": False,
                }
            )
            logging.info(f"Tweet data sent. Number of tweets: {tweets_amount}")


async def main():  # Define an asynchronous function to await the execution
    tool = GetRecentTweetsTool()
    result = await tool._arun("Donald Trump")  # Await the _arun method
    print(result)

if __name__ == "__main__":
    asyncio.run(main())