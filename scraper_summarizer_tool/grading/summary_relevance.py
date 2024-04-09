import logging
import traceback
import asyncio
from typing import List, Union
from scraper_summarizer_tool.grading.config import RewardModelType, RewardScoringType
from scraper_summarizer_tool.grading.scores import get_score_by_openai
from scraper_summarizer_tool.grading.prompts import SummaryRelevancePrompt
from scraper_summarizer_tool.protocol import ScraperStreamingSynapse


class SummaryRelevanceGradingModel:
    reward_model_name: str = "VMware/open-llama-7b-open-instruct"
    scoring_type = RewardScoringType.summary_relevance_score_template

    @property
    def name(self) -> str:
        return RewardModelType.summary_relavance_match.value

    def get_scoring_text(self, prompt: str, response: ScraperStreamingSynapse):
        try:
            completion = response.completion
            if not completion:
                return None
            if not self.scoring_type:
                return None

            scoring_prompt = None
            scoring_prompt_text = None
            if self.scoring_type.value == RewardScoringType.summary_relevance_score_template.value:
                scoring_prompt = SummaryRelevancePrompt()

            if scoring_prompt is None:
                return None

            if not scoring_prompt_text:
                scoring_prompt_text = scoring_prompt.text(prompt, completion)

            return scoring_prompt, [
                {"role": "system", "content": scoring_prompt.get_system_message()},
                {"role": "user", "content": scoring_prompt_text},
            ]
        except Exception as e:
            logging.error(f"Summary Relevance get_scoring_text: {str(e)}")
            return None

    def get_scores(self, prompt: str, responses: List[ScraperStreamingSynapse]):
        try:
            completions = [
                response.completion.strip() for response in responses if response.completion is not None
            ]
            logging.info(f"SummaryRelevanceGradingModel | PROMPT: {prompt}")
            logging.debug(
                f"SummaryRelevanceGradingModel | Calculating {len(completions)} rewards (typically < 1 sec/reward)."
            )
            logging.info(
                f"SummaryRelevanceGradingModel | prompt: {repr(prompt[:50])} ... {repr(prompt[-50:])}"
            )
            scoring_messages = [
                self.get_scoring_text(prompt, response) for response in responses
            ]
            filter_scoring_messages = [
                msg for msg in scoring_messages if msg is not None
            ]
            logging.debug(
                f"SummaryRelevanceGradingModel | Calculating {len(filter_scoring_messages)} rewards (typically < 1 sec/reward)."
            )
            logging.info(
                f"SummaryRelevanceGradingModel | prompt: {repr(prompt[:50])} ... {repr(prompt[-50:])}"
            )
            messages = [
                {str(index): item[1]}
                for index, item in enumerate(scoring_messages)
                if item is not None
            ]

            scores = {}
            if messages:
                logging.info(
                    f"Executing get_score_by_openai on {len(messages)} summary relevance messages."
                )
                score_responses = asyncio.run(get_score_by_openai(messages=messages))
                if score_responses and isinstance(score_responses, dict):  # Ensure score_responses is a dictionary
                    for (key, score_result), (scoring_prompt, _) in zip(score_responses.items(), filter_scoring_messages):
                        if score_result is not None:
                            score = scoring_prompt.extract_score(score_result)
                            # Scale 0-10 score to 0-1 range.
                            score /= 10.0
                            scores[key] = {}
                            scores[key]['value'] = score_result
                            scores[key]['score'] = score

            return scores
        except Exception as e:
            error_message = f"Summary Relevance get_scores: {str(e)}"
            tb_str = traceback.format_exception(type(e), e, e.__traceback__)
            logging.error("\n".join(tb_str) + error_message)
