import json
import logging
from typing import Dict, Any
from google.genai import types

# Import centralized configuration and schema
from client_config import PLANNER_MODEL, JUDGE_MODEL
from schemas.plan_schema import PLAN_SCHEMA

# --- TOOL DEFINITIONS (Text-based for JSON Mode) ---
TOOL_DESCRIPTIONS = """
AVAILABLE TOOLS:
1. log_expense_tool:
   - Purpose: Records a new expense in the database.
   - Arguments: {vendor: str, amount: float, category: str, user_id: str}
2. check_budget_tool:
   - Purpose: Retrieves the budget status and remaining balance.
   - Arguments: {category: str, user_id: str}
"""

# --- AGENT PROMPTS ---

PLANNER_PROMPT = f"""
You are the Strategic Planner for a Financial Auditor. Your task is to break down the user's 
request into a sequential list of actions.

{TOOL_DESCRIPTIONS}

STRATEGIC RULES:
1. Whenever a user wants to log an expense, you MUST ALWAYS follow it with a 'check_budget_tool' 
   call for that same category to verify the new status.
2. Order: 1st Log Expense -> 2nd Check Budget.

You MUST output a JSON object that adheres strictly to the provided schema.
CRITICAL: Every tool call must include the 'user_id' in its arguments.
"""

JUDGE_PROMPT = f"""
CRITIC: You are evaluating an action plan for a Financial Auditor.
{TOOL_DESCRIPTIONS}

Check for:
1. AUDITOR RULE: Every 'log_expense_tool' call MUST be followed by a 'check_budget_tool' call 
   to see if the user went over budget. If this is missing, the plan is INVALID.
2. Accuracy: Are the tool names and arguments (user_id, amount, category) extracted correctly?

If the plan is flawed, explain why in the 'critique' field and provide the corrected plan. 
If perfect, put 'Plan is valid' in 'critique' and return the original plan steps.
"""


def run_planner_auditor(client, user_id: str, expense_text: str, available_tools_declarations: list) -> Dict[str, Any]:
    """
    Orchestrates the Planning and Reflection phases.
    Fails fast on system errors to prevent unvalidated plan execution.
    """

    # --- PHASE 1: INITIAL PLANNING ---
    logging.info("PHASE 1: Generating Initial Plan")

    try:
        plan_response = client.models.generate_content(
            model=PLANNER_MODEL,
            contents=f"User ID: {user_id}\nRequest: {expense_text}",
            config=types.GenerateContentConfig(
                system_instruction=PLANNER_PROMPT,
                # Tools are omitted here because we use TOOL_DESCRIPTIONS in prompt + JSON mode
                response_mime_type="application/json",
                response_schema=PLAN_SCHEMA
            )
        )
        initial_plan_data = json.loads(plan_response.text)
    except Exception as e:
        logging.error(f"PLANNING CRITICAL ERROR: {e}")
        return {
            "final_report": f"Audit aborted: Initial planning failed due to system error: {e}",
            "plan_steps": [],
            "final_plan": {}
        }

    # --- PHASE 2: JUDGE/REFLECTION ---
    logging.info("PHASE 2: Judging/Correcting Plan")

    judge_contents = [
        f"Request: {expense_text}",
        f"Proposed Plan: {plan_response.text}"
    ]

    try:
        judge_response = client.models.generate_content(
            model=JUDGE_MODEL,
            contents=judge_contents,
            config=types.GenerateContentConfig(
                system_instruction=JUDGE_PROMPT,
                response_mime_type="application/json",
                response_schema=PLAN_SCHEMA
            )
        )
        final_plan_data = json.loads(judge_response.text)
        logging.info(f"Judge Reflection: {final_plan_data.get('critique', 'No critique provided.')}")

    except Exception as e:
        # 🟢 FAIL FAST: Do not "fallback" to the initial plan if the system is failing (e.g., 429 Quota)
        # This prevents unvalidated actions from being executed.
        error_msg = f"Audit aborted: Reflection phase failed due to system error: {e}"
        logging.error(error_msg)
        return {
            "final_report": error_msg,
            "plan_steps": [],
            "final_plan": {},
            "critique": "SYSTEM FAILURE"
        }

    return {
        "final_plan": final_plan_data,
        "plan_steps": final_plan_data.get('plan_steps', []),
        "critique": final_plan_data.get('critique', '')
    }