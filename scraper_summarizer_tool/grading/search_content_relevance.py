import logging
from typing import List
from .config import RewardModelType, RewardScoringType
from scraper_summarizer_tool.protocol import ScraperStreamingSynapse, ScraperTextRole
import traceback
import re
import asyncio
from scraper_summarizer_tool.grading.prompts import (
    SearchSummaryRelevancePrompt,
    extract_score_and_explanation,
)
import random
import json
from scraper_summarizer_tool.grading.prompts import ScoringPrompt, SearchSummaryRelevancePrompt
import time

from .scores import get_score_by_openai


class WebSearchContentRelevanceModel:
    reward_model_name: str = "VMware/open-llama-7b-open-instruct"

    @property
    def name(self) -> str:
        return RewardModelType.search_summary_relevance_match.value

    def __init__(self, scoring_type: None):
        super().__init__()
        self.scoring_type = scoring_type

    async def llm_process_validator_links(self, prompt, links_with_metadata):
        scoring_messages = []

        for link_with_metadata in links_with_metadata:
            url = link_with_metadata.get("url")
            title = link_with_metadata.get("title")
            description = link_with_metadata.get("description")
            content = f"Page Title: {title}. Page Description: {description}"

            result = self.get_scoring_text(
                prompt=prompt, content=content, response=None
            )
            if result:
                scoring_prompt, scoring_text = result
                scoring_messages.append({url: scoring_text})

        score_responses = asyncio.run(get_score_by_openai(scoring_messages))
        return score_responses

    async def process_links(
            self, prompt: str, responses: List[ScraperStreamingSynapse]
    ):
        all_links = []
        start_time = time.time()

        for response in responses:
            links = [
                link
                for link in random.sample(
                    response.search_completion_links,
                    min(3, len(response.search_completion_links)),
                )
            ]

            all_links.extend(links)

        unique_links = list(set(all_links))

        if len(unique_links) == 0:
            logging.info("No unique links found to process.")
            return {}

        links_with_metadata = await WebScraperActor().scrape_metadata(urls=unique_links)

        for response in responses:
            for link_with_metadata in links_with_metadata:
                url = link_with_metadata.get("url")

                if url in response.search_completion_links:
                    response.validator_links.append(link_with_metadata)

        val_score_responses = await self.llm_process_validator_links(
            prompt, links_with_metadata
        )

        end_time = time.time()
        logging.info(
            f"Fetched Web links method took {end_time - start_time} seconds. "
            f"All links count: {len(all_links)}, Unique links count: {len(unique_links)}, "
            f"APIFY fetched web links count: {len(links_with_metadata)}"
        )
        fetched_links = {link.get("url") for link in links_with_metadata}
        non_fetched_links = [link for link in unique_links if link not in fetched_links]

        logging.info(
            f"Web links not fetched amount: {len(non_fetched_links)}; List: {non_fetched_links}; For prompt: [{prompt}]"
        )
        if len(non_fetched_links):
            logging.info(
                f"Unique Web Links Amount: {len(unique_links)}; List: {unique_links};"
            )

        return val_score_responses

    def check_response_random_link(self, response: ScraperStreamingSynapse):
        try:
            link_score = 0

            completion = self.get_successful_search_summary_completion(
                response=response
            )

            if not completion:
                return 0

            search_completion_links = response.search_completion_links
            search_results = response.search_results
            validator_links = response.validator_links

            if not search_completion_links or not search_results or not validator_links:
                return 0

            if len(search_completion_links) < 2:
                # at least miners should provide two search links
                return 0

            random_link = random.choice(validator_links)

            if random_link["url"] in str(search_results):
                link_score = 1

            return link_score
        except Exception as e:
            logging.error(f"check_response_random_link: {str(e)}")
            return 0

    def get_scoring_text(
            self, prompt: str, content: str, response: ScraperStreamingSynapse
    ):
        try:
            if response:
                completion = self.get_successful_search_summary_completion(
                    response=response
                )

                if not completion:
                    return None

            if content is None:
                logging.debug("Search Content is empty.")
                return None

            scoring_prompt_text = None
            scoring_prompt = SearchSummaryRelevancePrompt()

            if not scoring_prompt_text:
                scoring_prompt_text = scoring_prompt.text(prompt, content)

            return scoring_prompt, [
                {"role": "system", "content": scoring_prompt.get_system_message()},
                {"role": "user", "content": scoring_prompt_text},
            ]
        except Exception as e:
            logging.error(f"Error in Prompt reward method: {str(e)}")
            return None

    def get_rewards(
            self, prompt: str, responses: List[ScraperStreamingSynapse]
    ):
        try:
            completions = [
                response.completion.strip() for response in responses if response.completion is not None
            ]
            logging.debug(
                f"WebSearchContentRelevanceModel | Calculating {len(completions)} rewards (typically < 1 sec/reward)."
            )
            logging.trace(
                f"WebSearchContentRelevanceModel | prompt: {repr(prompt[:50])} ... {repr(prompt[-50:])}"
            )
            val_score_responses = asyncio.run(
                self.process_links(prompt=prompt, responses=responses)
            )

            logging.info(
                f"WebSearchContentRelevanceModel | Keys in val_score_responses: {len(val_score_responses.keys()) if val_score_responses else 'No val_score_responses available'}"
            )
            scores = [
                self.check_response_random_link(response) for response in responses
            ]

            reward_events = []
            scoring_prompt = ScoringPrompt()

            grouped_val_score_responses = []

            for apify_score, response, uid_tensor in zip(scores, responses, uids):
                response_scores = {}
                total_score = 0
                num_links = len(response.validator_links)

                if num_links > 0:
                    for val_link in response.validator_links:
                        val_url = val_link.get("url")
                        if val_score_responses:
                            score_result = val_score_responses.get(val_url, None)
                            if score_result is not None:
                                score = scoring_prompt.extract_score(score_result)
                                total_score += (
                                        score / 10.0
                                )  # Adjust score scaling as needed
                                response_scores[val_url] = score

                    if total_score > 0:
                        average_score = total_score / num_links
                grouped_val_score_responses.append(response_scores)
            return scores
        except Exception as e:
            error_message = f"Search Summary Relevance get_rewards: {str(e)}"
            tb_str = traceback.format_exception(type(e), e, e.__traceback__)
            logging.error("\n".join(tb_str) + error_message)
