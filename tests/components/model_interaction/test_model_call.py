import logging
from literature_reviewer.components.model_interaction.model_call import ModelInterface
from literature_reviewer.components.model_interaction.frameworks_and_models import PromptFramework, Model
from literature_reviewer.components.database_operations.chroma_operations import query_chromadb
import argparse

from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def main(disable_logging=False):
    user_query = "What does Aubin say about scoliotic brace design?"
    
    if not disable_logging:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    else:
        logging.disable(logging.CRITICAL)

    num_vecdb_results=3
    prompt_framework = PromptFramework.OAI_API
    chat_model = Model("gpt-4o-mini", "OpenAI")
    chat_interface = ModelInterface(prompt_framework, chat_model)
    context = query_chromadb(query_text=user_query, num_results=num_vecdb_results)

    system_prompt = "You are a helpful AI assistant who analyzes the input text to find the relevant connections, themes, gaps, remaining questions, and future directions. I.e. the components of a narrative literature review. You are to express the answers in clear concise academic language suitable for anyone who works in the given topic's field. Write a list of the top 5 themes highlighted in the context. Each list item should be a short sentence."
    
    task_prompt = f"""
    Based on the following context and user query, provide a response:
    
    Context: {context}
    
    User Query: {user_query}
    """

    if not disable_logging:
        logging.info("Prepared prompts for LLM:")
        logging.info(f"System prompt: {system_prompt}")
        logging.info(f"Task prompt: {task_prompt}")
        logging.info("Sending request to LLM...")
    else:
        print("\nPrompt:")
        print(task_prompt)

    try:
        response = chat_interface.entry_chat_call(system_prompt, task_prompt)
        if not disable_logging:
            logging.info("LLM Response received")
        print("\nLLM Response:")
        print(response)
    except Exception as e:
        if not disable_logging:
            logging.error(f"An error occurred during LLM call: {e}")
        else:
            print(f"An error occurred during LLM call: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the literature reviewer with optional logging.")
    parser.add_argument("-dl","--disable-logging", action="store_true", help="Disable all logging output")
    args = parser.parse_args()

    main(disable_logging=args.disable_logging)