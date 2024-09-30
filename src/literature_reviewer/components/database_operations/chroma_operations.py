"""
Initial attempt at local vector store
Thanks to https://github.com/pixegami/rag-tutorial-v2/blob/main/populate_database.py
"""
import chromadb
from langchain.schema.document import Document
from langchain_chroma import Chroma
from literature_reviewer.components.model_interaction.frameworks.langchain import get_embedding_function
import numpy as np
import pandas as pd

def add_to_chromadb(chunks_with_ids: list[Document], chroma_path: str, model: str = "text-embedding-3-large"):
    # Load the existing database.
    db = Chroma(
        persist_directory=chroma_path, embedding_function=get_embedding_function(model)
    )

    # Add or Update the documents.
    existing_items = db.get(include=[])  # IDs are always included by default
    existing_ids = set(existing_items["ids"])
    print(f"Number of existing documents in DB: {len(existing_ids)}")

    # Only add documents that don't exist in the DB.
    new_chunks = []
    for chunk in chunks_with_ids:
        if chunk.metadata["id"] not in existing_ids:
            new_chunks.append(chunk)

    if len(new_chunks):
        print(f"Adding new documents: {len(new_chunks)}")
        new_chunk_ids = [chunk.metadata["id"] for chunk in new_chunks]
        db.add_documents(new_chunks, ids=new_chunk_ids)
        # db.persist() ?? now saying not a method
    else:
        print("No new documents to add")
        
        
def query_chromadb(
    query_text: str,
    num_results: int = 5,
    chroma_path: str = "chroma_db",
    model: str = "text-embedding-3-large"
) -> str:
    db = Chroma(persist_directory=chroma_path, embedding_function=get_embedding_function(model))
    result_list = db.similarity_search_with_score(query_text, k=num_results)
    return "\n\n---\n\n".join([doc.page_content for doc, _score in result_list])


def get_full_chromadb_collection(
    chroma_path: str,
    collection_index: int = 0,
) -> tuple[np.ndarray, list]:
    client = chromadb.PersistentClient(path=chroma_path)
    collection = client.list_collections()[collection_index]
    
    results = collection.get(include=['embeddings'])
    
    results = collection.get(include=['embeddings', 'documents', 'metadatas'])
    
    return {
        'ids': results['ids'],
        'embeddings': np.array(results['embeddings']),
        'documents': results['documents'],
        'metadatas': results['metadatas']
    }
