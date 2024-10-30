"""
Reads in the initial materials provided by the user, embeds them
and generates a list of N queries which will expand the corpus to
all that can be found via Semantic Scholar, ideally.

Then, embed that. At this point the database is ready for searching.
"""
import json, logging
from literature_reviewer.tools.components.data_ingestion.preprocessing.langchain_extract_from_pdf import LangchainPDFTextExtractor
from literature_reviewer.tools.components.database_operations.chroma_operations import (
    add_to_chromadb,
    query_chromadb,
)
from literature_reviewer.agents.components.model_call import ModelInterface
from literature_reviewer.agents.components.frameworks_and_models import Model
from literature_reviewer.tools.components.prompts.literature_search_query import (
    generate_literature_search_query_sys_prompt,
    generate_initial_corpus_search_query_sys_prompt,
)
from literature_reviewer.tools.components.input_output_models.response_formats import (
    SeedDataQueryList,
    S2QueryList,
)
from literature_reviewer.tools.basetool import BaseTool, ToolResponse
from typing import Any


class ResearchQueryGenerator(BaseTool):
    def __init__(
        self,
        user_goals_text,
        user_supplied_pdfs_directory,
        model_interface,
        chunk_size=800,
        chunk_overlap=80,
        num_vec_db_queries=1,
        vec_db_query_num_results=1,
        num_s2_queries=1,
        chromadb_path=None,
    ):
        super().__init__(
            model_interface=model_interface
        )
        self.user_goals_text = user_goals_text
        self.user_supplied_pdfs_directory = user_supplied_pdfs_directory
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.num_vec_db_queries = num_vec_db_queries
        self.vec_db_query_num_results = vec_db_query_num_results
        self.num_s2_queries = num_s2_queries
        self.chromadb_path = chromadb_path

    def use(self, step: Any) -> ToolResponse:
        queries = self.embed_initial_corpus_get_queries()
        return ToolResponse(
            output=json.dumps({"queries": queries}),  # Convert list to JSON string
            explanation="Generated research queries based on user goals and supplied PDFs."
        )

    def embed_user_supplied_pdfs(self):
        chunks_with_ids = LangchainPDFTextExtractor(
            self.user_supplied_pdfs_directory,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        ).pdf_directory_to_chunks_with_ids()
        add_to_chromadb(chunks_with_ids, chroma_path=self.chromadb_path)
        
    def search_initial_corpus_for_queries_based_on_goals(self):
        vec_db_queries_raw = self.model_interface.chat_completion_call(
            system_prompt=generate_initial_corpus_search_query_sys_prompt(self.num_vec_db_queries),
            user_prompt=self.user_goals_text,
            response_format=SeedDataQueryList
        )
        vec_db_queries = json.loads(vec_db_queries_raw)["vec_db_queries"]        
        contexts = [
            query_chromadb(
                query_text=query,
                num_results=self.vec_db_query_num_results,
                chroma_path=self.chromadb_path,
            ) for query in vec_db_queries
        ]
        joined_context = "\n".join(contexts)
        semantic_scholar_queries = self.model_interface.chat_completion_call(
            system_prompt=generate_literature_search_query_sys_prompt(self.num_s2_queries),
            user_prompt=joined_context + self.user_goals_text,
            response_format=S2QueryList
        )

        
        logging.info("S2 Query Objects Generated")
        return semantic_scholar_queries
    
    def embed_initial_corpus_get_queries(self):
        self.embed_user_supplied_pdfs()
        raw_s2_queries = self.search_initial_corpus_for_queries_based_on_goals()
        query_objects = json.loads(raw_s2_queries)
        queries = [obj['query'] for obj in query_objects['s2_queries']]
        return queries  # This still returns a list of strings directly


# Example Usage
if __name__ == "__main__":
    from literature_reviewer.agents.components.frameworks_and_models import ( #noqa
        PromptFramework, Model
    )    
    with open("/home/christian/literature-reviewer/user_inputs/goal_prompt.txt", "r") as file:
        user_goals_text = file.read()
    user_supplied_pdfs_directory = "/home/christian/literature-reviewer/user_inputs/user_supplied_pdfs"
    num_vec_db_queries = 3
    vec_db_query_num_results = 2
    num_s2_queries = 10

    model_interface = ModelInterface(
        prompt_framework=PromptFramework.OAI_API,
        model=Model("gpt-4o-mini","OpenAI"),
    )
    user_materials_input = ResearchQueryGenerator(
        user_goals_text=user_goals_text,
        user_supplied_pdfs_directory=user_supplied_pdfs_directory,
        model_interface=model_interface,
        num_vec_db_queries=num_vec_db_queries,
        vec_db_query_num_results=vec_db_query_num_results,
        num_s2_queries=num_s2_queries,
    )

    result = user_materials_input.use(None)  # Passing None as we don't use the step parameter
    print(f"Output: {result.output}")
    print(f"Explanation: {result.explanation}")
