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
from itertools import chain
from nltk.corpus import stopwords
import nltk

# Download the stopwords data (you may want to do this in a setup script)
nltk.download('stopwords', quiet=True)

# Define custom tools
def internet_search(query: str) -> str:
    results = search_bing(query, top_n=15)  # Increase the number of results
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
    template="""Identify specific stack requirements from the product description. Focus on specialized SDKs, providers, technologies, frameworks, and tools that are particularly relevant to the product's domain. Perform a thorough search and analysis to ensure a comprehensive list of requirements.

Available tools: {tools}

Format:
Question: input question
Thought: reasoning
Action: [{tool_names}]
Action Input: action input
Observation: action result
... (repeat as needed)
Thought: final reasoning
Final Answer: List each specific stack requirement on a new line. Prioritize specialized SDKs and providers which developers would list on Github. Do not use bullet points, numbering, or explanations. List all relevant SDKs and providers. Ensure the list is comprehensive and covers all aspects of the product.

Question: What are the specific stack requirements for this product description?
{input}
{agent_scratchpad}""",
    input_variables=["input", "tools", "tool_names", "agent_scratchpad"]
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
agent = create_react_agent(llm=gpt4, tools=tools, prompt=prompt)

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
    
    # Extract the list of requirements from the output
    output = result['output']
    if "Final Answer:" in output:
        output = output.split("Final Answer:")[-1].strip()
    
    # Split the output into individual lines and clean up
    raw_requirements = output.split('\n')
    requirements = []
    for req in raw_requirements:
        # Remove any leading/trailing whitespace, dashes, or other artifacts
        req = req.strip().lstrip('- ').strip()
        if req and not req.lower().startswith(('a ', 'an ', 'the ')):
            # Split compound requirements
            parts = re.split(r'[,/]', req)
            for part in parts:
                part = part.strip()
                if part and not part.lower() in ['e.g.', 'etc.', 'and', 'or']:
                    requirements.append(part)
    
    # Filter requirements to keep only likely SDKs, tools, and technologies
    filtered_requirements = filter_requirements(requirements)
    
    # If the list is too short, perform additional searches
    if len(filtered_requirements) < 5:
        additional_queries = [
            f"{product_description} technology stack",
            f"{product_description} development frameworks",
            f"{product_description} specialized tools"
        ]
        for query in additional_queries:
            search_results = json.loads(internet_search(query))
            for result in search_results:
                potential_reqs = extract_potential_requirements(result['snippet'])
                filtered_requirements.extend(filter_requirements(potential_reqs))
    
    # Final cleanup and deduplication
    filtered_requirements = list(set(filter(None, filtered_requirements)))
    
    # Additional post-processing to remove obviously irrelevant terms
    filtered_requirements = [req for req in filtered_requirements if not any(word in req.lower() for word in ['agreement', 'protocol', 'fund', 'market', 'exchange', 'bank', 'corporation'])]
    
    logger.info(f"Identified stack requirements: {filtered_requirements}")
    return filtered_requirements

def filter_requirements(requirements: List[str]) -> List[str]:
    # Use NLTK's stopwords
    stop_words = set(stopwords.words('english'))
    
    # List of known technologies, frameworks, and SDKs
    known_techs = set(['python', 'javascript', 'java', 'c++', 'rust', 'solana', 'ethereum', 'react', 'vue', 'angular', 'node.js', 'django', 'flask', 'spring', 'tensorflow', 'pytorch', 'scikit-learn', 'pandas', 'numpy', 'web3.js', 'solana-web3.js', 'anchor', 'serum', 'phantom wallet sdk'])
    
    # Regular expression for likely SDKs, tools, or technologies
    tech_pattern = re.compile(r'^(?!(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec))[A-Z0-9][A-Za-z0-9\-\.]*(?:\s[A-Z][A-Za-z0-9\-\.]*)*$')
    
    filtered = []
    for req in requirements:
        req_lower = req.lower()
        if req_lower in known_techs:
            filtered.append(req)
        elif tech_pattern.match(req) and req_lower not in stop_words and len(req) > 2:
            # Additional checks to filter out non-technical terms
            if not any(word in req_lower for word in ['agreement', 'protocol', 'fund', 'market', 'exchange', 'bank', 'corporation']):
                filtered.append(req)
    
    return filtered

def extract_potential_requirements(text: str) -> List[str]:
    # Extract potential requirements based on common naming patterns for technologies
    potential_reqs = re.findall(r'\b(?!(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec))[A-Z][a-zA-Z0-9.]+(?:\s[A-Z][a-zA-Z0-9.]+)*|\b[a-z]+(?:\.[a-z]+)+\b', text)
    return [req for req in potential_reqs if len(req) > 2 and not req.isdigit()]

# Example usage
if __name__ == "__main__":
    import sys
    import json

    product_descriptions = {
        "health-tech": [
            "AI-powered pathology slide analysis software for rare diseases",
            "Wearable tremor-cancelling gloves for surgeons performing microsurgeries",
            "VR-based phobia treatment platform for therapists",
            "IoT-enabled medication adherence tracking system for clinical trials",
            "Predictive analytics tool for hospital resource allocation during pandemics"
        ],
        "solana-blockchain": [
            "Video game development on Solana blockchain",
            "Solana-native supply chain verification system for luxury goods",
            "Tokenized real estate investment platform built on Solana",
            "Decentralized identity verification service for Solana dApps",
            "Solana-based carbon credit trading marketplace for corporations"
        ],
        "finance": [
            "AI-driven fraud detection system for cryptocurrency exchanges",
            "Quantum computing-based portfolio optimization tool for hedge funds",
            "Behavioral economics-based employee compensation structuring software",
            "Satellite imagery analysis platform for commodity traders",
            "Voice stress analysis tool for insurance claim verification"
        ]
    }

    if len(sys.argv) > 1:
        try:
            category, index = sys.argv[1].split('/')
            index = int(index)
            if category in product_descriptions and 0 <= index < len(product_descriptions[category]):
                product_description = product_descriptions[category][index]
            else:
                raise IndexError
        except (ValueError, IndexError, KeyError):
            print("Please provide a valid category and index, e.g., health-tech/3")
            print(f"Available categories: {', '.join(product_descriptions.keys())}")
            sys.exit(1)
    else:
        category = list(product_descriptions.keys())[0]
        product_description = product_descriptions[category][0]

    print(f"Analyzing product description: {product_description}")
    stack_requirements = identify_stack_requirements(product_description)
    print(json.dumps(stack_requirements, indent=4))