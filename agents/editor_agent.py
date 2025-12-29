"""
Editor Agent module for Markdown report generation.

This module defines the Editor Agent, which transforms a technical FinalDirective
JSON into a polished, human-readable executive summary.
"""
import json
import os
import httpx
from datetime import datetime
from pydantic_ai import RunContext, ModelRetry
from config.agent_factory import create_agent
from typing import TypedDict
from deps.dependencies import CryptoDependencies

class EditorResult(TypedDict):
    """The result of the editor's execution.
    
    Attributes:
        summary_path: The filesystem path where the Markdown report was saved.
    """
    summary_path: str

# Define the Editor Agent with explicit types
editor_agent = create_agent(
    model_name="openai/gpt-4o-mini",
    system_prompt=(
        "You are the Editor. Your task is to take a FinalDirective JSON "
        "and convert it into a polished, human-readable Markdown executive summary. "
        "Use professional tone and emphasize the primary trade stance."
    ),
    deps_type=CryptoDependencies,
    result_type=str
)

@editor_agent.tool
def get_latest_directive(ctx: RunContext[CryptoDependencies]) -> dict:
    """Finds and loads the most recent Analyst report.

    Scans the `reports/` directory for files matching `FINAL_DIRECTIVE_*.json`
    and returns the contents of the latest one (sorted by filename).

    Args:
        ctx: PydanticAI context.

    Returns:
        dict: The parsed JSON content of the latest final directive.

    Raises:
        ModelRetry: If the reports directory is missing or no directive reports are found.
    """
    reports_dir = "reports"
    if not os.path.exists(reports_dir):
        raise ModelRetry("Reports directory not found. Ensure the Analyst Agent has run.")
        
    files = [f for f in os.listdir(reports_dir) if f.startswith("FINAL_DIRECTIVE_") and f.endswith(".json")]
    if not files:
        raise ModelRetry("No directive reports found in the reports directory.")
    
    # Get latest report
    latest_report_file = sorted(files)[-1]
    with open(os.path.join(reports_dir, latest_report_file), "r") as f:
        return json.load(f)

async def run_editor_agent() -> EditorResult:
    """Runs the Editor Agent to produce a Markdown executive summary.

    Fetches the latest director, triggers the agent to generate human-readable
    content, and saves the result as a `.md` file.

    Returns:
        EditorResult: A dictionary containing the path to the generated summary.

    Raises:
        Exception: If the report generation or file saving fails.
    """
    async with httpx.AsyncClient() as client:
        deps = CryptoDependencies(
            http_client=client,
            user_context={"request_id": "editor-001"}
        )
        
        try:
            result = await editor_agent.run(
                "Find the latest trading directive and generate a professional Markdown "
                "executive summary. Return the summary content.",
                deps=deps
            )
            
            summary = result.data
            
            os.makedirs("reports", exist_ok=True)
            summary_path = f"reports/EXECUTIVE_SUMMARY_{datetime.utcnow().strftime('%Y%m%d')}.md"
            with open(summary_path, "w", encoding="utf-8") as f:
                f.write(summary)
                
            return {"summary_path": summary_path}

        except Exception as e:
            print(f"Error in editor_agent: {e}")
            raise

if __name__ == "__main__":
    import asyncio
    
    async def main():
        data = await run_editor_agent()
        print(json.dumps(data, indent=2))
        
    asyncio.run(main())
