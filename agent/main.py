# agent/main.py

from google.genai import types
import json
import logging
from typing import Dict, Any, Optional

# Import the core components
from client_config import CLIENT, SUMMARY_MODEL
from .planner import run_planner_auditor
from .executor import execute_plan_step
from .tools import get_available_tool_declarations

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def run_auditor(user_id: str, expense_text: str, test_engine: Optional[Any] = None) -> Dict[str, Any]:
    """
    The main orchestrator function (entry point) that runs the Plan-Reflect-Execute cycle.
    """
    if not CLIENT:
        logging.error("Gemini client not initialized.")
        return {"final_report": "System Error: Gemini client not available.", "full_history": []}

    # 1. SETUP
    tool_declarations = get_available_tool_declarations(CLIENT)

    # 2. PHASE 1 & 2: PLAN AND REFLECT
    planning_result = run_planner_auditor(
        client=CLIENT,
        user_id=user_id,
        expense_text=expense_text,
        available_tools_declarations=tool_declarations
    )

    final_steps = planning_result.get('plan_steps', [])
    if not final_steps:
        logging.error("Execution aborted: No valid plan steps were generated.")
        return planning_result

    # 3. PHASE 3: EXECUTION
    logging.info(f"Starting execution of {len(final_steps)} plan steps...")

    execution_history = []
    for step in final_steps:
        tool_name = step.get('tool_name', 'UNKNOWN')
        args = step.get('arguments', {})

        # Execute the tool
        result = execute_plan_step(tool_name, args, user_id, db_engine=test_engine)

        # 🟢 FIX: Clean the result before adding to history to avoid serialization errors
        # We remove 'db_engine', 'test_engine', or 'engine' if they exist in the result
        if isinstance(result, dict):
            clean_result = {
                k: v for k, v in result.items()
                if k not in ['engine', 'db_engine', 'test_engine', 'arguments_used']
            }
            # Also ensure any nested dicts (like arguments_used) don't contain the engine
            execution_history.append(clean_result)
        else:
            execution_history.append(result)

    # 4. PHASE 4: SUMMARIZATION
    logging.info("PHASE 4: SUMMARIZATION (Generating final report)")

    # Serialize the CLEANED history
    try:
        history_json = json.dumps(execution_history, indent=2)
    except TypeError as e:
        logging.error(f"Serialization failed again: {e}")
        history_json = str(execution_history)  # Fallback to string representation

    final_summary_prompt = (
        "Based on the following execution history, generate a final, concise, and "
        "professional report for the user. Explicitly state the final budget status "
        "(e.g., 'Status: Under Budget' or 'Warning: OVER BUDGET')."
        f"\n\nEXECUTION HISTORY:\n{history_json}"
    )

    try:
        # Using flash-lite for summarization to save quota, or flash for speed
        summary_response = CLIENT.models.generate_content(
            model=SUMMARY_MODEL,
            contents=final_summary_prompt
        )
        final_report = summary_response.text
    except Exception as e:
        final_report = f"SUMMARIZATION ERROR: Could not generate report. Error: {e}"

    return {
        "final_report": final_report,
        "full_history": execution_history,
        "plan_details": planning_result.get('final_plan', {})
    }


if __name__ == "__main__":
    # Internal test run logic
    pass