# agent/tools.py
from sqlmodel import select
from .db import Expense, Budget, get_db_engine, Session, engine
from typing import Optional

# ----------------------------------------------------
# 1. CORE Tool Functions (Private, accepts all args: user_id, db_engine)
# ----------------------------------------------------

def _log_expense_core(user_id: str, vendor: str, amount: float, category: str, db_engine=engine):
    """Core logic: Logs a new expense to the database."""
    with Session(db_engine) as session:
        expense = Expense(user_id=user_id, vendor=vendor, amount=amount, category=category)
        session.add(expense)
        session.commit()
        session.refresh(expense)
        return f"Successfully logged expense ID {expense.id} for ${amount} at {vendor}. Now checking budget."

def _check_budget_core(user_id: str, category: str, db_engine=engine):
    """Core logic: Checks the total spending for a given category against the user's limit."""
    with Session(db_engine) as session:
        # 1. Get the budget limit
        budget_statement = select(Budget).where(Budget.user_id == user_id, Budget.category == category)
        budget = session.exec(budget_statement).first()
        limit = budget.limit if budget else 0.0 
        
        # 2. Calculate current total spent
        expense_statement = select(Expense.amount).where(Expense.user_id == user_id, Expense.category == category)
        total_spent = sum(session.exec(expense_statement).all())
        
        status = "Under Budget"
        if total_spent > limit:
            status = "OVER BUDGET"
        
        return {
            "category": category, 
            "total_spent": total_spent, 
            "limit": limit, 
            "status": status,
            "message": f"Total spent on {category} is ${total_spent}. Limit is ${limit}. Status: {status}."
        }

# ----------------------------------------------------
# 2. PUBLIC Wrapper Functions (Signatures for Gemini to see)
# ----------------------------------------------------
def say_hello_tool():
    """Prints a message and requires no input parameters."""
    return "Hello World! The agent successfully called the tool."

def log_expense_tool(vendor: str, amount: float, category: str): # Removed -> str
    """Logs a new expense (amount, vendor, category) to the database for tracking. Category is required."""
    # This is the SCHEMA blueprint for Gemini.
    return "" 

def check_budget_tool(category: str): # Removed -> dict
    """Checks the current spending against the budget limit for a specific category."""
    # This is the SCHEMA blueprint for Gemini.
    return {}

