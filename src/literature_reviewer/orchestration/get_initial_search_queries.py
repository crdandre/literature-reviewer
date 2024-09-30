"""
Reads in the initial materials provided by the user, embeds them
and generates a list of N queries which will expand the corpus to
all that can be found via Semantic Scholar, ideally.

Then, embed that. At this point the database is ready for searching.
"""
import json
from literature_reviewer.components.preprocessing.langchain_extract_from_pdf import LangchainPDFTextExtractor
from literature_reviewer.components.database_operations.chroma_operations import (
    add_to_chromadb,
    query_chromadb,
)
from literature_reviewer.components.model_interaction.model_call import ModelInterface
from literature_reviewer.components.model_interaction.frameworks_and_models import (
    PromptFramework,
    Model,
)
from literature_reviewer.components.prompts.literature_search_query import (
    generate_literature_search_query_sys_prompt,
    generate_initial_corpus_search_query_sys_prompt,
)
from literature_reviewer.components.prompts.response_formats import (
    SeedDataQueryList,
    S2QueryList,
)


class UserMaterialsInput:
    def __init__(
        self,
        user_goals_text,
        user_supplied_pdfs_directory,
        chunk_size=800,
        chunk_overlap=80,
        num_vec_db_queries=1,
        vec_db_query_num_results=1,
        num_s2_queries = 1,
        prompt_framework=None,
        model_name="gpt-4o-mini",
        model_provider = "OpenAI",
        chromadb_path = None,
    ):
        self.user_goals_text = user_goals_text
        self.user_supplied_pdfs_directory = user_supplied_pdfs_directory
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.num_vec_db_queries = num_vec_db_queries
        self.vec_db_query_num_results = vec_db_query_num_results
        self.num_s2_queries = num_s2_queries
        self.prompt_framework = prompt_framework
        self.model_name = model_name
        self.model_provider = model_provider
        self.chromadb_path = chromadb_path
        
    def embed_user_supplied_pdfs(self):
        chunks_with_ids = LangchainPDFTextExtractor(
            self.user_supplied_pdfs_directory,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        ).pdf_directory_to_chunks_with_ids()
        add_to_chromadb(chunks_with_ids, chroma_path=self.chromadb_path)
        
    def search_initial_corpus_for_queries_based_on_goals(self):
        chat_model = Model(self.model_name, self.model_provider)
        chat_interface = ModelInterface(self.prompt_framework, chat_model)
        vec_db_queries_raw = chat_interface.entry_chat_call(
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
        semantic_scholar_queries = chat_interface.entry_chat_call(
            system_prompt=generate_literature_search_query_sys_prompt(self.num_s2_queries),
            user_prompt=joined_context + self.user_goals_text,
            response_format=S2QueryList
        )

        
        # # Pretty print the semantic_scholar_queries in JSON format
        # print("SEMANTIC SCHOLAR QUERY LIST (Pretty JSON):")
        # print(json.dumps(json.loads(semantic_scholar_queries), indent=4))
        print("S2 Query Objects Generated")
        return semantic_scholar_queries
    
    def embed_initial_corpus_get_queries(self):
        self.embed_user_supplied_pdfs()
        raw_s2_queries = self.search_initial_corpus_for_queries_based_on_goals()
        # Parse the JSON string to get the list of queries
        query_objects = json.loads(raw_s2_queries)
        queries = [obj['query'] for obj in query_objects['s2_queries']]
        
        # Return only the parsed list of queries
        return queries

if __name__ == "__main__":
    with open("/home/christian/literature-reviewer/user_inputs/goal_prompt.txt", "r") as file:
        user_goals_text = file.read()
    user_supplied_pdfs_directory = "/home/christian/literature-reviewer/input_pdfs"
    num_vec_db_queries = 3
    vec_db_query_num_results = 2
    num_s2_queries = 10
    model_name = "gpt-4o-mini"
    model_provider = "OpenAI"

    user_materials_input = UserMaterialsInput(
        user_goals_text=user_goals_text,
        user_supplied_pdfs_directory=user_supplied_pdfs_directory,
        num_vec_db_queries=num_vec_db_queries,
        vec_db_query_num_results=vec_db_query_num_results,
        num_s2_queries=num_s2_queries,
        model_name=model_name,
        model_provider=model_provider
    )

    user_materials_input.embed_user_supplied_pdfs()
    user_materials_input.search_initial_corpus_for_queries_based_on_goals()
    
