from literature_reviewer.components.model_interaction.model_call import ChatInterface
from literature_reviewer.components.model_interaction.frameworks_and_models import PromptFramework, Model

from dotenv import load_dotenv
load_dotenv()

def main():
    prompt_framework = PromptFramework.ELL
    model = Model("gpt-4o-mini", "OpenAI")
    llm_interface = ChatInterface(prompt_framework, model)

    system_prompt = "You are a helpful AI assistant specializing in literature reviews."
    task_prompt = "Summarize the key findings of the paper 'Recent Advances in Natural Language Processing' in 10 words."

    print("Sending request to LLM...")
    
    try:
        response = llm_interface.entry_chat_call(system_prompt, task_prompt)
        print("\nLLM Response:")
        print(response)
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()