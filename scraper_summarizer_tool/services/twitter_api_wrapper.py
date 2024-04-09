import aiohttp
import os
from scraper_summarizer_tool.services.twitter_utils import TwitterUtils

BEARER_TOKEN = os.environ.get("TWITTER_BEARER_TOKEN")

VALID_DOMAINS = ["twitter.com", "x.com"]


class TwitterAPIClient:
    def __init__(
        self,
        openai_query_model="gpt-3.5-turbo-0125",
        openai_fix_query_model="gpt-4-1106-preview",
    ):
        self.bearer_token = BEARER_TOKEN
        self.utils = TwitterUtils()
        self.openai_query_model = openai_query_model
        self.openai_fix_query_model = openai_fix_query_model

    async def bearer_oauth(self, session: aiohttp.ClientSession):
        session.headers["Authorization"] = f"Bearer {self.bearer_token}"
        session.headers["User-Agent"] = "v2RecentSearchPython"

    async def connect_to_endpoint(self, url, params):
        async with aiohttp.ClientSession() as session:
            await self.bearer_oauth(session)
            async with session.get(url, params=params) as response:
                if response.status in [401, 403]:
                    print(
                        f"Critical Twitter API Request error occurred: {await response.text()}"
                    )
                    os._exit(1)

                json_data = None

                try:
                    json_data = await response.json()
                except aiohttp.ContentTypeError:
                    pass

                response_text = await response.text()
                return json_data, response.status, response_text

    async def get_tweet_by_id(self, tweet_id):
        tweet_url = f"https://api.twitter.com/2/tweets/{tweet_id}"
        response_json, status_code = await self.connect_to_endpoint(tweet_url, {})
        return response_json

    async def get_tweets_by_ids(self, tweet_ids):
        ids = ",".join(tweet_ids)  # Combine all tweet IDs into a comma-separated string
        tweets_url = f"https://api.twitter.com/2/tweets?ids={ids}"
        response_json, status_code = await self.connect_to_endpoint(tweets_url, {})
        if status_code != 200:
            return []
        return response_json

    async def get_recent_tweets(self, query_params):
        search_url = "https://api.twitter.com/2/tweets/search/recent"
        return await self.connect_to_endpoint(search_url, query_params)

    async def get_full_archive_tweets(self, query_params):
        search_url = "https://api.twitter.com/2/tweets/search/all"
        return await self.connect_to_endpoint(search_url, query_params)
