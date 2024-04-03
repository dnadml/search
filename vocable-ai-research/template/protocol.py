import json
from abc import ABC, abstractmethod
from typing import List, Union, Callable, Awaitable, Dict, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class TwitterPromptAnalysisResult(BaseModel):
    api_params: Dict[str, Any] = {}
    keywords: List[str] = []
    hashtags: List[str] = []
    user_mentions: List[str] = []

    def fill(self, response: Dict[str, Any]):
        if "api_params" in response:
            self.api_params = response["api_params"]
        if "keywords" in response:
            self.keywords = response["keywords"]
        if "hashtags" in response:
            self.hashtags = response["hashtags"]
        if "user_mentions" in response:
            self.user_mentions = response["user_mentions"]

    def __str__(self):
        return f"Query String: {self.api_params}, Keywords: {self.keywords}, Hashtags: {self.hashtags}, User Mentions: {self.user_mentions}"


class TwitterScraperMedia(BaseModel):
    media_url: str = ""
    type: str = ""


class TwitterScraperUser(BaseModel):
    id: Optional[str] = ""
    url: Optional[str] = ""
    username: Optional[str] = ""
    description: Optional[str] = ""
    created_at: Optional[str] = ""
    favourites_count: Optional[int] = 0
    followers_count: Optional[int] = 0
    listed_count: Optional[int] = 0
    media_count: Optional[int] = 0
    name: Optional[str] = ""
    profile_image_url: Optional[str] = ""
    statuses_count: Optional[int] = 0
    verified: Optional[bool] = False


class TwitterScraperTweet(BaseModel):
    user: Optional[TwitterScraperUser] = TwitterScraperUser()
    id: Optional[str] = ""
    full_text: Optional[str] = ""
    reply_count: Optional[int] = 0
    retweet_count: Optional[int] = 0
    like_count: Optional[int] = 0
    view_count: Optional[int] = 0
    quote_count: Optional[int] = 0
    url: Optional[str] = ""
    created_at: Optional[str] = ""
    is_quote_tweet: Optional[bool] = False
    is_retweet: Optional[bool] = False
    media: Optional[List[TwitterScraperMedia]] = []


class ScraperTextRole(str, Enum):
    INTRO = "intro"
    TWITTER_SUMMARY = "twitter_summary"
    SEARCH_SUMMARY = "search_summary"
    FINAL_SUMMARY = "summary"


def extract_json_chunk(chunk, response, buffer=""):
    """
    Extracts JSON objects from a chunk of data, handling cases where JSON objects are split across multiple chunks.

    :param chunk: The current chunk of data to process.
    :param response: The response object, used for logging.
    :param buffer: A buffer holding incomplete JSON data from previous chunks.
    :return: A tuple containing a list of extracted JSON objects and the updated buffer.
    """
    buffer += chunk  # Add the current chunk to the buffer
    json_objects = []
    start_index = None  # Initialize start_index for JSON object extraction

    i = 0  # Start index for scanning the buffer
    while i < len(buffer):
        if buffer[i] == "{":
            if start_index is None:  # Start of a new JSON object
                start_index = i
            stack = 1  # Initialize stack to keep track of braces
            i += 1
            while i < len(buffer) and stack > 0:
                if buffer[i] == "{":
                    stack += 1
                elif buffer[i] == "}":
                    stack -= 1
                i += 1
            if stack == 0:  # Found a complete JSON object
                json_str = buffer[start_index:i]
                try:
                    json_obj = json.loads(json_str)
                    json_objects.append(json_obj)
                    start_index = None  # Reset start_index for the next JSON object
                except json.JSONDecodeError as e:
                    port = response.real_url.port
                    host = response.real_url.host
        else:
            i += 1  # Move to the next character if not the start of a JSON object

    remaining_buffer = (
        buffer[start_index:] if start_index is not None else ""
    )  # Remaining buffer after extracting JSON objects

    return json_objects, remaining_buffer
