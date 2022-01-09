from sqlmodel import SQLModel, Field
from typing import Optional

class Ratings(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    company: str
    business_info_score: float
    environment_score: float
    governance_transparency_score: float
    earthmark_rating: float
    create_date: str

class Tokens(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    client: str
    token: str
    package: str
    email: Optional[str] = None
    contact_person: Optional[str] = None
    create_date: str

class Statistics(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    client: str
    api_calls: int
    company_calls: int
    report_date: str
    report_month: str
