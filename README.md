<div align="center">

# **Scrape & Summarize Tool**

</div>

## Installation

**Requirements:** Python 3.8 or higher

1. Clone the repository:
   ```bash
   git clone https://github.com/dnadml/search.git
   ```
2. Install the requirements:
   ```bash
   cd search
   python3 -m pip install -r requirements.txt
   python3 -m pip install -e .
   ```

---

## Preparing Your Environment
- Create an enviroment file (.env)
- Set the following environment variables:
- OPENAI_API_KEY=your-key-here
- TWITTER_BEARER_TOKEN=your-token-here
- SERPAPI_API_KEY=your-key-here


## Run

**1. Import the package:**
   ```python
   from scraper_summarizer_tool.tools import run_tool_manager
   ```
**2. Select the Tools:**
- 'Web Search': SerpGoogleSearchTool()
- 'Wikipedia Search': WikipediaSearchTool()
- 'Youtube Search': YoutubeSearchTool()
- 'Recent Tweets': GetRecentTweetsTool()
- 'Full Archive Tweets': GetFullArchiveTweetsTool()

**3. Run Tool Manager:**
   ```python   
   from scraper_summarizer_tool.tools import run_tool_manager
   run_tool_manager(prompt="Architecture Styles in Software Development", filter_profanity=True, tools=["Web Search", "Recent Tweets"])

   # To automatically select "tools" based on Prompt
   run_tool_manager(prompt="Donald Trump", filter_profanity=True)
   ```
