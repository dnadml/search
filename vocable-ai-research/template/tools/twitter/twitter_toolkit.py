import asyncio
from abc import ABC
from typing import List
from template.tools.base import BaseToolkit, BaseTool
from template.tools.twitter.get_recent_tweets_tool import GetRecentTweetsTool
from template.tools.twitter.get_full_archive_tweets_tool import GetFullArchiveTweetsTool
from template.tools.twitter.twitter_summary import summarize_twitter_data, prepare_tweets_data_for_summary


class TwitterToolkit(BaseToolkit, ABC):
    name: str = "Twitter Toolkit"
    description: str = "Toolkit containing tools for retrieving tweets."
    slug: str = "twitter"
    toolkit_id: str = "0e0ae6fb-0f1c-4d00-bc84-1feb2a6824c6"

    def get_tools(self) -> List[BaseTool]:
        return [GetRecentTweetsTool(), GetFullArchiveTweetsTool()]

    async def summarize(self, prompt, model, data):
        tweets, prompt_analysis = data

        return await summarize_twitter_data(
            prompt=prompt,
            model=model,
            filtered_tweets=prepare_tweets_data_for_summary(tweets),
            prompt_analysis=prompt_analysis,
        )
