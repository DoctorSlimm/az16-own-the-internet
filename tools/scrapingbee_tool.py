import re
import os
import json
from copy import deepcopy

from pydantic import BaseModel
from typing import List, Optional

from bs4 import BeautifulSoup
from scrapingbee import ScrapingBeeClient
from urllib.parse import urlparse, urlunparse, quote, urljoin
from langchain_community.document_transformers import MarkdownifyTransformer

from tools.llm import gpt4


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

    nested_links: List[str] = []
    nested_social_links: List[str] = []     #... ermmm ok

    nested_image_urls: List[str] = []


    @classmethod
    def from_html_and_base_url(cls, html, base_url):

        soup = BeautifulSoup(html, 'lxml')

        title = soup.find('title')
        if title: title = soup.find('title').text
        else: title = None

        description = soup.find("meta", attrs={"name": "description"})
        if description: description = description.get("content", "none")
        else: description = None

        # can also load from google search thumbnail or google images
        icon = soup.find("link", rel=lambda value: value and "icon" in value.lower())
        if icon: icon = icon.get("href")
        else: icon = None

        # links
        nested_links = extract_nested_links_from_html(html, base_url)

        # specific social links
        nested_social_links = filter_social_links(nested_links)

        # image urls
        nested_image_urls = extract_image_urls_from_html(html)
        nested_image_urls = list(set(nested_image_urls)) or []

        return cls(
            icon=icon,
            title=title,
            description=description,
            nested_links=nested_links,
            nested_social_links=nested_social_links,
            nested_image_urls=nested_image_urls
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
    content = md_transformer.transform_documents([LangchainDocument(html)])[0].page_content


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



def scrapingbee_url_loader(url: str):
    """Loads the page input url to markdown text for page reading"""

    html = load_html_content(url) # headers... clasify redirector ir bad...
    if html is None: return None

    metadata = UrlDocumentMetadata.from_html_and_base_url(html, url)
    page_content = convert_html_to_markdown_content(html)
    return Document(page_content, metadata=dict(






class UrlDocumentLoader(BaseModel):
    """status"""
    success: bool = False

    """deprecated"""
    icon: str = None
    link: str = None
    document: Document = None
    metadata: Optional[UrlDocumentMetadata] = None

    """latest"""
    url: str = None

    links: List[str] = []               # 
    images: List[str] = []              # 
    socials: List[str] = []             # could just extract and filetr at thend...

    html: Optional[str] = None
    content: Optional[str] = None

    summary: Optional[str] = None


    def lalaload(self):
        """load and summarize the document."""

        self.html = load_html_content(self.url) # headers... clasify redirector ir bad...
        if self.html is None: return

        # extract icon, title, description, links, socials, images
        self.metadata = UrlDocumentMetadata.from_html_and_base_url(self.html, self.url)

        # update links (extract nested links from html metadata)
        self.icon = self.metadata.icon
        self.links += self.metadata.nested_links
        self.images += self.metadata.nested_image_urls

        # html -> markdown
        self.content = convert_html_to_markdown_content(self.html)

        # update links (extract nested links from markdown content)
        self.links += extract_nested_links_from_markdown(self.content)

        # update markdown content (remove nested links)
        self.content = remove_nested_links_from_markdown(self.content)

        # filter socials
        self.socials = filter_social_links(self.links)


        ## classify document as wether valid or invalid
        # >> proxy by (status code error. see more... parked domains etc.)

        ## summarize document... if too short warning???
        self.summary = summarize(self.content)
        if len(self.summary.split()) < 100:
            logger.warning(f'warning: summary is short {self.url}.')
            logger.warning(f'summary: {self.summary}')

        ### Backwards compatibility
        self.document = Document(
            self.summary,
            metadata=dict(
                link_or_filename=self.link,
                source_of_page_content='website',
                encoded=json.dumps(self.metadata.model_dump())
            )
        )

        ### update success status
        self.success = True

    def load(self):

        try:
            self.lalaload() # if this was cmopatible with .load() would be fine..?
        
        except Exception as e:
            logger.error(f'error loading document: {e}')
            self.success = False

    def summarize(self):
        if self.document is None:
            return None
        
        content = 'Summarize the web page content (Note if the web page if 404 or some other domain error or captch or login please return FAILED_TO_LOAD in capitals.):\n\n===Content' + self.document.page_content

        try:
            while len(tokenizers.tiktokenize(content)) > 2048:
                content = content[:len(content)//2]

            completion = gpt4.invoke(content).content
            if 'FAILED_TO_LOAD' in completion:
                self.document = None
                raise Exception('FAILED_TO_LOAD')

            self.document.page_content = completion

        except Exception as e:
            tokens = tokenizers.tiktokenize(content)
            logger.error(e)
            logger.error(f"Failed to summarize {self.document.metadata.link_or_filename}. with {len(tokens)} tokens.")

        return deepcopy(self.document)


    