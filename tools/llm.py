import os
from langchain_openai import AzureChatOpenAI

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