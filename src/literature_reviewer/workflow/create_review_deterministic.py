"""
Top-level orchestration.

Handles doing tasks, moving around the flow building blocks.

May it generate useful ideas.
"""
import argparse, datetime, logging, os
from dotenv import load_dotenv
from literature_reviewer.tools import (
    cluster_analyzer,
    corpus_gatherer,
    research_query_generator,
    review_author
)
from literature_reviewer.agents.components.frameworks_and_models import PromptFramework

def create_literature_review(
    model_interface,
    title: str = "YOU FORGOT TO SPECIFY A TITLE, SILLY",
    chunk_size: int = 800,
    chunk_overlap: int = 80,
    vec_db_num_queries_to_create_s2_queries: int = 64,
    vec_db_query_num_results_per_query: int = 32,
    num_s2_queries_to_use: int = 16,
    s2_query_response_length_limit: int = 10,
    cluster_analyis_max_clusters_to_analyze: int = 999,
    cluster_analysis_num_keywords_per_cluster: int = 12,
    cluster_analysis_num_chunks_per_cluster: int = 12,
    cluster_analysis_reduced_embedding_dimensionality: int = 120,
    cluster_analyis_dimensionality_reduction_method: str = "PCA",
    cluster_analysis_clustering_method: str = "HDBSCAN",
):
    def print_and_confirm_parameters(**kwargs):
        print("Review parameters:")
        for key, value in kwargs.items():
            print(f"{key.replace('_', ' ').title()}: {value}")
        
        print("\nPress Enter to confirm and continue, or Ctrl+C to cancel...")
        while True:
            if input() == '':  # Enter key
                break
            
    print_and_confirm_parameters(**locals())
    
    #set paths for experiment
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_folder_name = f"{title}_{timestamp}"
    user_supplied_inputs_base_path = os.getenv("INPUTS_PATH")
    user_supplied_pdfs_path = os.path.join(user_supplied_inputs_base_path, "user_supplied_pdfs")
    user_supplid_goal_prompt_path = os.path.join(user_supplied_inputs_base_path, "goal_prompt.txt")
    framework_run_base_path = os.path.join(os.getenv("OUTPUT_PATH"), unique_folder_name)
    run_downloaded_pdfs_path = os.path.join(framework_run_base_path, "downloaded_pdfs")
    run_chromadb_path = os.path.join(framework_run_base_path, "chroma_db")
    run_writeup_materials_output_path = os.path.join(framework_run_base_path, "writeup")
    
    # Ensure all directories are present
    os.makedirs(user_supplied_inputs_base_path, exist_ok=True)
    os.makedirs(user_supplied_pdfs_path, exist_ok=True)
    os.makedirs(framework_run_base_path, exist_ok=True)
    os.makedirs(run_downloaded_pdfs_path, exist_ok=True)
    os.makedirs(run_chromadb_path, exist_ok=True)
    os.makedirs(run_writeup_materials_output_path, exist_ok=True)

    #load user goals
    with open(user_supplid_goal_prompt_path, "r") as file:
        user_goals_text = file.read()

    # Get semantic scholar queries
    semantic_scholar_queries = research_query_generator.ResearchQueryGenerator(
        user_goals_text=user_goals_text,
        user_supplied_pdfs_directory=user_supplied_pdfs_path,
        model_interface=model_interface,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        num_vec_db_queries=vec_db_num_queries_to_create_s2_queries,
        vec_db_query_num_results=vec_db_query_num_results_per_query,
        num_s2_queries=num_s2_queries_to_use,
        chromadb_path=run_chromadb_path,
    ).embed_initial_corpus_get_queries()
    print("QUERIES GENERATED")
    
    # Initialize and run CorpusGatherer to embed user info/pdfs
    approved_paper_ids = corpus_gatherer.CorpusGatherer(
        search_queries=semantic_scholar_queries,
        user_goals_text=user_goals_text,
        model_interface=model_interface,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        s2_query_response_length_limit=s2_query_response_length_limit,
        pdf_download_path=run_downloaded_pdfs_path,
        chromadb_path=run_chromadb_path,
    ).gather_and_embed_corpus()
    print(f"CORPUS GATHERED. {len(approved_paper_ids)} PAPERS EMBEDDED...")

    # Summarize Clusters in reduced-dimension embeddings
    clusters_summary = cluster_analyzer.ClusterAnalyzer(
        user_goals_text=user_goals_text,
        model_interface=model_interface,
        max_clusters_to_analyze=cluster_analyis_max_clusters_to_analyze,
        num_keywords_per_cluster=cluster_analysis_num_keywords_per_cluster,
        num_chunks_per_cluster=cluster_analysis_num_chunks_per_cluster,
        reduced_dimensions=cluster_analysis_reduced_embedding_dimensionality,
        dimensionality_reduction_method=cluster_analyis_dimensionality_reduction_method,
        clustering_method=cluster_analysis_clustering_method,
        chromadb_path=run_chromadb_path,
    ).perform_full_cluster_analysis()
    print("CLUSTERS ANALYZED")

        
    review_outline = review_author.ReviewAuthor(
        user_goals_text=user_goals_text,
        multi_cluster_summary=clusters_summary,
        materials_output_path=run_writeup_materials_output_path,
        model_interface=model_interface,
        theme_limit=os.getenv("DEFAULT_THEME_LIMIT"),
        chromadb_path=run_chromadb_path,
    ).generate_and_save_full_writeup_and_outlines()
    print("REVIEW MANUSCRIPT WRITTEN")
            
    # Writeup to reviewed writeup
    
    # Reviewed writeup to formatted pdf
    
    # Visualizations of the entire process, flow of information charts that are explorable.
    
    

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    from literature_reviewer.agents.components.model_call import ModelInterface
    from literature_reviewer.agents.components.frameworks_and_models import PromptFramework, Model

    
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Create a literature review")
    parser.add_argument("-t", "--title", type=str, help="Title of the literature review", required=True)
    args = parser.parse_args()

    # Load fresh env
    load_dotenv(override=True)
    
    # Set logging level
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    model_interface = ModelInterface(
        prompt_framework=PromptFramework.OAI_API,
        model=Model("gpt-4o-mini","OpenAI"),
    )
    # Call create_literature_review with the title argument
    create_literature_review(
        title=args.title,
        model_interface=model_interface,
        vec_db_num_queries_to_create_s2_queries = 2,
        vec_db_query_num_results_per_query = 2,
        num_s2_queries_to_use = 2,   
    )