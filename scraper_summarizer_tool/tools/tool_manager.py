from typing import List, Dict, Optional, Any
import re

import requests
from openai import OpenAI
import asyncio
import os
import json
import logging
from langchain_openai import ChatOpenAI
from starlette.types import Send
import better_profanity

from scraper_summarizer_tool.services.twitter_prompt_analyzer import TwitterPromptAnalyzer
from scraper_summarizer_tool.tools.base import BaseTool
from scraper_summarizer_tool.tools.get_tools import (
    get_all_tools,
    find_toolkit_by_tool_name,
    find_toolkit_by_name,
)
from scraper_summarizer_tool.tools.twitter.twitter_toolkit import TwitterToolkit
from langchain_core.prompts import PromptTemplate
from langchain.tools.render import render_text_description
from scraper_summarizer_tool.protocol import ScraperTextRole
from openai import AsyncOpenAI
from scraper_summarizer_tool.tools.response_streamer import ResponseStreamer
from scraper_summarizer_tool.protocol import TwitterPromptAnalysisResult

OpenAI.api_key = os.environ.get("OPENAI_API_KEY")

if not OpenAI.api_key:
    raise ValueError("Please set the OPENAI_API_KEY environment variable.")

TEMPLATE = """Answer the following question as best you can.
User Question: {input}

You have access to the following tools:
{tools}

You can use multiple tools to answer the question. Order of tools does not matter.

Here is example of JSON array format to return. Keep in mind that this is example:
[
  {{
    "action": "Recent Tweets",
    "args": {{
      "query": "AI trends"
    }}
  }},
  {{
    "action": "Web Search",
    "args": {{
      "query": "What are AI trends?"
    }}
  }}
]
"""

prompt_template = PromptTemplate.from_template(TEMPLATE)

client = AsyncOpenAI(timeout=60.0)


