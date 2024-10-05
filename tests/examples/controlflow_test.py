"""
Test for using any model from openrouter with the controlflow agent system
"""

# import os

import controlflow as cf
# from langchain_openai import ChatOpenAI

from dotenv import load_dotenv
load_dotenv()

# model = "meta-llama/llama-3-70b-instruct"
# # model= "openai/gpt-4o-mini"
# open_model = ChatOpenAI(
#     model=model,
#     temperature=0.6,
#     openai_api_key=os.getenv("OPENROUTER_API_KEY"),
#     openai_api_base="https://openrouter.ai/api/v1"
# )

# agent_open = cf.Agent(name="Testy McTest", model=open_model, interactive=True)
agent_closed = cf.Agent(name="OpenAI-Direct", model="openai/gpt-4o-mini", interactive=True)

agent_closed.run("quiz me on the metric prefixes")

"""

02:57:43.780 | WARNING | langsmith.client - Failed to batch ingest runs: langsmith.utils.LangSmithError: Failed to POST https://api.smith.langchain.com/runs/batch in LangSmith API. HTTPError('403 Client Error: Forbidden for url: https://api.smith.langchain.com/runs/batch', '{"detail":"Forbidden"}')

What is this? It uses langsmith and is getting 403...

export LANGCHAIN_TRACING_V2=false fixed it,
setting that to "true" and adding export LANGCHAIN_API_KEY=<your-api-key>
would allow me to use 
"""