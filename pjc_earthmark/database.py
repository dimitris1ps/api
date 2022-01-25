from sqlmodel import SQLModel, create_engine
import os

# Get current file directory, and create sqlite url
BASE_DIR = os.path.dirname(os.path.realpath("__file__"))
SQLITE_DB_URL = f"sqlite:///{BASE_DIR}/earthmark.db"

# Create database if it does not exist, else connect to it
engine = create_engine(SQLITE_DB_URL, connect_args={"check_same_thread": False}, echo=False)
