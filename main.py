# main.py
import uvicorn
from fastapi import FastAPI
from dotenv import load_dotenv
from pydantic import BaseModel
from agent.agent_core import run_auditor
import os

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="Expense Auditor Agent")

class ExpenseRequest(BaseModel):
    user_id: str
    expense_text: str

@app.get("/")
def read_root():
    return {"message": "Expense Auditor Agent is running."}

@app.post("/process_expense")
def process_expense(data: ExpenseRequest):
    """Endpoint to process an expense via the Gemini Agent."""
    if not os.getenv("GEMINI_API_KEY"):
        return {"error": "GEMINI_API_KEY not found. Check your .env file."}
        
    report = run_auditor(data.user_id, data.expense_text)
    
    # Note: run_auditor uses the default (persistent) engine when called here.
    return report

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
