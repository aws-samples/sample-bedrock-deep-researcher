from datetime import datetime, timezone

from .retrievers import RetrieverResults


def generate_search_queries_prompt(
    query: str, context: str = None, num_queries: int = 3
):
    dynamic_example = ", ".join([f'"query {i+1}"' for i in range(num_queries)])
    prompt_context = f"Context: {context}" if context else ""

    return f"""
You are a seasoned research assistant tasked with generating a list of Google search queries to find relevant information for a given task. Follow these steps:

1. Review the task description:
<task>{query}</task>

2. Consider the provided context that may inform and refine your search queries:
<context>{prompt_context}</context>
This context provides real-time web information that can help you generate more specific and relevant queries. Take into account any current events, recent developments, or specific details mentioned in the context that could enhance the search queries.

3. Generate {num_queries} Google search queries that can help form an objective opinion on the given task, following these requirements:
- If required, assume the current date is {datetime.now(timezone.utc).strftime('%B %d, %Y')}.
- Respond with a list of strings in the following format: [{dynamic_example}]
- The response should contain ONLY the list of search queries, without any additional text.

Provide your response immediately without any preamble.
"""
