import os
from openai import OpenAI
# from literature_reviewer.model_interaction.frameworks_and_models import 
# from dotenv import load_dotenv
# load_dotenv()


def entry_chat_call(model_choice, system, task):
    client = OpenAI(
        base_url=os.getenv("OPENROUTER_BASE_URL"),
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )
    model_name = f"{model_choice.provider.lower()}/{model_choice.model_name}"
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": task}
    ]
    completion = client.chat.completions.create(
        model=model_name, messages=messages
    )
    return completion.choices[0].message.content    


def embed(model, input):
    client = OpenAI()
    
    if isinstance(input, str):
        input = [input.replace("\n", " ")]
    elif isinstance(input, list):
        input = [text.replace("\n", " ") for text in input]
    else:
        raise ValueError("Input must be a string or a list of strings")
    
    response = client.embeddings.create(input=input, model=model)
    
    if len(input) == 1:
        return response.data[0].embedding
    else:
        return [item.embedding for item in response.data]