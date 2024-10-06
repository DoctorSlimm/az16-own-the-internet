import os
from typing import Dict
from pydantic import BaseModel
from dotenv import load_dotenv, find_dotenv


class Settings(BaseModel):

    """Access Token Header"""
    x_api_key: str = os.environ['ACCESS_TOKEN']
    
    """Ratelimiting for all routes (slowapi)"""
    ratelimit: str = '300/minute'

    """Middleware. TODO: add allowed retool hosts."""
    cors_args: Dict = dict(allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

    """FastApi Initialization."""
    init_args: Dict = dict(docs_url=None, redoc_url=None, openapi_url=None) 


settings = Settings()