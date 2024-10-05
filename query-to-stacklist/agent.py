from langchain.agents import Tool, AgentExecutor, LLMSingleActionAgent
from langchain.prompts import StringPromptTemplate
from langchain import LLMChain
from langchain.schema import AgentAction, AgentFinish
from typing import List, Union
import re
from pydantic import BaseModel, Field

from tools.llm import gpt3, gpt4
from tools.scrapingbee_tool import UrlDocumentLoader

# Define custom tools
class InternetSearchTool(BaseModel):
    name: str = Field(default="internet_search")
    description: str = Field(default="Useful for searching the internet to find information on a topic")

    def run(self, query: str) -> str:
        # Implement internet search using Azure Bing Search API
        # Return results as JSON string
        pass

class WebScraperTool(BaseModel):
    name: str = Field(default="web_scraper")
    description: str = Field(default="Useful for scraping web pages and extracting their content")

    def run(self, url: str) -> str:
        loader = UrlDocumentLoader(url=url)
        loader.load()
        return loader.content if loader.success else "Failed to load content"

# Define the prompt template
class CustomPromptTemplate(StringPromptTemplate):
    template: str
    tools: List[Tool]

    def format(self, **kwargs) -> str:
        intermediate_steps = kwargs.pop("intermediate_steps")
        thoughts = ""
        for action, observation in intermediate_steps:
            thoughts += action.log
            thoughts += f"\nObservation: {observation}\nThought: "
        kwargs["agent_scratchpad"] = thoughts
        kwargs["tools"] = "\n".join([f"{tool.name}: {tool.description}" for tool in self.tools])
        kwargs["tool_names"] = ", ".join([tool.name for tool in self.tools])
        return self.template.format(**kwargs)

prompt = CustomPromptTemplate(
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
    tools=[InternetSearchTool(), WebScraperTool()]
)

# Define output parser
class CustomOutputParser:
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

# Set up the agent
tools = [InternetSearchTool(), WebScraperTool()]

llm_chain = LLMChain(llm=gpt3, prompt=prompt)
agent = LLMSingleActionAgent(
    llm_chain=llm_chain,
    output_parser=CustomOutputParser(),
    stop=["\nObservation:"],
    allowed_tools=[tool.name for tool in tools]
)

agent_executor = AgentExecutor.from_agent_and_tools(agent=agent, tools=tools, verbose=True)

# Function to run the agent
def identify_stack_requirements(product_description: str) -> List[str]:
    result = agent_executor.run(product_description)
    # Assuming the result is a comma-separated list of stack requirements
    return [req.strip() for req in result.split(",")]

# Example usage
product_description = "We need a web application for real-time chat with video calling capabilities, supporting multiple users in a single room."
stack_requirements = identify_stack_requirements(product_description)
print("Stack Requirements:", stack_requirements)