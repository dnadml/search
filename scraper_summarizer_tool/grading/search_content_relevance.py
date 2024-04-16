import logging
from typing import List
from scraper_summarizer_tool.grading.config import RewardModelType
from scraper_summarizer_tool.protocol import ScraperStreamingSynapse, ScraperTextRole
import traceback
import asyncio
import random
from scraper_summarizer_tool.grading.prompts import ScoringPrompt, SearchSummaryRelevancePrompt
import time
from scraper_summarizer_tool.grading.scores import get_score_by_openai


class WebSearchContentRelevanceModel:
    reward_model_name: str = "VMware/open-llama-7b-open-instruct"

    @property
    def name(self) -> str:
        return RewardModelType.search_summary_relevance_match.value

    async def process_links(
            self, prompt: str, responses: List[ScraperStreamingSynapse]
    ):
        all_links = []
        links_with_metadata = {}
        start_time = time.time()

        for response in responses:
            links = []
            for link in response.search_completion_links:
                links.append(link)
                links_with_metadata[link] = str(response.search_completion_links_metadata[link])

            all_links.extend(links)

        unique_links = list(set(all_links))

        if len(unique_links) == 0:
            logging.info("No unique links found to process.")
            return {}

        scoring_messages = []
        for url, link_with_metadata in links_with_metadata.items():
            result = self.get_scoring_text(
                prompt=prompt, content=link_with_metadata
            )
            if result:
                scoring_prompt, scoring_text = result
                scoring_messages.append({url: scoring_text})

        val_score_responses = await get_score_by_openai(scoring_messages)

        end_time = time.time()
        logging.info(
            f"Fetched Web links method took {end_time - start_time} seconds. "
        )

        return val_score_responses

    def get_scoring_text(
            self, prompt: str, content: str
    ):
        try:
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

    def get_scores(
            self, prompt: str, responses: List[ScraperStreamingSynapse]
    ):
        try:
            # Search Summary
            completions = [
                response.get_search_summary_completion().strip() for response in responses
            ]
            logging.debug(
                f"WebSearchContentRelevanceModel | Calculating {len(completions)} rewards (typically < 1 sec/reward)."
            )
            logging.info(
                f"WebSearchContentRelevanceModel | prompt: {repr(prompt[:50])} ... {repr(prompt[-50:])}"
            )
            val_score_responses = asyncio.run(
                self.process_links(prompt=prompt, responses=responses)
            )

            logging.info(
                f"WebSearchContentRelevanceModel | Keys in val_score_responses: {len(val_score_responses.keys()) if val_score_responses else 'No val_score_responses available'}"
            )
            scoring_prompt = ScoringPrompt()
            grouped_val_score_responses = []

            for response in responses:
                response_scores = {}
                total_score = 0
                num_links = len(response.search_completion_links)

                if num_links > 0:
                    for val_url in response.search_completion_links:
                        if val_score_responses:
                            score_result = val_score_responses.get(val_url, None)
                            if score_result is not None:
                                score = scoring_prompt.extract_score(score_result)
                                total_score += (
                                        score / 10.0
                                )  # Adjust score scaling as needed
                                response_scores[val_url] = {}
                                response_scores[val_url]['value'] = score_result
                                response_scores[val_url]['score'] = score
                    if total_score > 0:
                        average_score = total_score / num_links
                grouped_val_score_responses.append(response_scores)
            return grouped_val_score_responses
        except Exception as e:
            error_message = f"Search Summary Relevance get_scores: {str(e)}"
            tb_str = traceback.format_exception(type(e), e, e.__traceback__)
            logging.error("\n".join(tb_str) + error_message)