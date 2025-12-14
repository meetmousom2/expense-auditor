# agent/agent_core.py
import pprint
from google import genai
from google.genai import types
from .tools import _log_expense_core, _check_budget_core, log_expense_tool, check_budget_tool, say_hello_tool
import os
import json 

# ----------------------------------------------------
# 1. Debug Helper (The corrected _debug_print_response function)
# ----------------------------------------------------
def _debug_print_response(response, step_name):
    """
    Prints the entire contents of the GenerateContentResponse object
    by converting it to a dictionary first, using pprint for readability.
    """
    print(f"\n--- DEBUG: Gemini Response ({step_name}) ---")

    try:
        # Convert the complex object to a standard Python dictionary
        # response_dict = response.to_dict()

        # Use pprint to print the dictionary in a structured, readable format
        pprint.pprint(response.to_dict(), indent=4, width=100)

    except AttributeError:
        # Fallback if .to_dict() is unavailable or the object is unexpected
        print("Error: Could not convert response to dict. Printing raw object string:")
        print(str(response))

    print("-------------------------------------------\n")


# ----------------------------------------------------
# 2. Agent Configuration
# ----------------------------------------------------

# SYSTEM_PROMPT = """
# You are a simple function caller. Your only task is to acknowledge the user's message
# and immediately call the 'say_hello_tool'.
# After receiving the result from the tool, state the result in your final output.
# """

SYSTEM_PROMPT = """
You are a specialized Financial Auditor. Your primary categories are: [Hardware, Meals, Software, Travel]. 
Your goal is to process expense reports and enforce budget compliance. You MUST adhere to the following steps for every user message:
1. Extract the Vendor, exact Amount, and a Category from the list [Hardware, Meals, Software, Travel] from the expense text.
2. Call the 'log_expense_tool' to record the transaction.
3. Immediately call the 'check_budget_tool' for the extracted category to determine the budget status. If a category was NOT extracted in step 1, use 'Uncategorized' for the check.
4. CRITICAL: After the final tool call result is returned, you MUST generate a final, 
   concise, and professional report. The report MUST explicitly state the budget limit, 
   the new total spent, and the budget status (e.g., 'Warning: OVER BUDGET by $20').
"""

# Initialize the client globally
try:
    CLIENT = genai.Client(api_key=os.getenv("GEMINI_API_KEY")) 
except Exception as e:
    # Handle the case where the key is not set
    print(f"Warning: Client failed to initialize at top level: {e}")
    CLIENT = None

# Tool Registry maps the NAME Gemini requests to the PRIVATE CORE function
TOOL_REGISTRY = {
    "say_hello_tool": say_hello_tool,
    "log_expense_tool": _log_expense_core,
    "check_budget_tool": _check_budget_core,
}
if CLIENT:
    LOG_EXPENSE_DECLARATION = types.FunctionDeclaration.from_callable(
        callable=log_expense_tool,
        client=CLIENT
    )

    CHECK_BUDGET_DECLARATION = types.FunctionDeclaration.from_callable(
        callable=check_budget_tool,
        client=CLIENT
    )

    SAY_HELLO_DECLARATION = types.FunctionDeclaration.from_callable(
        callable=say_hello_tool,
        client=CLIENT
    )

    AVAILABLE_TOOLS = [
        types.Tool(function_declarations=[
            SAY_HELLO_DECLARATION,
            LOG_EXPENSE_DECLARATION,
            CHECK_BUDGET_DECLARATION
        ]),
    ]

    print("\n--- DEBUG: Final Tool Structure Sent to Gemini ---")
    pprint.pprint([t for t in AVAILABLE_TOOLS], indent=4)
    print("----------------------------------------------------\n")
else:
    # If client fails to initialize, use empty declarations to avoid crash
    AVAILABLE_TOOLS = []

# ----------------------------------------------------
# 4. Main Execution Function
# ----------------------------------------------------

def run_auditor(user_id: str, expense_text: str, test_engine=None):
    client = CLIENT # Use the global client
    if not client:
        return {"final_report": "Agent Error: Gemini client was not initialized.", "full_history": []}
    # expense_text = "Please initiate the test tool call."

    model_name = "gemini-2.5-flash-lite"
    
    history = [
        types.Content(role="user", parts=[types.Part.from_text(text=expense_text)])
    ]
    
    response = client.models.generate_content(
        model=model_name,
        contents=history,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=AVAILABLE_TOOLS,
        )
    )

    _debug_print_response(response, "Initial Response")

    # 5. The ReAct Loop (Handles multiple tool calls)
    while response.function_calls:
        tool_responses = []
        for call in response.function_calls:
            func_name = call.name
            
            # Arguments extracted by Gemini (vendor, amount, category)
            gemini_args = dict(call.args) 
            
            # Arguments for the CORE function (includes environment-supplied args)
            core_args = gemini_args.copy() 
            core_args['user_id'] = user_id # INJECT the required user_id
            if test_engine:
                core_args['db_engine'] = test_engine # INJECT the required db_engine
            
            # Execute the core function
            if func_name in TOOL_REGISTRY:
                tool_function = TOOL_REGISTRY[func_name]
                print(f"-> Calling Tool: {func_name}({core_args})")
                
                try:
                    tool_result = tool_function(**core_args)
                except Exception as e:
                    tool_result = f"Tool Execution Error in {func_name}: {e}"
                
                print(f"<- Tool Result: {tool_result}")
                
                tool_responses.append(
                    types.Part.from_function_response(
                        name=func_name,
                        response={"result": tool_result}
                    )
                )

        # Add function call request and tool response to history
        history.append(response.candidates[0].content)
        history.append(types.Content(role="tool", parts=tool_responses))
        
        # Send back to Gemini for the next step
        response = client.models.generate_content(
            model=model_name,
            contents=history,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=AVAILABLE_TOOLS
            )
        )
        _debug_print_response(response, "Intermediate Response")
    
    # 5. Return the Final Report (Robust Check)
    final_text = response.text
    
    if final_text is None or final_text.strip() == "":
        return {
            "final_report": "Agent Error: The model failed to generate a final summary text after tool execution. Check history for tool results.", 
            "full_history": history
        }

    return {"final_report": final_text, "full_history": history}
