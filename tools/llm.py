import os
from dotenv import load_dotenv
from pathlib import Path
from langchain_openai import AzureChatOpenAI
# Get the project root directory
project_root = Path(__file__).parent.parent

# Load the .env file from the project root
load_dotenv(project_root / '.env')

# azure chat
gpt3 = AzureChatOpenAI(
    temperature = 0,
    deployment_name = os.environ['GPT3_AZURE_OPENAI_CHAT_DEPLOYMENT_NAME'],
    openai_api_version = os.environ['AZURE_OPENAI_API_VERSION']
)
gpt4 = AzureChatOpenAI(
    temperature = 0,
    deployment_name = os.environ['GPT4_AZURE_OPENAI_CHAT_DEPLOYMENT_NAME'],
    openai_api_version = os.environ['AZURE_OPENAI_API_VERSION']
)