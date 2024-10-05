import os
from pydantic import BaseModel
from typing import List, Optional
from langchain_core.documents import Document

from bs4 import BeautifulSoup
from scrapingbee import ScrapingBeeClient

from urllib.parse import urlparse, urlunparse, quote
from langchain_community.document_transformers import MarkdownifyTransformer

from tools.llm import gpt4
from tools.logger import _logger


logger = _logger('url_document_loader')




client = ScrapingBeeClient(os.environ['SCRAPINGBEE_API_KEY'])
params = {"render_js": "True"} # works... , "wait": "1000", "timeout": "1500", "premium_proxy": "True" }
logger.info(f'scrapingbee client params: {params}')


class UrlDocumentMetadata(BaseModel):
    """additional info we get from the url document to display...
        source_of_page_content: Literal['website']
        source_of_page_content: str = 'website'
    """

    icon: Optional[str] = None              # Allows None for this field as input
    title: Optional[str] = None             # Allows None for this field as input
    description: Optional[str] = None       # Allows None for this field

    # nested_links: List[str] = []
    # nested_social_links: List[str] = []     #... ermmm ok
    # nested_image_urls: List[str] = []

    @classmethod
    def from_html_and_base_url(cls, html, base_url):

        soup = BeautifulSoup(html, 'lxml')

        title = soup.find('title')
        if title: title = soup.find('title').text
        else: title = None

        description = soup.find("meta", attrs={"name": "description"})
        if description: description = description.get("content", "none")
        else: description = None

        return cls(
            title=title,
            description=description,
            ### Unused... (might be useful if repose mentionde on page)
            # nested_links=nested_links,
            # nested_social_links=nested_social_links,
            # nested_image_urls=nested_image_urls
        )


def encode_url(url) -> str:
    """encode url for scrapingbee."""

    parsed_url = urlparse(url)
    encoded_path = quote(parsed_url.path)
    encoded_query = quote(parsed_url.query)
    return urlunparse((parsed_url.scheme, parsed_url.netloc, encoded_path, parsed_url.params, encoded_query, parsed_url.fragment))


def load_html_content(url) -> str:
    """load html string from url using scrapingbee."""

    try:
        url = encode_url(url)      
        response = client.get(url, params=params)
        response.raise_for_status()
        if response is None: raise Exception('scrapingbee no response')
        assert response.status_code == 200, f'scrapingbee status code: {response.status_code}'
        return response.text
    
    except Exception as e:
        logger.error(f'error loading html: {e}')
        return None



def convert_html_to_markdown_content(html) -> str:
    """convert html content to markdown content."""

    md_transformer = MarkdownifyTransformer(
        autolinks=True,             # Ensure that automatic link style is used
        heading_style='ATX'         # Use 'ATX' style headings
    )
    content = md_transformer.transform_documents([Document(html)])[0].page_content

    ### unstructured is Too much RAM
    # content = clean_with_unstructured(content,
    #     dashes = True,
    #     bullets = True,
    #     lowercase = False,
    #     trailing_punctuation = True,
    #     extra_whitespace = True,
    # )  
    lines = content.split('\n')
    lines = [l.strip() for l in lines]
    lines = [line for line in lines if not line.startswith('![')]

    valid_line = lambda l: len([w for w in l.split(' ')]) > 3

    lines = [line for line in lines if valid_line(line)]
    content = '\n'.join(lines)
    return content



def load_page_for_url(url: str):
    """Loads the page input url to markdown text for page reading"""

    html = load_html_content(url) # headers... clasify redirector ir bad...
    if html is None: return None

    metadata = UrlDocumentMetadata.from_html_and_base_url(html, url)
    metadata = dict(
        url=url,
        title=metadata.title,
        description=metadata.description,
    )
    page_content = convert_html_to_markdown_content(html)
    return Document(page_content, metadata=metadata)