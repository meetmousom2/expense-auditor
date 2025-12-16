# client_config.py
import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

# --- MODEL CENTRALIZATION ---
# Using 2.0-flash-lite for all tasks to maximize Free Tier stability
PRIMARY_MODEL = "gemini-2.5-flash-lite"
PLANNER_MODEL = PRIMARY_MODEL
JUDGE_MODEL = PRIMARY_MODEL
SUMMARY_MODEL = PRIMARY_MODEL

# Initialize the global client
CLIENT = None
if os.getenv("GEMINI_API_KEY"):
    CLIENT = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
else:
    print("WARNING: GEMINI_API_KEY not found in environment.")