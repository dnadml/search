from typing import Dict

from langchain_community.utilities.serpapi import (
    SerpAPIWrapper as LangChainSerpAPIWrapper,
)


class SerpAPIWrapper(LangChainSerpAPIWrapper):
    num = 10

    def get_params(self, query: str) -> Dict[str, str]:
        """Get parameters for SerpAPI."""
        _params = {
            "api_key": self.serpapi_api_key,
            "q": query,
            "num": self.num
        }
        params = {**self.params, **_params}
        return params

    @staticmethod
    def _process_response(res: dict):
        """Process response from SerpAPI."""
        if "error" in res.keys():
            raise ValueError(f"Got error from SerpAPI: {res['error']}")

        # TODO use answer box later to display in UI
        # if "answer_box_list" in res.keys():
        #     res["answer_box"] = res["answer_box_list"]
        # if "answer_box" in res.keys():
        #     answer_box = res["answer_box"]
        #     if isinstance(answer_box, list):
        #         answer_box = answer_box[0]
        #     if "result" in answer_box.keys():
        #         return answer_box["result"]
        #     elif "answer" in answer_box.keys():
        #         return answer_box["answer"]
        #     elif "snippet" in answer_box.keys():
        #         return answer_box["snippet"]
        #     elif "snippet_highlighted_words" in answer_box.keys():
        #         return answer_box["snippet_highlighted_words"]
        #     else:
        #         answer = {}
        #         for key, value in answer_box.items():
        #             if not isinstance(value, (list, dict)) and not (
        #                 isinstance(value, str) and value.startswith("http")
        #             ):
        #                 answer[key] = value
        #         return str(answer)

        # UNCOMMENT TO RETURN FIRST FOUND DICTIONARY
        # if "events_results" in res.keys():
        #     return {"events_results": res["events_results"][:10]}
        # elif "sports_results" in res.keys():
        #     return {"sports_results": res["sports_results"]}
        # elif "top_stories" in res.keys():
        #     return {"top_stories": res["top_stories"]}
        # elif "news_results" in res.keys():
        #     return {"news_results": res["news_results"]}
        # elif "jobs_results" in res.keys() and "jobs" in res["jobs_results"].keys():
        #     return {"jobs_results": res["jobs_results"]["jobs"][:10]}
        # if "shopping_results" in res and res["shopping_results"]:
        #     return {"shopping_results": res["shopping_results"][:3]}
        # elif "questions_and_answers" in res:
        #     return {"questions_and_answers": res["questions_and_answers"]}
        # elif "popular_destinations" in res and "destinations" in res["popular_destinations"]:
        #     return {"popular_destinations": res["popular_destinations"]["destinations"]}
        # elif "top_sights" in res and "sights" in res["top_sights"]:
        #     return {"top_sights": res["top_sights"]["sights"]}
        # elif "images_results" in res and res["images_results"]:
        #     return {"images_results": [item["thumbnail"] for item in res["images_results"][:10]]}

        snippets = []

        # if "knowledge_graph" in res.keys():
        #     knowledge_graph = res["knowledge_graph"]
        #     title = knowledge_graph["title"] if "title" in knowledge_graph else ""
        #     if "description" in knowledge_graph.keys():
        #         snippets.append(knowledge_graph["description"])
        #     for key, value in knowledge_graph.items():
        #         if (
        #             isinstance(key, str)
        #             and isinstance(value, str)
        #             and key not in ["title", "description"]
        #             and not key.endswith("_stick")
        #             and not key.endswith("_link")
        #             and not value.startswith("http")
        #         ):
        #             snippets.append(f"{title} {key}: {value}.")

        for organic_result in res.get("organic_results", []):
            snippet_dict = {}
            if "snippet" in organic_result:
                snippet_dict["snippet"] = organic_result["snippet"]
            if "snippet_highlighted_words" in organic_result:
                snippet_dict["snippet_highlighted_words"] = organic_result[
                    "snippet_highlighted_words"
                ]
            if "rich_snippet" in organic_result:
                snippet_dict["rich_snippet"] = organic_result["rich_snippet"]
            if "rich_snippet_table" in organic_result:
                snippet_dict["rich_snippet_table"] = organic_result[
                    "rich_snippet_table"
                ]
            if "link" in organic_result:
                snippet_dict["link"] = organic_result["link"]

            snippets.append(snippet_dict)

        # if "buying_guide" in res.keys():
        #     snippets.append(res["buying_guide"])
        # if "local_results" in res and isinstance(res["local_results"], list):
        #     snippets += res["local_results"]
        # if (
        #     "local_results" in res.keys()
        #     and isinstance(res["local_results"], dict)
        #     and "places" in res["local_results"].keys()
        # ):
        #     snippets.append(res["local_results"]["places"])

        # UNCOMMENT TO RETURN FIRST FOUND DICTIONARY
        # if len(snippets) > 0:
        #     return {"organic_results": "snippets"}
        # else:
        #     return "No good search result found"

        # COMMENT ALL BELOW TO RETURN FIRST FOUND DICTIONARY
        processed_data = {}

        if "events_results" in res:
            processed_data["events_results"] = res["events_results"][:10]
        if "sports_results" in res:
            processed_data["sports_results"] = res["sports_results"]
        if "top_stories" in res:
            processed_data["top_stories"] = res["top_stories"]
        if "news_results" in res:
            processed_data["news_results"] = res["news_results"]
        if "jobs_results" in res and "jobs" in res["jobs_results"]:
            processed_data["jobs_results"] = res["jobs_results"]["jobs"][:10]
        if "shopping_results" in res and res["shopping_results"]:
            processed_data["shopping_results"] = res["shopping_results"][:3]
        if "questions_and_answers" in res:
            processed_data["questions_and_answers"] = res["questions_and_answers"]
        if "popular_destinations" in res and "destinations" in res["popular_destinations"]:
            processed_data["popular_destinations"] = res["popular_destinations"]["destinations"]
        if "top_sights" in res and "sights" in res["top_sights"]:
            processed_data["top_sights"] = res["top_sights"]["sights"]
        if "images_results" in res and res["images_results"]:
            processed_data["images_results"] = [item["thumbnail"] for item in res["images_results"][:10]]

        snippets = []

        for organic_result in res.get("organic_results", []):
            snippet_dict = {}
            if "snippet" in organic_result:
                snippet_dict["snippet"] = organic_result["snippet"]
            if "snippet_highlighted_words" in organic_result:
                snippet_dict["snippet_highlighted_words"] = organic_result["snippet_highlighted_words"]
            if "rich_snippet" in organic_result:
                snippet_dict["rich_snippet"] = organic_result["rich_snippet"]
            if "rich_snippet_table" in organic_result:
                snippet_dict["rich_snippet_table"] = organic_result["rich_snippet_table"]
            if "link" in organic_result:
                snippet_dict["link"] = organic_result["link"]

            snippets.append(snippet_dict)

        if snippets:
            processed_data["organic_results"] = snippets

        if not processed_data:
            processed_data["error"] = "No good search result found"

        return processed_data
