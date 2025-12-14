# agent/db.py
from sqlmodel import create_engine, SQLModel, Field, Session
from typing import Optional

# 1. Define Models
class Expense(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str
    vendor: str
    amount: float
    category: str
    is_flagged: bool = Field(default=False)

class Budget(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(unique=True) # Unique per user/category (for PoC)
    limit: float
    category: str

# 2. Engine Creation Function
def get_db_engine(engine_url: str = None):
    """
    Creates the database engine. Uses :memory: for testing if specified.
    """
    if engine_url is None:
        # Default for the main application (persistent file)
        sqlite_file_name = "poc_main.db"
        engine_url = f"sqlite:///{sqlite_file_name}"
        
    engine = create_engine(
        engine_url, 
        connect_args={"check_same_thread": False} # Required for SQLite with FastAPI
    )
    SQLModel.metadata.create_all(engine)
    return engine

# The global engine used by the main application
engine = get_db_engine()
