"""
LLM Breathing, First Form: Queries from local seed data.

Prior to this file being called, get_initial_search_queries
is called.

For now the content vetting is on a paper level, but could be
on a chunk level, so that irrelevant chunks are removed but relevant
chunks within a paper can be kept for that paper's entry...not yet

I also don't yet do anything with the reasons yet or connect anything
back to the user goals directly in the output list.

batches of chunks per evaluation for filtering the search results
depends on chunk size, set elsewhere
"""
import json, os, requests
from literature_reviewer.components.data_ingestion.semantic_scholar import SemanticScholarInterface
from literature_reviewer.components.preprocessing.langchain_extract_from_pdf import LangchainPDFTextExtractor
from literature_reviewer.components.database_operations.chroma_operations import (
    add_to_chromadb,
)
from literature_reviewer.components.model_interaction.model_call import ModelInterface
from literature_reviewer.components.model_interaction.frameworks_and_models import (
    PromptFramework,
    Model,
)
from literature_reviewer.components.prompts.literature_search_query import (
    generate_s2_results_evaluation_system_prompt,
)
from literature_reviewer.components.prompts.response_formats import (
    CorpusInclusionVerdict
)
from langchain.schema import Document
import logging

class CorpusGatherer:
    def __init__(
        self,
        search_queries,
        user_goals_text,
        s2_interface=SemanticScholarInterface(),
        s2_results_num_eval_loops=1,
        pdf_download_path=None,
        model_name=None,
        model_provider=None,
        vector_db_path=None,
        batch_size=12,
        inclusion_threshold=0.85
    ):
        self.search_queries = search_queries
        self.user_goals_text = user_goals_text
        self.s2_interface = s2_interface
        self.s2_results_num_eval_loops = s2_results_num_eval_loops
        self.pdf_download_path = pdf_download_path or os.getenv("PDF_DOWNLOAD_PATH", "pdf_downloads")
        self.model_name = model_name or os.getenv("DEFAULT_MODEL_NAME")
        self.model_provider = model_provider or os.getenv("DEFAULT_MODEL_PROVIDER")
        self.vector_db_path = vector_db_path or os.getenv("CHROMA_DB_PATH")
        self.batch_size = batch_size
        self.inclusion_threshold = inclusion_threshold
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def search_s2_for_queries(self):
        return self.s2_interface.search_papers_via_queries(self.search_queries)
        
    
    def populate_s2_search_results_text(self, search_results):
        """
        Removes the "openAccessPdf" and "abstract" fields, so that they
        can be re-written to a more flexible "text" field containing
        chunks
        """
        logging.info(f"Processing {len(search_results)} search results")
        processed_results = []
        for index, result in enumerate(search_results):
            if result is None:
                logging.warning(f"Skipping None result at index {index}")
                continue
            
            try:
                paper_id = result.get('paperId', 'unknown')
                processed_result = {
                    key: value for key, value in result.items() 
                    if key not in ['openAccessPdf', 'abstract']
                }
                processed_result['text'] = {
                    'abstract': [],
                    'pdf_extraction': []
                }
                
                if result.get('abstract'):
                    processed_result['text']['abstract'] = [(paper_id, result['abstract'])]
                
                if (
                    result.get('isOpenAccess') and result.get('openAccessPdf') and result['openAccessPdf'].get('url') and
                    f"{result.get('paperId', 'unknown')}.pdf" not in os.listdir(self.pdf_download_path)
                ):
                    pdf_url = result['openAccessPdf']['url']
                    pdf_filename = f"{result.get('paperId', 'unknown')}.pdf"
                    pdf_path = os.path.join(self.pdf_download_path, pdf_filename)
                    
                    try:
                        response = requests.get(pdf_url)
                        response.raise_for_status()
                        with open(pdf_path, 'wb') as pdf_file:
                            pdf_file.write(response.content)
                        logging.info(f"Downloaded PDF: {pdf_filename}")
                    except Exception as e:
                        logging.error(f"Failed to download PDF: {pdf_url}. Error: {str(e)}")
                else:
                    logging.info(f"PDF for {paper_id} already downloaded...")
                
                processed_results.append(processed_result)
                
            except Exception as e:
                logging.error(f"Error processing result at index {index}: {str(e)}")
                continue

        logging.info(f"Processed {len(processed_results)} valid results")

        # Convert all PDFs to Documents using LangchainPDFTextExtractor
        extractor = LangchainPDFTextExtractor(input_folder=self.pdf_download_path)
        all_chunks_with_ids = extractor.pdf_directory_to_chunks_with_ids()

        # Group chunks by their source (PDF file)
        chunks_by_source = {}
        for chunk in all_chunks_with_ids:
            source = chunk.metadata.get("source")
            if source not in chunks_by_source:
                chunks_by_source[source] = []
            chunks_by_source[source].append(chunk)

        # Add chunks to each processed result
        for processed_result in processed_results:
            paper_id = processed_result.get('paperId', 'unknown')
            pdf_filename = f"{paper_id}.pdf"
            pdf_path = os.path.join(self.pdf_download_path, pdf_filename)
            
            if os.path.exists(pdf_path):
                chunks = chunks_by_source.get(pdf_path, [])
                processed_result['text']['pdf_extraction'] = [
                    (chunk.metadata.get("id"), chunk.page_content)
                    for chunk in chunks
                ]
            else:
                logging.warning(f"PDF not found for paper ID: {paper_id}")

        return processed_results, all_chunks_with_ids
    
    #TODO
    def search_for_related_papers():
        """
        finds papers related to a given input paper
        possibly useful for each of the initial findings
        which are found based on the created queries
        """
        pass
    
    
    #TODO
    def clean_formatted_s2_results():
        pass
    

    def evaluate_formatted_s2_results(self, results, batch_size, inclusion_threshold):
        """
        This is somewhat improvised.
        Make this more meta-agent-y later, for now give a static approach.
        
        for each paper in the results list, query the LLM for each batch of chunks whether the
        content of the chunks relates well to the existing corpus and the user's goals, to vet
        whether it should be added to the corpus
        """
        system_prompt = generate_s2_results_evaluation_system_prompt()
        prompt_framework = PromptFramework.OAI_API
        chat_model = Model(self.model_name, self.model_provider)
        chat_interface = ModelInterface(prompt_framework, chat_model)
        paper_verdicts = []
        for result in results:
            abstract_chunks = result.get('text', {}).get('abstract', [])
            pdf_extraction_chunks = result.get('text', {}).get('pdf_extraction', [])
            combined_chunks = abstract_chunks + pdf_extraction_chunks
            num_batches = (len(combined_chunks) + batch_size - 1) // batch_size
            this_paper_verdicts = []
            for batch_index in range(num_batches):
                start_index = batch_index * batch_size
                end_index = min((batch_index + 1) * batch_size, len(combined_chunks))
                batch = combined_chunks[start_index:end_index]
                batch_as_string = "\n".join([chunk[1] for chunk in batch]) #joins the content of the chunk not the ID
                corpus_inclusion_verdict = chat_interface.entry_chat_call(
                    system_prompt=system_prompt,
                    user_prompt=batch_as_string + "\n\n" + self.user_goals_text,
                    response_format=CorpusInclusionVerdict
                )
                # Convert the string to a dictionary
                verdict_dict = json.loads(corpus_inclusion_verdict)
                # Append the boolean verdict
                this_paper_verdicts.append(verdict_dict['verdict'])
                logging.info(f"Batch {batch_index + 1} verdict for paper {result['paperId']}: {verdict_dict['verdict']}")
                
            average_verdict = sum(this_paper_verdicts) / len(this_paper_verdicts) if this_paper_verdicts else 0
            paper_id = result.get('paperId', 'unknown')
            paper_verdicts.append((paper_id, average_verdict))
            
        # Filter out papers below the inclusion threshold and return their IDs
        approved_paper_ids = [
            paper_id
            for paper_id, verdict in paper_verdicts 
            if verdict >= inclusion_threshold
        ]
        
        logging.info(f"Number of papers approved: {len(approved_paper_ids)}")
        logging.info(f"Number of papers rejected: {len(paper_verdicts) - len(approved_paper_ids)}")
            
        return approved_paper_ids

    def embed_approved_search_results(self, approved_paper_ids, all_chunks_with_ids):
        """
        Gets chunks with ids for the selected papers and adds them to the database.
        """
        approved_chunks = []
        for chunk in all_chunks_with_ids:
            # Extract paper ID from the chunk's source path
            paper_id = chunk.metadata['source'].split('/')[-1].split('.')[0]
            if paper_id in approved_paper_ids:
                approved_chunks.append(Document(
                    page_content=chunk.page_content,
                    metadata={
                        'id': chunk.metadata['id'],
                        **chunk.metadata
                    }
                ))
        
        # Add the approved chunks to the vector database
        if approved_chunks:
            add_to_chromadb(approved_chunks)
        
        logging.info(f"Added {len(approved_chunks)} chunks from {len(approved_paper_ids)} papers to the vector database.")

    def gather_and_embed_corpus(self):
        search_results = self.search_s2_for_queries()
        formatted_search_results_with_text, all_chunks_with_ids = self.populate_s2_search_results_text(search_results)
        approved_paper_ids = self.evaluate_formatted_s2_results(
            results=formatted_search_results_with_text,
            batch_size=self.batch_size,
            inclusion_threshold=self.inclusion_threshold
        )
        self.embed_approved_search_results(approved_paper_ids=approved_paper_ids, all_chunks_with_ids=all_chunks_with_ids)

if __name__ == "__main__":
    # Example usage
    from dotenv import load_dotenv
    load_dotenv()
    
    logging.info(f"PDF_DOWNLOAD_PATH: {os.getenv('PDF_DOWNLOAD_PATH')}")
    logging.info(f"DEFAULT_MODEL_NAME: {os.getenv('DEFAULT_MODEL_NAME')}")
    logging.info(f"DEFAULT_MODEL_PROVIDER: {os.getenv('DEFAULT_MODEL_PROVIDER')}")
    logging.info(f"CHROMA_DB_PATH: {os.getenv('CHROMA_DB_PATH')}")
    
    with open("/home/christian/literature-reviewer/user_inputs/goal_prompt.txt", "r") as file:
        user_goals_text = file.read()
    search_queries = ["scoliosis spine finite element models d'andrea"]
    corpus_gatherer = CorpusGatherer(
        search_queries=search_queries,
        user_goals_text=user_goals_text,
        batch_size=12,
        inclusion_threshold=0.85
    )
    corpus_gatherer.gather_corpus()

