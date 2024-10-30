"""
OpenAI API calls (or any that use this format)

Includes handling for o1 (user-only, no images)
"""

import logging
import os
from openai import OpenAI


def chat_completion_call(
    model_choice,
    system,
    user,
    response_format=None,
    assistant=None,
    base64_image_string=None,
    temperature=0.7,
    tools=None,
    tool_choice=None
):
    if not user:
        raise ValueError("User input is required")

    try:
        client = OpenAI(
            base_url=os.getenv("OPENROUTER_BASE_URL"),
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )
        model_name = f"{model_choice.provider.lower()}/{model_choice.model_name}"
        
        messages = []
        if "o1" in model_name.lower():
            combined_prompt = ""
            if system:
                combined_prompt += f"System: {system}\n\n"
            if assistant:
                combined_prompt += f"Assistant: {assistant}\n\n"
            combined_prompt += f"User: {user}"
            messages.append({"role": "user", "content": combined_prompt})
        else:
            if system:
                messages.append({"role": "system", "content": system})
            if assistant:
                messages.append({"role": "assistant", "content": assistant})
            user_message = {"role": "user", "content": [{"type": "text", "text": user}]}
            if base64_image_string:
                user_message["content"].append({"type": "image_url", "image_url": f"data:image/jpeg;base64,{base64_image_string}"})
            messages.append(user_message)

        completion_kwargs = {
            "model": model_name,
            "messages": messages,
            "temperature": temperature
        }
        if tools and not "o1" in model_name.lower():
            completion_kwargs.update({"tools": tools, "tool_choice": tool_choice})
        
        completion_method = client.beta.chat.completions.parse if response_format else client.chat.completions.create
        completion_kwargs["response_format"] = response_format if response_format else None
        
        completion = completion_method(**completion_kwargs)
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