import logging
from literature_reviewer.components.model_interaction.model_call import ModelInterface
from literature_reviewer.components.model_interaction.frameworks_and_models import PromptFramework, Model
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import os
from literature_reviewer.components.preprocessing.extract_from_pdf import LocalPDFTextExtractor
from tqdm import tqdm
import argparse

from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Sample documents (in a real scenario, these would be loaded from files)
def load_markdown_from_pdf(pdf_path):
    # pdf_folder = os.path.dirname(pdf_path)
    # pdf_filename = os.path.basename(pdf_path)
    # extractor = LocalPDFTextExtractor(
    #     pdf_inputs_folder=pdf_folder,
    #     marker_single_input_filename=pdf_filename
    # )
    # markdown_path = extractor.extract_single_pdf_to_markdown()
    markdown_path = r"/home/christian/literature-reviewer/input_pdfs/markdown_conversions/1_Arthur_2021_Foundations_of_Complexity_Economics/1_Arthur_2021_Foundations_of_Complexity_Economics.md"
    if markdown_path and os.path.exists(markdown_path):
        with open(markdown_path, 'r', encoding='utf-8') as file:
            return file.read()
    else:
        logging.error(f"Failed to extract markdown from PDF: {pdf_path}")
        return None

def split_into_chunks(text, chunk_size=1000, overlap=100, max_chunks=1000):
    chunks = []
    start = 0
    while start < len(text) and len(chunks) < max_chunks:
        end = start + chunk_size
        if end > len(text):
            end = len(text)
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
    return chunks

def create_embeddings(interface, texts):
    logging.info(f"Creating embeddings for {len(texts)} documents")
    all_chunks = []
    for i, text in enumerate(texts):
        logging.info(f"Processing document {i+1}/{len(texts)}")
        chunks = split_into_chunks(text)
        logging.info(f"Document split into {len(chunks)} chunks")
        all_chunks.extend(chunks)
    
    logging.info(f"Total chunks to embed: {len(all_chunks)}")
    
    try:
        logging.info(interface.model)
        logging.info(interface.prompt_framework)
        all_embeddings = interface.embed(all_chunks)
        logging.info("Embeddings created successfully")
        
        # Log a few elements of the embedding for the first chunk
        if all_embeddings and isinstance(all_embeddings[0], (list, np.ndarray)):
            logging.info(f"Sample of embedding for first chunk: {all_embeddings[0][:5]}")
        else:
            logging.info(f"Unexpected embedding format: {type(all_embeddings)}")
        
        return all_embeddings
    except Exception as e:
        logging.error(f"An error occurred during embedding: {e}")
        return None

def find_most_similar(query_embedding, doc_embeddings, top_k=1):
    similarities = cosine_similarity([query_embedding], doc_embeddings)[0]
    top_indices = np.argsort(similarities)[-top_k:][::-1]
    return top_indices

def main(disable_logging=False):
    if not disable_logging:
        # Configure logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    else:
        # Disable all logging
        logging.disable(logging.CRITICAL)

    prompt_framework = PromptFramework.OAI_API
    chat_model = Model("gpt-4o-mini", "OpenAI")
    embedding_model = Model("text-embedding-3-small", "OpenAI")
    
    chat_interface = ModelInterface(prompt_framework, chat_model)
    embedding_interface = ModelInterface(prompt_framework, embedding_model)
        
    # User query
    user_query = "What literature review content exists here?"

    logging.info(f"User query: {user_query}")

    # Replace the sample documents with the extracted markdown
    pdf_path = "/home/christian/literature-reviewer/input_pdfs/1_Arthur_2021_Foundations_of_Complexity_Economics.pdf"  # Update this with the actual path to your PDF
    markdown_content = load_markdown_from_pdf(pdf_path)
    
    if markdown_content is None:
        logging.error("Failed to load markdown content. Exiting.")
        return

    documents = [markdown_content]

    # Create embeddings for documents
    doc_embeddings = create_embeddings(embedding_interface, documents)
    if doc_embeddings is None:
        logging.error("Failed to create document embeddings. Exiting.")
        return

    logging.info("Creating embedding for user query")
    query_embedding = embedding_interface.embed([user_query])
    logging.info("Query embedding created successfully")

    # Log information about the query embedding
    if isinstance(query_embedding, (list, np.ndarray)) and len(query_embedding) > 0:
        if isinstance(query_embedding[0], (list, np.ndarray)):
            logging.info(f"Sample of query embedding: {query_embedding[0][:5]}")
        else:
            logging.info(f"Query embedding: {query_embedding[:5]}")
    else:
        logging.info(f"Unexpected query embedding format: {type(query_embedding)}")

    # Ensure query_embedding is in the correct format for find_most_similar
    if isinstance(query_embedding, (list, np.ndarray)) and len(query_embedding) > 0:
        if isinstance(query_embedding[0], (list, np.ndarray)):
            query_embedding = query_embedding[0]
    else:
        logging.error("Invalid query embedding format. Exiting.")
        return

    # Find most similar chunks
    top_k = 3  # Number of most similar chunks to consider
    most_similar_indices = find_most_similar(query_embedding, doc_embeddings, top_k)
    most_similar_chunks = [documents[0][i*1000:(i+1)*1000] for i in most_similar_indices]  # Assuming 1000 is the chunk size
    
    context = " ".join(most_similar_chunks)
    logging.info(f"Most similar chunks found. Combined length: {len(context)} characters")

    system_prompt = "You are a helpful AI assistant who analyzes the input text to find the relevant connections, themes, gaps, remaining questions, and future directions. I.e. the components of a narrative literature review. You are to express the answers in clear concise academic language suitable for anyone who works in the given topic's field"
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