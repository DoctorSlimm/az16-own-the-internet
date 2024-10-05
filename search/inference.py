from typing import List
from pydantic import BaseModel, Field



from tools.llm import gpt4

from search.agent import agent_executor

from tools.extractor import extract_model_from_content




class StackRequirements(BaseModel):
    """Identify core stack and framework requirements for a product description"""

    frameworks: List[str] = Field(description="list of framework or sdk names")


def identify_requirements(product_description: str) -> StackRequirements:
    """Load the stack requirements for a given product description."""

    product_description = f"""{product_description}

--- additional notes ---
* Prioritize popular open source frameworks.
* Please return no more than 7 stack requirements or alternative solutions.
"""

    # run analysis
    
    output = agent_executor.invoke({"input": product_description})
    analysis = output['output']


    # extract stack requirements from analysis

    stack_requirements = extract_model_from_content(
        StackRequirements,
        content=analysis,
        llm=gpt4
    )

    return stack_requirements