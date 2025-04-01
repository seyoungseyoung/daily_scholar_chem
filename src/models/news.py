from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class News:
    title: str
    url: str
    author: str = None
    abstract: str = None
    created_at: datetime = None
    categories: List[str] = None
    pdf_url: Optional[str] = None
    html_url: Optional[str] = None
    source_url: Optional[str] = None
