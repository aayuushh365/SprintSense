from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class Issue(BaseModel):
    issue_id: str
    issue_type: str
    status: str
    story_points: Optional[float] = Field(default=None, ge=0)
    assignee: Optional[str] = None
    reporter: Optional[str] = None
    created: datetime
    updated: Optional[datetime] = None
    resolved: Optional[datetime] = None
    sprint_id: Optional[str] = None
    sprint_name: Optional[str] = None
    sprint_start: Optional[datetime] = None
    sprint_end: Optional[datetime] = None
    parent_id: Optional[str] = None
    labels: Optional[str] = None
    priority: Optional[str] = None

CSV_HEADERS = [
    "issue_id","issue_type","status","story_points","assignee","reporter",
    "created","updated","resolved","sprint_id","sprint_name","sprint_start",
    "sprint_end","parent_id","labels","priority"
]