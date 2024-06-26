import json

from scraper_summarizer_tool.grading.config import RewardScoringType
from scraper_summarizer_tool.grading.prompts import SummaryRelevancePrompt
from scraper_summarizer_tool.grading.search_content_relevance import WebSearchContentRelevanceModel
from scraper_summarizer_tool.grading.summary_relevance import SummaryRelevanceGradingModel
from scraper_summarizer_tool.grading.twitter_content_relevance import TwitterContentRelevanceModel
from scraper_summarizer_tool.tools import run_tool_manager
from scraper_summarizer_tool.protocol import ScraperStreamingSynapse


def grading_tool_manager(prompt, tools):
    result = json.loads(run_tool_manager(prompt, tools))

    print(
        "\n-------------------------- Search Results Start --------------------------\n",
        result,
        "\n-------------------------- Search Results End --------------------------\n"
    )

    texts = result['summaries']
    completions = ', '.join(texts.values())
    search_completion_links = []
    search_completion_links_metadata = {}
    completion_links = []
    completion_links_metadata = {}
    web_search_grading = False
    twitter_grading = False
    wikipedia_grading = False
    youtube_grading = False

    if "Web Search" in result:
        sections = result["Web Search"]
        for section, links in sections.items():
            search_completion_links_metadata.update({link['link']: link for link in links})
            search_completion_links = list(search_completion_links_metadata.keys())
        web_search_grading = True

    if "Recent Tweets" in result and 'data' in result["Recent Tweets"]:
        links = (result["Recent Tweets"]['data'])
        completion_links_metadata = {
            f"https://twitter.com/{link['author_id']}/status/{link['id']}": link for link in links
        }
        # completion_links_metadata = {
        #     link['entities']['urls'][0]['url']: link
        #     for link in links
        #     if 'entities' in link and 'urls' in link['entities'] and 'url' in link['entities']['urls'][0]
        # }
        completion_links = list(completion_links_metadata.keys())
        twitter_grading = True

    responses = [
        ScraperStreamingSynapse(
            completion=completions,
            messages=prompt,
            texts=texts,
            search_completion_links=search_completion_links,
            search_completion_links_metadata=search_completion_links_metadata,
            completion_links=completion_links,
            completion_links_metadata=completion_links_metadata
        ),
    ]

    summary_scores = (SummaryRelevanceGradingModel().get_scores(prompt, responses))
    web_search_scores = (WebSearchContentRelevanceModel().get_scores(prompt, responses)) if web_search_grading else None
    twitter_scores = (TwitterContentRelevanceModel().get_scores(prompt, responses)) if twitter_grading else None

    if "Wikipedia Search" in result:
        links = result["Wikipedia Search"]
        search_completion_links_metadata = {
            link['url']: link for link in links
        }
        search_completion_links = list(search_completion_links_metadata.keys())
        wikipedia_grading = True

    responses = [
        ScraperStreamingSynapse(
            completion=completions,
            messages=prompt,
            texts=texts,
            search_completion_links=search_completion_links,
            search_completion_links_metadata=search_completion_links_metadata,
        ),
    ]

    wikipedia_scores = (WebSearchContentRelevanceModel().get_scores(prompt, responses)) if wikipedia_grading else None

    if "Youtube Search" in result:
        links = result["Youtube Search"]
        search_completion_links_metadata = {
            f"https://www.youtube.com/{link['url_suffix']}": link for link in links
        }
        search_completion_links = list(search_completion_links_metadata.keys())
        youtube_grading = True

    responses = [
        ScraperStreamingSynapse(
            completion=completions,
            messages=prompt,
            texts=texts,
            search_completion_links=search_completion_links,
            search_completion_links_metadata=search_completion_links_metadata,
        ),
    ]

    youtube_grading = (WebSearchContentRelevanceModel().get_scores(prompt, responses)) if youtube_grading else None

    return summary_scores, web_search_scores, twitter_scores, wikipedia_scores, youtube_grading


def select_tools(tools):
    print("Select tools (press Enter after each selection, press Enter twice to finish):")
    selected_tools = []
    while True:
        for i, tool in enumerate(tools, 1):
            print(f"{i}. {tool}")
        choice = input("Enter the number of the tool (or press Enter to finish): ")
        if choice == "":
            break
        try:
            index = int(choice) - 1
            selected_tool = tools[index]
            selected_tools.append(selected_tool)
        except (ValueError, IndexError):
            print("Invalid input. Please enter a valid number.")
    return selected_tools


def run_grading_tool_manager():
    prompt = input("Enter the prompt text: ")
    tools = [
        "Web Search",
        "Youtube Search",
        "Wikipedia Search",
        "Recent Tweets",
        "Full Archive Tweets"
    ]
    selected_tools = select_tools(tools)
    print("Selected Tools:", selected_tools)
    (
        summary_scores,
        web_search_scores,
        twitter_scores,
        wikipedia_scores,
        youtube_scores
    ) = grading_tool_manager(prompt, selected_tools)

    print(
        "\n-------------------------- Summary Scores Start --------------------------\n",
        summary_scores,
        "\n-------------------------- Summary Scores End --------------------------\n"
    )
    if web_search_scores:
        print(
            "\n-------------------------- Web Search Scores Start --------------------------\n",
            web_search_scores,
            "\n-------------------------- Web Search Scores End --------------------------\n"
        )

    if twitter_scores:
        print(
            "\n-------------------------- Twitter Scores Start --------------------------\n",
            twitter_scores,
            "\n-------------------------- Twitter Scores End --------------------------\n"
        )

    if wikipedia_scores:
        print(
            "\n-------------------------- Wikipedia Scores Start --------------------------\n",
            wikipedia_scores,
            "\n-------------------------- Wikipedia Scores End --------------------------\n"
        )

    if youtube_scores:
        print(
            "\n-------------------------- YouTube Scores Start --------------------------\n",
            youtube_scores,
            "\n-------------------------- YouTube Scores End --------------------------\n"
        )
