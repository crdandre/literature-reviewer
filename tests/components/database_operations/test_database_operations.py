from literature_reviewer.components.preprocessing.langchain_extract_from_pdf import LangchainPDFTextExtractor
from literature_reviewer.components.database_operations.chroma_operations import add_to_chromadb, query_chromadb

def test_embed_pdf_in_chromadb_langchain():
    pdf_folder = r"/home/christian/literature-reviewer/input_pdfs"
    chunks_with_ids = LangchainPDFTextExtractor(pdf_folder).pdf_directory_to_chunks_with_ids()
    add_to_chromadb(chunks_with_ids)
    
def test_chromadb_query_langchain():
    num_results = 3
    query = "What is complexity economics, and what document can this be found in?"
    context = query_chromadb(query_text=query, num_results=num_results)
    assert(len(context)==num_results)


if __name__ == "__main__":
    # test_embed_pdf_in_chromadb_langchain()
    test_chromadb_query_langchain()
