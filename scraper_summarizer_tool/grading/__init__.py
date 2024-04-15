from scraper_summarizer_tool.grading.config import RewardScoringType
from scraper_summarizer_tool.grading.prompts import SummaryRelevancePrompt
from scraper_summarizer_tool.grading.search_content_relevance import WebSearchContentRelevanceModel
from scraper_summarizer_tool.grading.summary_relevance import SummaryRelevanceGradingModel
from scraper_summarizer_tool.protocol import ScraperStreamingSynapse
from scraper_summarizer_tool.tools import run_tool_manager


def run_grading_tool_manager(prompt, tools):
    web_search_grading = False

    tool_manager, result = run_tool_manager(prompt, tools)
    texts = result['summaries']
    completions = str(texts)
    search_completion_links = None
    search_completion_links_metadata = None

    if "Web Search" in tools:
        links = result["Web Search"]['content']
        search_completion_links_metadata = {link['link']: link for link in links}
        search_completion_links = list(search_completion_links_metadata.keys())
        web_search_grading = True

    responses = [
        ScraperStreamingSynapse(
            completion=completions,
            messages=prompt,
            texts=texts,
            search_completion_links=search_completion_links,
            search_completion_links_metadata=search_completion_links_metadata,
        ),
    ]

    summary_scores = (SummaryRelevanceGradingModel().get_scores(prompt, responses))
    # search_summary_scores = (WebSearchContentRelevanceModel().get_scores("Climate Changes in Pakistan", responses))
    web_search_scores = (WebSearchContentRelevanceModel().get_scores(prompt, responses)) if web_search_grading else None

    return summary_scores, web_search_scores


if __name__ == '__main__':
    prompt = "Effects of Global Warming"
    tools = [
        "Web Search",
        # "Youtube Search",
        # "Wikipedia Search",
        # "Recent Tweets"
    ]
    summary_scores, web_search_scores = run_grading_tool_manager(prompt, tools)
    print("Summary Scores", summary_scores)
    print("Web Search Scores", web_search_scores)