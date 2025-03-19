from langchain_core.runnables import RunnableConfig

from ..model import ArticleState


class CompileFinalArticle:
    """Compile the final report"""

    N = "compile_final_article"

    def __call__(self, state: ArticleState, config: RunnableConfig):

        # Get sections
        title = state["title"]
        sections = state["sections"]
        completed_sections = {
            s.name: s.content for s in state["completed_sections"]}

        # Update sections with completed content while maintaining original order
        for section in sections:
            section.content = completed_sections[section.name]

        all_sections = f"# {title}\n"

        # head_image_path = state["head_image_path"]
        # if head_image_path:
        #     all_sections += f"![AI generated image]({head_image_path})\n\n"

        # Compile final report
        all_sections += "\n\n".join(
            [f"## {s.name}\n{s.content}" for s in sections])

        return {"final_report": all_sections, "sections": sections}
