from typing import List
from scraper_summarizer_tool.tools.base import BaseToolkit, BaseTool
from scraper_summarizer_tool.tools.twitter.twitter_toolkit import TwitterToolkit
from scraper_summarizer_tool.tools.search.search_toolkit import SearchToolkit

TOOLKITS: List[BaseToolkit] = [SearchToolkit(), TwitterToolkit()]


def get_all_tools():
    """Return a list of all tools."""
    result: List[BaseTool] = []

    for toolkit in TOOLKITS:
        tools = toolkit.get_tools()
        result.extend(tools)

    return result


def find_toolkit_by_tool_name(tool_name: str):
    """Return the toolkit that contains the tool with the given name."""
    for toolkit in TOOLKITS:
        for tool in toolkit.get_tools():
            if tool.name == tool_name:
                return toolkit

    return None


def find_toolkit_by_name(toolkit_name: str):
    """Return the toolkit with the given name."""
    for toolkit in TOOLKITS:
        if toolkit.name == toolkit_name:
            return toolkit

    return None
