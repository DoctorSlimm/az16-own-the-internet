from pydantic import BaseModel
from langchain_core.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain.output_parsers import RetryOutputParser

### Extract any structured model from content.
# https://python.langchain.com/v0.1/docs/modules/model_io/output_parsers/types/retry/

### --- usage ---
#
#     from typing import List
#     from pydantic import BaseModel, Field
#
#
#     class Organization(BaseModel):
#         """Identify a named company, project or organization."""
#
#         name: str = Field(description="The name of the organization.")
#
#         location: str = Field(description="The location of the organization in ISO-3166-1 alpha-2 format.")
#
#         members: List[str] = Field(description="The list of members in the organization.") 
#    
#       
#     content = """Bluecorp was founded in arizona by james franco at the same time as alphabet"""
#
#
#     extracted: Organization = model_from_content(Organization, content, llm)
#
### --- output ---
#     >> extracted
#     >> is an instance of Organization Model with the extracted Typed fields.



template = """Please extract the information from the content provided \
following the format:
{format_instructions}


===Content:
{content}


===Output:"""


def invoke_chain_with_inputs(prompt, llm, parser, inputs):
    chain = prompt | llm | parser
    output = chain.invoke(inputs)
    return output


def extract_model_from_content(model: BaseModel, content: str, llm, retry=False):
    '''Extract any structured pydantic model with typed definitions and fields.'''

    parser = PydanticOutputParser(pydantic_object=model)

    prompt = PromptTemplate(
        template=template,
        input_variables=["content"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )


    # invoke the default chain

    if not retry:

        extracted = invoke_chain_with_inputs(prompt, llm, parser, {"content": content})

        return extracted
    

    # invoke the retry chain (forces to try again if fails)

    retry_parser = RetryOutputParser.from_llm(parser=parser, llm=llm, max_retries=3)

    prompt_value = prompt.format_prompt(content=content)

    extracted = retry_parser.parse_with_prompt(content, prompt_value)

    return extracted