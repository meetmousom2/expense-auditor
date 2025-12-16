# schemas/plan_schema.py

# This schema defines a single action the agent should take
PLAN_STEP_SCHEMA = {
    "type": "object",
    "properties": {
        "step_number": {
            "type": "integer",
            "description": "The sequential order of the step, starting from 1."
        },
        "tool_name": {
            "type": "string",
            "description": "The exact name of the tool to call: 'log_expense_tool' or 'check_budget_tool'."
        },
        "arguments": {
            "type": "object",
            "description": "The parameters for the tool. MUST include user_id, amount, vendor, or category as required.",
            "properties": {
                "user_id": {"type": "string"},
                "vendor": {"type": "string", "description": "The merchant or vendor name."},
                "amount": {"type": "number", "description": "The transaction amount."},
                "category": {"type": "string", "description": "The spending category (e.g., 'Hardware', 'Meals')."}
            },
            "required": ["user_id"]
        }
    },
    "required": ["step_number", "tool_name", "arguments"]
}

# This is the top-level schema passed to the Gemini API
PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "critique": {
            "type": "string",
            "description": "The Judge's evaluation of the plan's logic and completeness."
        },
        "plan_steps": {
            "type": "array",
            "description": "The list of sequential steps to be executed by the agent.",
            "items": PLAN_STEP_SCHEMA,
            "minItems": 1
        }
    },
    "required": ["critique", "plan_steps"]
}