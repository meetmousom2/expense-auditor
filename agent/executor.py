# agent/executor.py
from typing import Dict, Any, Optional
from .tools import TOOL_REGISTRY
import logging

def execute_plan_step(tool_name: str, args: Dict[str, Any], user_id: str, db_engine: Optional[Any]) -> Dict[str, Any]:
    """
    Executes a single step (tool call) from the structured plan, injecting the DB engine.
    """
    logging.info(f"EXECUTOR: Starting execution for {tool_name}")

    if tool_name not in TOOL_REGISTRY:
        error_msg = f"Tool '{tool_name}' not found in registry."
        logging.error(error_msg)
        return {"tool_name": tool_name, "status": "FAILED", "result": error_msg}

    tool_function = TOOL_REGISTRY[tool_name]

    final_args = args.copy()
    final_args['user_id'] = user_id
    final_args['db_engine'] = db_engine  # CRITICAL: Pass the DB engine

    try:
        # Unpack and execute the core Python function
        tool_result = tool_function(**final_args)
        status = "SUCCESS"
        logging.info(f"EXECUTOR: Success for {tool_name}")

    except Exception as e:
        tool_result = f"Tool Execution Error: {type(e).__name__}: {str(e)}"
        status = "FAILED"
        logging.error(f"EXECUTOR: Error during {tool_name}: {tool_result}")

    return {
        "tool_name": tool_name,
        "status": status,
        "arguments_used": final_args,
        "result": tool_result
    }