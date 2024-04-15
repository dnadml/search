from scraper_summarizer_tool.tools import run_tool_manager
from pprint import pprint
if __name__ == "__main__":
    # 'Web Search': SerpGoogleSearchTool()
    # 'Wikipedia Search': WikipediaSearchTool()
    # 'Youtube Search': YoutubeSearchTool()
    # 'Recent Tweets': GetRecentTweetsTool()
    # 'Full Archive Tweets': GetFullArchiveTweetsTool()
    tool_manager, result = run_tool_manager("Architecture Styles in Software Development",
                              ["Youtube Search", "Web Search"]
                              )
    print(result)