class ToolManager:
    openai_summary_model: str = "gpt-3.5-turbo-0125"
    all_tools: List[BaseTool]
    manual_tool_names: List[str]
    tool_name_to_instance: Dict[str, BaseTool]
    twitter_prompt_analysis: Optional[TwitterPromptAnalysisResult]
    twitter_data: Optional[Dict[str, Any]]

    def __init__(self, prompt, manual_tool_names, send):
        self.prompt = prompt
        self.manual_tool_names = manual_tool_names

        self.response_streamer = ResponseStreamer(send=send)
        self.send = send
        self.openai_summary_model = self.openai_summary_model

        self.all_tools = get_all_tools()
        self.tool_name_to_instance = {tool.name: tool for tool in self.all_tools}
        self.twitter_prompt_analysis = None
        self.twitter_data = None

    async def run(self):
        response_data = {}
        actions = await self.detect_tools_to_use()

        # Always Get Recent Tweets
        if not {"action": "Recent Tweets", "args": self.prompt} in actions:
            actions.append({"action": "Recent Tweets", "args": self.prompt})

        tasks = [asyncio.create_task(self.run_tool(action)) for action in actions]
        toolkit_results = {}

        for completed_task in asyncio.as_completed(tasks):
            result, toolkit_name, tool_name = await completed_task
            response_data[tool_name] = result

            if tool_name == "Recent Tweets" or tool_name == "Full Archive Tweets":
                response_data['keywords'] = result[1].keywords
                response_data[tool_name] = result[0]

            if result is not None:
                if toolkit_name == TwitterToolkit().name:
                    toolkit_results[toolkit_name] = result
                else:
                    if toolkit_name not in toolkit_results:
                        toolkit_results[toolkit_name] = ""

                    toolkit_results[
                        toolkit_name
                    ] += f"{tool_name} results: {result}\n\n"

        # Twitter Toolkit Not Selected
        # if 'keywords' not in response_data:
            # twitter_prompt_analyzer = await TwitterPromptAnalyzer().generate_query_params_from_prompt(self.prompt)
            # response_data['keywords'] = twitter_prompt_analyzer['keywords']

        streaming_tasks = []

        for toolkit_name, results in toolkit_results.items():
            response, role = await find_toolkit_by_name(toolkit_name).summarize(
                prompt=self.prompt, model=self.openai_summary_model, data=results
            )

            streaming_task = asyncio.create_task(
                self.response_streamer.stream_response(response=response, role=role)
            )

            streaming_tasks.append(streaming_task)

        await asyncio.gather(*streaming_tasks)

        await self.finalize_summary_and_stream(
            self.response_streamer.get_full_text(),
        )

        await self.response_streamer.send_texts_event()
        await self.response_streamer.send_completion_event()

        completion_response_body = {
            "type": "completion",
            "content": self.response_streamer.get_full_text(),
        }

        await self.send(
            {
                "type": "http.response.body",
                "body": json.dumps(completion_response_body).encode("utf-8"),
            }
        )

        if self.response_streamer.more_body:
            await self.send(
                {
                    "type": "http.response.body",
                    "body": b"",
                    "more_body": False,
                }
            )
        response_data['summaries'] = (self.response_streamer.get_texts_by_role())
        return response_data

    async def detect_tools_to_use(self):
        # If user provided tools manually, use them
        if self.manual_tool_names:
            return [
                {"action": tool_name, "args": self.prompt}
                for tool_name in self.manual_tool_names
            ]

        # Otherwise identify tools to use based on prompt
        # TODO model
        llm = ChatOpenAI(model_name="gpt-4-0125-preview", temperature=0.2)
        chain = prompt_template | llm

        tools_description = render_text_description(self.all_tools)

        message = chain.invoke(
            {
                "input": self.prompt,
                "tools": tools_description,
            }
        )

        actions = []

        try:
            actions = json.loads(message.content)
        except json.JSONDecodeError as e:
            print(e)
        return actions

    async def run_tool(self, action: Dict[str, str]):
        tool_name = action.get("action")
        tool_args = action.get("args")
        tool_instance = self.tool_name_to_instance.get(tool_name)

        if not tool_instance:
            return

        logging.info(f"Running tool: {tool_name} with args: {tool_args}")

        tool_instance.tool_manager = self
        result = None

        try:
            result = await tool_instance.ainvoke(tool_args)
        except Exception as e:
            logging.error(f"Error running tool {tool_name}: {e}")

        if tool_instance.send_event and result is not None:
            logging.info(f"Sending event with data from {tool_name} tool")

            await tool_instance.send_event(
                send=self.send,
                response_streamer=self.response_streamer,
                data=result,
            )

        return result, find_toolkit_by_tool_name(tool_name).name, tool_name

    async def finalize_summary_and_stream(self, information):
        content = f"""
            In <UserPrompt> provided User's prompt (Question).
            In <Information>, provided highlighted key information and relevant links from Twitter and Google Search.

            <UserPrompt>
            {self.prompt}
            </UserPrompt>

                Output Guidelines (Tasks):
                1. Summary: Conduct a thorough analysis of <TwitterData> in relation to <UserPrompt> and generate a comprehensive summary.
                2. Relevant Links: Provide a selection of Twitter links that directly correspond to the <UserPrompt>. For each link, include a concise explanation that connects its relevance to the user's question.
                Synthesize insights from both the <UserPrompt> and the <TwitterData> to formulate a well-rounded response. But don't provide any twitter link, which is not related to <UserPrompt>.
                3. Highlight Key Information: Identify and emphasize any crucial information that will be beneficial to the user.
                4. You would explain how you did retrieve data based on <PromptAnalysis>.

            <Information>
            {information}
            </Information>
        """

        system_message = """As a summary analyst, your task is to provide users with a clear and concise summary derived from the given information and the user's query.

        Output Guidelines (Tasks):
        1. Summary: Conduct a thorough analysis of <Information> in relation to <UserPrompt> and generate a comprehensive summary.

        Operational Rules:
        1. Emphasis on Critical Issues: Focus on and clearly explain any significant issues or points of interest that emerge from the analysis.
        2. Seamless Integration: Avoid explicitly stating "Based on the provided <Information>" in responses. Assume user awareness of the data integration process.
        3. Not return text like <UserPrompt> to your response, make response easy to understand to any user.
        4. Start text with bold text "Summary:".
        """

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": content},
        ]

        response = await client.chat.completions.create(
            model=self.openai_summary_model,
            messages=messages,
            temperature=0.1,
            stream=True,
        )

        await self.response_streamer.stream_response(
            response=response, role=ScraperTextRole.FINAL_SUMMARY
        )

        logging.info(
            "================================== Completion Response ==================================="
        )
        logging.info(
            f"{self.response_streamer.get_full_text()}"
        )  # Print the full text at the end
        logging.info(
            "================================== Completion Response ==================================="
        )


