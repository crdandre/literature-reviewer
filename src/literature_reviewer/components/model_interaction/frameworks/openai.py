import logging
import os
from openai import OpenAI


def entry_chat_call(model_choice, system, user, response_format, base64_image_string):
    try:
        client = OpenAI(
            base_url=os.getenv("OPENROUTER_BASE_URL"),
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )
        model_name = f"{model_choice.provider.lower()}/{model_choice.model_name}"
        messages = [
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": [{"type": "text", "text": user}]
            }
        ]
        
        if base64_image_string is not None:
            messages[1]["content"].append({
                "type": "image_url",
                "image_url": f"data:image/jpeg;base64,{base64_image_string}"
            })
        if response_format:
            completion = client.beta.chat.completions.parse(
                model=model_name,
                messages=messages,
                response_format=response_format
            )      
        else: 
            completion = client.chat.completions.create(
                model=model_name,
                messages=messages
            )
        return completion.choices[0].message.content
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        return None


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