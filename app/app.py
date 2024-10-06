from typing import Dict, List
from pydantic import BaseModel

### FastAPI
from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from fastapi.encoders import jsonable_encoder

### Middleware
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware


## Custom Imports

from tools.logger import _logger
from app.settings import settings



## Logger
logger = _logger('app')



## Authorization

api_key_header = APIKeyHeader(name="x-api-key")

async def get_x_api_key_header(x_api_key: str = Security(api_key_header)):
    if x_api_key == settings.x_api_key: return None
    raise HTTPException(status_code=401, detail="Unauthorized.") 



## Middleware

def add_middleware(app: FastAPI, ratelimit: str, cors_config: Dict):

    # CORS
    app.add_middleware(CORSMiddleware, **cors_config)

    # Rate limiting
    limiter = Limiter(key_func=get_remote_address, default_limits=[ratelimit])
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)



## FastAPI App

app = FastAPI(dependencies=[Depends(get_x_api_key_header)], **settings.init_args)
add_middleware(app, settings.ratelimit, settings.cors_args)



## Routes
from inference import inference_fn, Contact

class RequestSchema(BaseModel):
    query: str = None

class DisplayCardSchema(BaseModel):
    confidence: float = 0.0

    displayName: str = None
    profileImage: str = None
    githubProfileUrl: str = None

    followerCount: int = 0          # not informative.
    issueResponseCount: int = 0     # not infiormative.

    location: str = None
    company: str = None

    labels: List[str] = []         # top 3 labels

    timeline: List[Dict] = []      # {url, title, caption}


class ResponseSchema(BaseModel):

    data: List[DisplayCardSchema] = []

    metrics: Dict = {}


def contact_to_display_data(contact: Contact) -> DisplayCardSchema:

    confidence = contact.confidence
    displayName = contact.title
    profileImage = f'{contact.url}.png'
    labels = contact.labels

    location = contact.caption

    company = contact.caption

    # ['url', 'title', 'creator', 'created_at', 'comments', 'state', 'labels', 'assignee', 'milestone', 'locked', 'number', 'is_pull_request']
    timeline = contact.timeline 

    return DisplayCardSchema(
        confidence=confidence,
        displayName=displayName,
        profileImage=profileImage,
        labels=labels,
        timeline=timeline,

        location=location,
        company=company
    )





@app.post('/inference')
def api_inference_fn(req: RequestSchema):
    """Run inference and return top contacts and metrics"""

    logger.info(f"Received request: {req.query}")

    out = inference_fn(req.query, verbose=True)
    metrics = out['metrics']

    contacts = out['data']

    diplay_data = [contact_to_display_data(contact) for contact in contacts]

    response = ResponseSchema(metrics=metrics, data=diplay_data)

    return jsonable_encoder(response)


### Start Application.
for route in app.routes:
    logger.info(route.path)
logger.info(f'FastApi App configured with {len(app.routes)} endpoints.')