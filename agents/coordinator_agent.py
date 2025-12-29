"""
Coordinator Agent module for multi-source data aggregation.

This module defines the Coordinator Agent, which aggregates output from the
Quant and Scout agents to form a unified Master State for analysis.
"""
import json
import os
import httpx
from datetime import datetime
from pydantic_ai import RunContext, ModelRetry
from config.agent_factory import create_agent
from models.models import MasterState, TechnicalData, FundamentalData
from deps.dependencies import CryptoDependencies

# Define the Coordinator Agent with explicit types
coordinator_agent = create_agent(
    model_name="openai/gpt-4o-mini",
    system_prompt=(
        "You are a Coordinator Agent. Your role is to aggregate market state data "
        "from various sources and ensure the final state is consistent and valid."
    ),
    deps_type=CryptoDependencies,
    result_type=MasterState
)

@coordinator_agent.tool
def load_and_merge_data(ctx: RunContext[CryptoDependencies]) -> dict:
    """Loads and aggregates data from Quant and Scout agent outputs.

    Reads `technical_data.json` and `fundamental_data.json` from the local
    `data/` directory.

    Args:
        ctx: PydanticAI context containing dependencies.

    Returns:
        dict: A dictionary containing the merged 'technical' and 'fundamental' data.

    Raises:
        ModelRetry: If either technical or fundamental data files are missing.
    """
    master_dict = {}
    
    # Load Technical Data
    tech_path = "data/technical_data.json"
    if os.path.exists(tech_path):
        with open(tech_path, "r") as f:
            master_dict["technical"] = json.load(f)
    else:
        raise ModelRetry("Technical data not found. Ensure the Quant Agent has run.")
    
    # Load Fundamental Data
    fund_path = "data/fundamental_data.json"
    if os.path.exists(fund_path):
        with open(fund_path, "r") as f:
            master_dict["fundamental"] = json.load(f)
    else:
        raise ModelRetry("Fundamental data not found. Ensure the Scout Agent has run.")
            
    return master_dict

async def run_coordinator_agent() -> MasterState:
    """Runs the PydanticAI Coordinator Agent to aggregate the market state.

    Orchestrates the data merging process and validates the resulting 
    state against the MasterState Pydantic model.

    Returns:
        MasterState: The validated, aggregated market state.

    Raises:
        Exception: If the aggregation or validation fails.
    """
    async with httpx.AsyncClient() as client:
        deps = CryptoDependencies(
            http_client=client,
            user_context={"request_id": "coord-001"}
        )
        
        try:
            result = await coordinator_agent.run(
                "Aggregate the technical and fundamental data from the local storage. "
                "Validate the schema and return the final master state.",
                deps=deps
            )
            
            output = result.data.model_dump()
            
            # Legacy compatibility
            os.makedirs("data", exist_ok=True)
            with open("data/master_state.json", "w") as f:
                json.dump(output, f, indent=2, default=str)
                
            return result.data
            
        except Exception as e:
            print(f"Error in coordinator_agent: {e}")
            raise

if __name__ == "__main__":
    import asyncio
    
    async def main():
        data = await run_coordinator_agent()
        print(data.model_dump_json(indent=2))
        
    asyncio.run(main())
