import os
import logging
logging.basicConfig(level=logging.INFO)

from dotenv import load_dotenv, dotenv_values
load_dotenv()

from openai import AsyncOpenAI

AsyncOpenAI.api_key = os.environ.get("OPENAI_API_KEY")
if not AsyncOpenAI.api_key:
    raise ValueError("Please set the OPENAI_API_KEY environment variable.")

client = AsyncOpenAI(timeout=90.0)

# Blacklist variables
ALLOW_NON_REGISTERED = False
PROMPT_BLACKLIST_STAKE = 20000
TWITTER_SCRAPPER_BLACKLIST_STAKE = 20000
ISALIVE_BLACKLIST_STAKE = min(PROMPT_BLACKLIST_STAKE, TWITTER_SCRAPPER_BLACKLIST_STAKE)
MIN_REQUEST_PERIOD = 2
MAX_REQUESTS = 30

ENTITY = "vocable-ai-research-scrape"
PROJECT_NAME = "vocable-ai-research"
