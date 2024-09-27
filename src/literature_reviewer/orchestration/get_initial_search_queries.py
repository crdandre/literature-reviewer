"""
Reads in the initial materials provided by the user, embeds them
and generates a list of N queries which will expand the corpus to
all that can be found via Semantic Scholar, ideally.

Then, embed that. At this point the database is ready for searching.
"""
import json
from literature_reviewer.components.preprocessing.langchain_extract_from_pdf import LangchainPDFTextExtractor
from literature_reviewer.components.database_operations.chroma_operations import add_to_chromadb, query_chromadb
from literature_reviewer.components.model_interaction.model_call import ModelInterface
from literature_reviewer.components.model_interaction.frameworks_and_models import PromptFramework, Model
from literature_reviewer.components.prompts.literature_search_query import generate_literature_search_query_sys_prompt, generate_initial_corpus_search_query_sys_prompt
from literature_reviewer.components.prompts.response_formats import SeedDataQueryList, S2QueryList


class UserMaterialsInput:
    def __init__(
        self,
        user_goals_txt,
        user_supplied_pdfs_directory,
        num_vec_db_queries=2,
        vec_db_query_num_results=1,
        num_s2_queries = 10,
        model_name="gpt-4o-mini",
        model_provider = "OpenAI",
    ):
        self.user_goals_txt = user_goals_txt
        self.user_supplied_pdfs_directory = user_supplied_pdfs_directory
        self.num_vec_db_queries = num_vec_db_queries
        self.vec_db_query_num_results = vec_db_query_num_results
        self.num_s2_queries = num_s2_queries
        self.model_name = model_name
        self.model_provider = model_provider
        
    def embed_user_supplied_pdfs(self):
        chunks_with_ids = LangchainPDFTextExtractor(
            self.user_supplied_pdfs_directory
        ).pdf_directory_to_chunks_with_ids()
        add_to_chromadb(chunks_with_ids)
        
    def search_initial_corpus_for_queries_based_on_goals(self):
        prompt_framework = PromptFramework.OAI_API
        chat_model = Model(self.model_name, self.model_provider)
        chat_interface = ModelInterface(prompt_framework, chat_model)
        vec_db_queries_raw = chat_interface.entry_chat_call(
            system_prompt=generate_initial_corpus_search_query_sys_prompt(self.num_vec_db_queries),
            user_prompt=self.user_goals_txt,
            response_format=SeedDataQueryList
        )
        vec_db_queries = json.loads(vec_db_queries_raw)["vec_db_queries"]        
        contexts = [
            query_chromadb(
                query_text=query,
                num_results=self.vec_db_query_num_results
            ) for query in vec_db_queries
        ]
        joined_context = "\n".join(contexts)
        semantic_scholar_queries = chat_interface.entry_chat_call(
            system_prompt=generate_literature_search_query_sys_prompt(self.num_s2_queries),
            user_prompt=joined_context + self.user_goals_txt,
            response_format=S2QueryList
        )

        
        # Pretty print the semantic_scholar_queries in JSON format
        print("SEMANTIC SCHOLAR QUERY LIST (Pretty JSON):")
        print(json.dumps(json.loads(semantic_scholar_queries), indent=4))

if __name__ == "__main__":
    user_goals_txt = "/home/christian/literature-reviewer/user_inputs/goal_prompt.txt"
    user_supplied_pdfs_directory = "/home/christian/literature-reviewer/input_pdfs"
    num_vec_db_queries = 3
    vec_db_query_num_results = 2
    num_s2_queries = 10
    model_name = "gpt-4o-mini"
    model_provider = "OpenAI"

    user_materials_input = UserMaterialsInput(
        user_goals_txt=user_goals_txt,
        user_supplied_pdfs_directory=user_supplied_pdfs_directory,
        num_vec_db_queries=num_vec_db_queries,
        vec_db_query_num_results=vec_db_query_num_results,
        num_s2_queries=num_s2_queries,
        model_name=model_name,
        model_provider=model_provider
    )

    user_materials_input.embed_user_supplied_pdfs()
    user_materials_input.search_initial_corpus_for_queries_based_on_goals()
