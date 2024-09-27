"""
Handles extracting text from pdf using langchain's inbuilt functionality

Thanks to: https://github.com/pixegami/rag-tutorial-v2/blob/main/populate_database.py
For logic here. For some reason I had to turn it into a class...
"""
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema.document import Document

class LangchainPDFTextExtractor:
    def __init__(
        self,
        input_folder,
        chunk_size=800,
        chunk_overlap=80
    ):
        self.input_folder = input_folder
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap


    def pdf_directory_to_chunks_with_ids(self):
        documents = self._load_documents()
        chunks = self._split_documents(documents)
        return self._calculate_chunk_ids(chunks)


    def _load_documents(self):
        document_loader = PyPDFDirectoryLoader(self.input_folder)
        return document_loader.load()


    def _split_documents(self, documents: list[Document]):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )
        return text_splitter.split_documents(documents)


    @staticmethod
    def _calculate_chunk_ids(chunks):
        """        
        This will create IDs like "data/monopoly.pdf:6:2"
        Page Source : Page Number : Chunk Index
        """

        last_page_id = None
        current_chunk_index = 0

        for chunk in chunks:
            source = chunk.metadata.get("source")
            page = chunk.metadata.get("page")
            current_page_id = f"{source}:{page}"

            # If the page ID is the same as the last one, increment the index.
            if current_page_id == last_page_id:
                current_chunk_index += 1
            else:
                current_chunk_index = 0

            # Calculate the chunk ID.
            chunk_id = f"{current_page_id}:{current_chunk_index}"
            last_page_id = current_page_id

            # Add it to the page meta-data.
            chunk.metadata["id"] = chunk_id

        return chunks
