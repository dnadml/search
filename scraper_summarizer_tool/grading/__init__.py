from scraper_summarizer_tool.grading.config import RewardScoringType
from scraper_summarizer_tool.grading.prompts import SummaryRelevancePrompt
from scraper_summarizer_tool.grading.summary_relevance import SummaryRelevanceGradingModel
from scraper_summarizer_tool.protocol import ScraperStreamingSynapse
from scraper_summarizer_tool.tools import run_tool_manager
from pprint import pprint

if __name__ == '__main__':
    prompt = "Effects of Global Warming"
    test_result_1 = run_tool_manager(prompt, ["Web Search", "Youtube Search", "Wikipedia Search"])
    test_result_2 = run_tool_manager(prompt, ["Web Search"])

    responses = [
        ScraperStreamingSynapse(
            messages="Architecture Styles in Software Development",
            seed=1,
            completion="This has no summary related whatsoever.",
            completion_links=[
                "https://twitter.com/XtalksFood/status/1743286252969828589",
                "https://twitter.com/XtalksFood/status/1743286252969828589",
            ],
        ),
        ScraperStreamingSynapse(
            completion=test_result_1[-1]['summary'], messages=prompt
        ),
        ScraperStreamingSynapse(
            completion=test_result_2[-1]['summary'], messages=prompt
        ),
    ]

    scores = (SummaryRelevanceGradingModel().get_scores(prompt, responses))
    pprint(scores)
