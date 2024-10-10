"""
Handles extracting text from pdf using langchain's inbuilt functionality

Thanks to: https://github.com/pixegami/rag-tutorial-v2/blob/main/populate_database.py
For logic here. For some reason I had to turn it into a class...
"""
import os, logging
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema.document import Document
from pypdf.errors import PdfStreamError, PdfReadError


class LangchainPDFTextExtractor:
    def __init__(
        self,
        input_folder=None,
        chunk_size=800,
        chunk_overlap=80,
        extract_images=False
    ):
        self.input_folder = input_folder
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.extract_images = extract_images


    def pdf_directory_to_chunks_with_ids(self):
        documents = self._load_documents()
        chunks = self._split_documents(documents)
        return self._calculate_chunk_ids(chunks)

    
    def _load_documents(self):
        all_documents = []
        for filename in os.listdir(self.input_folder):
            if filename.lower().endswith('.pdf'):
                file_path = os.path.join(self.input_folder, filename)
                try:
                    # Check if the file is actually a PDF
                    with open(file_path, 'rb') as f:
                        if not f.read(5).startswith(b'%PDF-'):
                            logging.warning(f"File {filename} is not a valid PDF. Skipping.")
                            continue

                    loader = PyPDFLoader(file_path)
                    documents = loader.load()
                    all_documents.extend(documents)
                    logging.info(f"Successfully loaded {filename}")
                except (PdfStreamError, PdfReadError) as e:
                    logging.error(f"Error loading PDF {filename}: {str(e)}")
                except Exception as e:
                    logging.error(f"Unexpected error loading PDF {filename}: {str(e)}")
        
        if not all_documents:
            logging.warning("No documents were successfully loaded.")
        else:
            logging.info(f"Successfully loaded {len(all_documents)} documents in total.")
        
        return all_documents


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
