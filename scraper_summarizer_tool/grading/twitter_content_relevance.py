import traceback
import logging
import time
import asyncio
from typing import List
from scraper_summarizer_tool.grading.config import RewardModelType, RewardScoringType
from scraper_summarizer_tool.grading.prompts import (
    LinkContentPrompt,
    ScoringPrompt
)
from scraper_summarizer_tool.protocol import (
    ScraperStreamingSynapse,
)
from scraper_summarizer_tool.services.twitter_api_wrapper import TwitterAPIClient
from scraper_summarizer_tool.grading.scores import get_score_by_openai


class TwitterContentRelevanceModel:
    reward_model_name: str = "VMware/open-llama-7b-open-instruct"
    scoring_type = RewardScoringType.summary_relevance_score_template
    tw_client = TwitterAPIClient()

    @property
    def name(self) -> str:
        return RewardModelType.link_content_match.value


    async def process_tweets(self, prompt, responses):
        try:
            all_links = []
            links_with_metadata = {}
            start_time = time.time()
            for response in responses:
                links = []
                for link in response.completion_links:
                    links.append(link)
                    links_with_metadata[link] = str(response.completion_links_metadata[link])
                all_links.extend(links)

            unique_links = list(set(all_links))

            if len(unique_links) == 0:
                logging.info("No unique links found to process.")
                return {}

            start_llm_time = time.time()
            scoring_messages = []
            for url, link_with_metadata in links_with_metadata.items():
                result = self.get_scoring_text(
                    prompt=prompt, content=link_with_metadata
                )
                if result:
                    scoring_prompt, scoring_text = result
                    scoring_messages.append({str(url): scoring_text})
            val_score_responses = await get_score_by_openai(scoring_messages)

            end_llm_time = time.time()
            llm_duration_minutes = (end_llm_time - start_llm_time) / 60
            logging.info(
                f"TwitterContentRelevanceModel LLM process validator tweets took {llm_duration_minutes} minutes."
            )

            end_time = time.time()
            logging.info(
                f"Fetched Twitter links method took {end_time - start_time} seconds. "
            )
            return val_score_responses
        except Exception as e:
            logging.error(f"Error in process_tweets: {str(e)}")
            return {}

    def get_scoring_text(
        self, prompt: str, content: str
    ):
        try:
            scoring_prompt = LinkContentPrompt()
            if content is None:
                logging.debug("Twitter Content is empty")
                return None

            scoring_prompt_text = scoring_prompt.text(prompt, content)

            return scoring_prompt, [
                {"role": "system", "content": scoring_prompt.get_system_message()},
                {"role": "user", "content": scoring_prompt_text},
            ]
        except Exception as e:
            error_message = f"Error in Prompt reward method: {str(e)}"
            tb_str = traceback.format_exception(type(e), e, e.__traceback__)
            logging.warning("\n".join(tb_str) + error_message)
            return None

    def get_scores(
        self, prompt: str, responses: List[ScraperStreamingSynapse],
    ):
        try:
            completions = [
                response.get_twitter_completion().strip() for response in responses
            ]
            logging.debug(
                f"TwitterContentRelevanceModel | Calculating {len(completions)} rewards (typically < 1 sec/reward)."
            )
            logging.info(
                f"TwitterContentRelevanceModel | prompt: {repr(prompt[:50])} ... {repr(prompt[-50:])}"
            )

            val_score_responses = asyncio.run(
                self.process_tweets(prompt=prompt, responses=responses)
            )
            logging.info(f"TwitterContentRelevanceModel | PROMPT: {prompt}")
            logging.info(
                f"TwitterContentRelevanceModel | Keys in val_score_responses: {len(val_score_responses.keys()) if val_score_responses else 'No val_score_responses available'}"
            )

            scoring_prompt = ScoringPrompt()
            grouped_val_score_responses = []

            for response in responses:
                score_result = None
                response_scores = {}
                total_score = 0
                if len(response.completion_links):
                    for val_tweet in response.completion_links:
                        if val_score_responses:
                            score_result = val_score_responses.get(val_tweet, None)
                            if score_result is not None:
                                score = scoring_prompt.extract_score(score_result)
                                total_score += score
                                response_scores[val_tweet] = {}
                                response_scores[val_tweet]['value'] = score_result
                                response_scores[val_tweet]['score'] = score
                    if total_score > 0:
                        response_scores['average_score'] = round(total_score / len(val_score_responses), 2)
                        response_scores['count'] = len(val_score_responses)
                grouped_val_score_responses.append(response_scores)
            return grouped_val_score_responses
        except Exception as e:
            error_message = f"Link Content Relevance get_scores: {str(e)}"
            tb_str = traceback.format_exception(type(e), e, e.__traceback__)
            logging.error("\n".join(tb_str) + error_message)