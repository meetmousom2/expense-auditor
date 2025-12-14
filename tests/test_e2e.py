# tests/test_e2e.py
import httpx
import json
import os
from agent.db import get_db_engine, Budget, Session
from agent.tools import log_expense_tool
from agent.agent_core import run_auditor  # We will call the agent directly for full control

# Load API key for local testing environment
from dotenv import load_dotenv

load_dotenv()


# --- Helper Functions (No Change) ---

def setup_test_db(engine, user_id, initial_state):
    """Initializes the in-memory database with required budget data."""
    # Create tables defined in the model (required for the in-memory engine)
    Budget.metadata.create_all(engine)

    with Session(engine) as session:
        # Create the budget limit
        budget = Budget(
            user_id=user_id,
            limit=initial_state['budget_limit'],
            category=initial_state['category']
        )
        session.add(budget)
        session.commit()

        # Log a pre-existing expense if needed
        if initial_state.get('pre_expense_amount') > 0:
            log_expense_tool(
                user_id=user_id,
                vendor="Previous Bills",
                amount=initial_state['pre_expense_amount'],
                category=initial_state['category'],
                db_engine=engine  # Pass the test engine!
            )


# --- Main E2E Runner (Modified) ---

def run_all_e2e_tests():
    print("--- Starting Idempotent E2E Test Suite ---")

    # Load test case data
    try:
        with open('tests/test_data.json', 'r') as f:
            test_cases = json.load(f)['tests']
    except FileNotFoundError:
        print("ERROR: tests/test_data.json not found. Cannot run tests.")
        return

    total_tests = len(test_cases)
    passed_count = 0

    # LOOP THROUGH ALL TEST CASES
    for i, test_case in enumerate(test_cases):
        test_name = test_case.get('name', f"Test Case {i + 1}")
        print(f"\n=======================================================")
        print(f"▶️ RUNNING: {test_name}")
        print(f"=======================================================")

        # 1. Create the IN-MEMORY database engine
        # CRITICAL: This MUST be inside the loop to ensure a fresh, empty DB for each test.
        test_engine = get_db_engine(engine_url="sqlite:///:memory:")

        try:
            # 2. Populate the in-memory DB with the required initial state
            setup_test_db(test_engine, test_case['user_id'], test_case['initial_db_state'])
            print(f"DB initialized. Budget Limit for {test_case['initial_db_state']['category']}: ${test_case['initial_db_state']['budget_limit']}")

            # 3. Run the Agent Logic
            print(f"Sending Agent Input: {test_case['test_input']['expense_text']}")
            report = run_auditor(
                user_id=test_case['user_id'],
                expense_text=test_case['test_input']['expense_text'],
                test_engine=test_engine  # CRITICAL: Pass the in-memory engine
            )

            # 4. Assertions
            final_text = report.get('final_report', '')
            expected_fragment = test_case['expected_output_fragment']

            if expected_fragment in final_text:
                print(f"✅ PASS: {test_name}")
                print(f"   Expected fragment '{expected_fragment}' found.")
                passed_count += 1
            else:
                print(f"❌ FAIL: {test_name}")
                print(f"   Expected fragment '{expected_fragment}' NOT found.")
                print("--- Full Agent Report ---")
                print(final_text)

        except Exception as e:
            print(f"❌ ERROR: {test_name} failed due to an exception: {e}")

    # 5. Final Summary
    print(f"\n=======================================================")
    print(f"📋 TEST SUMMARY: {passed_count}/{total_tests} tests passed.")
    print(f"=======================================================")


if __name__ == "__main__":
    if not os.getenv("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY not set in .env file. Cannot run test.")
    else:
        # Note: You need to make sure 'Budget' has a .metadata.create_all() call
        # inside setup_test_db to properly initialize the in-memory tables.
        # I've added this to the helper function above.
        run_all_e2e_tests()