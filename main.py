from typing import List, Dict
from pydantic import BaseModel


class ResponseIO(BaseModel):
    metrics: Dict[str, int]
    contacts: List[Dict]
    companies: List[Dict]


class RunIO(BaseModel):

    """User input."""
    query: str

    """Search module output."""
    search_terms: str

    """Load module output."""
    contacts: List[Dict] = []                   # accounts.
    documents: List[Dict] = []                  # issues.

    """Labelling module output."""
    document_labels: List[Dict] = []            # has id?


    """Runtime output..."""








# gradio frontend / fastapi