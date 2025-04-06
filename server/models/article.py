from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import List, Optional

class Article(BaseModel):
    title: str
    description: str
    content: str
    publish_date: datetime
    category: List[str]
    link: HttpUrl
    sentiment: Optional[str] = None