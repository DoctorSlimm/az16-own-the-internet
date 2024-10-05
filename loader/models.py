from typing import List
from pydantic import BaseModel
from langchain_core.documents import Document


class Timeline(BaseModel):

    url: str

    title: str

    labels: List[str]

    caption: str

    timestamp: str


class Contact(BaseModel):

    url: str

    title: str

    caption: str = None

    labels: List[str] = []

    company: str = None

    location: str = None

    confidence: float = 0.0

    timeline: List[Timeline] = []

    documents: List[Document] = []
