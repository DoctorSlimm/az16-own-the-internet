from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain.prompts import PromptTemplate
from langchain.schema import AgentAction, AgentFinish, BaseOutputParser
from langchain_core.runnables import RunnablePassthrough
from typing import List, Union, Any, Dict
import re
from pydantic import BaseModel, Field
import json
from tools.llm import gpt3, gpt4
from tools.scrapingbee_tool import UrlDocumentLoader
from tools.bing_tool import search_bing
from tools.logger import logger

# Define custom tools
def internet_search(query: str) -> str:
    results = search_bing(query, top_n=3)
    return json.dumps([{"title": doc.metadata['title'], "snippet": doc.page_content, "url": doc.metadata['link']} for doc in results])

def web_scraper(url: str) -> str:
    loader = UrlDocumentLoader(url=url)
    loader.load()
    return loader.content if loader.success else "Failed to load content"

tools = [
    Tool(
        name="internet_search",
        func=internet_search,
        description="Useful for searching the internet to find information on a topic"
    ),
    Tool(
        name="web_scraper",
        func=web_scraper,
        description="Useful for scraping web pages and extracting their content"
    )
]

# Update the prompt template
prompt = PromptTemplate(
    template="""You are an AI assistant tasked with identifying stack requirements from a product description.

Available tools:
{tools}

Use the following format:
Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Question: {input}
{agent_scratchpad}""",
    input_variables=["input", "intermediate_steps", "tools", "tool_names", "agent_scratchpad"]
)

# Update the output parser
class CustomOutputParser(BaseOutputParser):
    def parse(self, llm_output: str) -> Union[AgentAction, AgentFinish]:
        if "Final Answer:" in llm_output:
            return AgentFinish(
                return_values={"output": llm_output.split("Final Answer:")[-1].strip()},
                log=llm_output,
            )
        
        action_match = re.search(r"Action: (\w+)", llm_output, re.DOTALL)
        action_input_match = re.search(r"Action Input: (.*)", llm_output, re.DOTALL)
        
        if not action_match or not action_input_match:
            raise ValueError(f"Could not parse LLM output: `{llm_output}`")
        
        action = action_match.group(1)
        action_input = action_input_match.group(1)
        return AgentAction(tool=action, tool_input=action_input.strip(" ").strip('"'), log=llm_output)

# Set up the agent using the new method
agent = create_react_agent(llm=gpt3, tools=tools, prompt=prompt)

# Create the AgentExecutor
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True
)

# Function to run the agent
def identify_stack_requirements(product_description: str) -> List[str]:
    logger.info(f"Identifying stack requirements for: {product_description}")
    result = agent_executor.invoke({"input": product_description})
    # Assuming the result is a comma-separated list of stack requirements
    requirements = [req.strip() for req in result['output'].split(",")]
    logger.info(f"Identified stack requirements: {requirements}")
    return requirements

# Example usage
if __name__ == "__main__":
    product_description = "We need a web application for real-time chat with video calling capabilities, supporting multiple users in a single room."
    stack_requirements = identify_stack_requirements(product_description)
    print("Stack Requirements:", stack_requirements)