def remove_links(text):
    url_pattern = re.compile(r"https?://\S+")
    return url_pattern.sub("", text)


def profanity_percentage(text):
    bp = better_profanity.Profanity()
    words = text.split()
    total_words = 0
    profane_words = 0

    for word in words:
        clean_word = ''.join(filter(str.isalnum, word))
        if clean_word:
            total_words += 1
            if bp.contains_profanity(clean_word.lower()):
                profane_words += 1
    profanity_percentage = (profane_words / total_words) * 100 if total_words > 0 else 0.0
    return profanity_percentage


def filter_inappropriate_content(results, percentage=50):
    if "Recent Tweets" in results and 'data' in results['Recent Tweets']:
        results['Recent Tweets']['data'] = [
            item for item in results['Recent Tweets']['data']
            if percentage > profanity_percentage(str(item['text']))
        ]

    # if "Full Archived Tweets" in results:
    #     results['Full Archived Tweets']['data'] = [
    #         item for item in results['Full Archived Tweets']['data']
    #         if percentage > profanity_percentage(str(item['text']))
    #     ]

    if "Web Search" in results:
        for section, data in results['Web Search'].items():
            results['Web Search'][section] = [
                item for item in data
                if percentage > profanity_percentage(" ".join(remove_links(str(value)) for value in item.values()))
            ]

    if "Wikipedia Search" in results:
        results['Wikipedia Search'] = [
            item for item in results['Wikipedia Search']
            if percentage > profanity_percentage(" ".join(remove_links(str(value)) for value in item.values()))
        ]

    if "Youtube Search" in results:
        results['Youtube Search'] = [
            item for item in results['Youtube Search']
            if percentage > profanity_percentage(str(f"{item['title']} {item['long_desc']} {item['channel']}"))
        ]

    return results


async def set_tool_manager(prompt, tools):
    # 'Web Search': SerpGoogleSearchTool()
    # 'Wikipedia Search': WikipediaSearchTool()
    # 'Youtube Search': YoutubeSearchTool()
    # 'Recent Tweets': GetRecentTweetsTool()
    # 'Full Archive Tweets': GetFullArchiveTweetsTool()

    logging.info(
        "================================== Prompt ==================================="
    )
    logging.info(prompt)
    logging.info(
        "================================== Prompt ===================================="
    )

    # Define the send function using ResponseStreamer
    async def send(message):
        pass

    # Initialize ResponseStreamer with the send function
    response_streamer = ResponseStreamer(send)

    # Pass the send function to tool_manager initialization
    tool_manager = ToolManager(
        prompt=prompt,
        manual_tool_names=tools,
        send=response_streamer.send,
    )
    result = await tool_manager.run()
    return tool_manager, result


def run_tool_manager(prompt, tools=None, filter_profanity=True):
    tool_manager, result = asyncio.run(set_tool_manager(prompt, tools))
    if filter_profanity:
        result = filter_inappropriate_content(result)
    return json.dumps(result)


if __name__ == "__main__":
    result = json.loads(run_tool_manager(
        "Brooklyn Nine Nine",
        ["Web Search"],
        False
    ))
    print(
        "\n-------------------------- Search Results Start --------------------------\n",
        (result),
        "\n-------------------------- Search Results End --------------------------\n"
    )
    print(
        "\n-------------------------- Filtered Search Results Start --------------------------\n",
        filter_inappropriate_content(result),
        "\n-------------------------- Filtered Search Results End --------------------------\n"
    )
