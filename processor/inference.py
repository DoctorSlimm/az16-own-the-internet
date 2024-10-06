from typing import List
from pydantic import BaseModel, Field

from tools.logger import _logger
from tools.llm import gpt4, gpt3

from tools.extractor import extract_model_from_content

logger = _logger('processing.inference')


### Default
PRODUCT_DESCRIPTION = "a developer-first blockchain devtools"


### Extract template.
class GeneratedDeveloperCaption(BaseModel):
    """A single sentence to put in the CRM or database about the developer."""

    caption: str = Field(description="A few words about the developer.")


### Analysis Template.
template = """You are a sales agent / developer community and growth manager \
working in a company specializing in {product_description}.

Please consider the developer profile and all context provided \
to write a one line caption of the sinlge most important thing about this developer. \
Considering what is most important about their activity to your business model. \
Please respond in the format below:
ANALYSIS: few sentences about what makes the developer important or problematic / unprofitable to your business.
CAPTION: a single sentence to put in the CRM or database about the developer.


===Developer Information:
{developer_info}


===Response:"""



def generate_caption_for_account(developer_info: str, product_description: str = PRODUCT_DESCRIPTION, llm = gpt3) -> List[str]:

    try:


        # Generate a caption for the developer.
        analysis_prompt = template.format(
            product_description=product_description,
            developer_info=developer_info
        )

        analysis = gpt3.invoke(analysis_prompt).content


        # Extract the caption from the analysis.
        generated_caption = extract_model_from_content(
            GeneratedDeveloperCaption,
            content=analysis,
            llm=gpt4
        ).caption

        return generated_caption
    
    except Exception as e:
        logger.error(f"Error generating labels: {e}")
        return None # compatible with datasets...?
