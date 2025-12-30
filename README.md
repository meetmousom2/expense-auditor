# 🛡️ Expense Auditor AI Agent

A local, privacy-first AI agent designed to automate financial auditing. This system uses a **Plan-Reflect-Execute** architecture to process natural language expense reports, validate them against budget rules, and update a local database—all running entirely on your own hardware using **Ollama** and **DeepSeek-R1**.

---

## 🚀 The Architecture: Plan-Reflect-Execute

Unlike standard chatbots, this agent follows a structured four-phase reasoning cycle to ensure accuracy and adherence to financial rules:

1.  **Phase 1: Planning** – The **Planner Agent** (DeepSeek-R1) analyzes the user input and generates a sequence of tool calls (e.g., `log_expense`, `check_budget`).
2.  **Phase 2: Reflection** – The **Judge Agent** reviews the plan. It enforces critical business logic, such as ensuring a budget check always follows an expense entry.
3.  **Phase 3: Execution** – The **Executor** runs the validated steps against a local SQLAlchemy database.
4.  **Phase 4: Summarization** – The **Summarizer** parses the raw execution history and generates a professional audit report for the user.



---

## 🛠️ Prerequisites

- **Python 3.10+**
- **Ollama** ([Download for Mac](https://ollama.com/download))
- **Hardware:** 16GB+ RAM is recommended for the 14B model; 8GB is sufficient for the 8B model.

---

## ⚙️ Setup & Installation

### 1. Initialize the Environment
Clone the repository and set up a Python virtual environment:

```bash
# Create and activate venv
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install ollama sqlalchemy
```

### 2. Prepare the Local Models
Pull the DeepSeek reasoning models via Ollama. It is recommended to use the **14B** model for high-accuracy planning and the **8B** model for fast summarization.

```bash
ollama pull deepseek-r1:14b
ollama pull deepseek-r1:8b
```

---

## 🖥️ Running the Server & Agent

### Start Ollama in Debug Mode
To see the agent's **internal thought process** (reasoning tokens) in real-time, quit the Ollama desktop app and run it via terminal with the debug flag:

```bash
OLLAMA_DEBUG=1 ollama serve
```

### Run the Auditor
Open a new terminal tab, ensure your virtual environment is active, and execute the main orchestrator:

```bash
python main.py
```

---

## 📁 Project Structure

- `main.py`: The entry point that manages the 4-phase audit loop.
- `planner.py`: Contains the **Planner** and **Judge** logic for step generation and reflection.
- `executor.py`: Handles tool execution and database interactions.
- `tools.py`: Definitions for `log_expense_tool` and `check_budget_tool`.
- `client_config.py`: Centralized config for Ollama model selection and API settings.

---

## 🛡️ Privacy & Security

- **100% Local:** No data is sent to external clouds (OpenAI, Google, etc.). All processing happens on your CPU/GPU.
- **Context Cleaning:** The system automatically strips database engine objects and sensitive connection strings before passing data to the LLM for summarization. This prevents serialization errors and ensures the model only sees the necessary audit data.
