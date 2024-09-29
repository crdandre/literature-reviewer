"""
Top-level orchestration
"""
import argparse, datetime, logging, os
from dotenv import load_dotenv
from literature_reviewer.orchestration import (
    get_initial_search_queries,
    gather_the_corpus,
    cluster_analysis,
    review_creation
)
from literature_reviewer.components.model_interaction.frameworks_and_models import PromptFramework

def create_literature_review(
    title: str = "YOU FORGOT TO SPECIFY A TITLE, SILLY",
    model_name: str = "gpt-4o-mini",
    model_provider: str = "OpenAI",
    vec_db_num_queries_to_create_s2_queries: int = 10,
    vec_db_query_num_results_per_query: int = 10,
    num_s2_queries_to_use: int = 10,
    corpus_gatherer_chunks_per_batch: int = 10,
    corpus_gatherer_inclusion_threshold: float = 0.85,
    cluster_analyis_max_clusters_to_analyze: int = 10,
    cluster_analysis_num_keywords_per_cluster: int = 10,
    cluster_analysis_num_chunks_per_cluster: int = 10,
    cluster_analysis_reduced_embedding_dimensionality: int = 200,
    cluster_analyis_dimensionality_reduction_method: str = "PCA",
    cluster_analysis_clustering_method: str = "HDBSCAN",
    
):
    def print_and_confirm_parameters(
        title, model_name, model_provider, vec_db_num_queries_to_create_s2_queries,
        vec_db_query_num_results_per_query, num_s2_queries_to_use,
        corpus_gatherer_chunks_per_batch, corpus_gatherer_inclusion_threshold,
        cluster_analyis_max_clusters_to_analyze, cluster_analysis_num_keywords_per_cluster,
        cluster_analysis_num_chunks_per_cluster, cluster_analysis_reduced_embedding_dimensionality,
        cluster_analyis_dimensionality_reduction_method, cluster_analysis_clustering_method
    ):
        print("Review parameters:")
        print(f"Title: {title}")
        print(f"Model Name: {model_name}")
        print(f"Model Provider: {model_provider}")
        print(f"Vector DB Queries to Create S2 Queries: {vec_db_num_queries_to_create_s2_queries}")
        print(f"Vector DB Query Results per Query: {vec_db_query_num_results_per_query}")
        print(f"Number of S2 Queries to Use: {num_s2_queries_to_use}")
        print(f"Corpus Gatherer Chunks per Batch: {corpus_gatherer_chunks_per_batch}")
        print(f"Corpus Gatherer Inclusion Threshold: {corpus_gatherer_inclusion_threshold}")
        print(f"Max Clusters to Analyze: {cluster_analyis_max_clusters_to_analyze}")
        print(f"Number of Keywords per Cluster: {cluster_analysis_num_keywords_per_cluster}")
        print(f"Number of Chunks per Cluster: {cluster_analysis_num_chunks_per_cluster}")
        print(f"Reduced Embedding Dimensionality: {cluster_analysis_reduced_embedding_dimensionality}")
        print(f"Dimensionality Reduction Method: {cluster_analyis_dimensionality_reduction_method}")
        print(f"Clustering Method: {cluster_analysis_clustering_method}")
        
        print("\nPress Enter to confirm and continue, or ESC to cancel...")
        while True:
            key = input()
            if key == '\x1b':  # ESC key
                print("Run cancelled.")
                exit()
            elif key == '':  # Enter key
                break

    print_and_confirm_parameters(
        title, model_name, model_provider, vec_db_num_queries_to_create_s2_queries,
        vec_db_query_num_results_per_query, num_s2_queries_to_use,
        corpus_gatherer_chunks_per_batch, corpus_gatherer_inclusion_threshold,
        cluster_analyis_max_clusters_to_analyze, cluster_analysis_num_keywords_per_cluster,
        cluster_analysis_num_chunks_per_cluster, cluster_analysis_reduced_embedding_dimensionality,
        cluster_analyis_dimensionality_reduction_method, cluster_analysis_clustering_method
    )
    
    #set paths for experiment
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_folder_name = f"{title}_{timestamp}"

    #user-supplied materials
    user_supplied_inputs_base_path = os.getenv("INPUTS_PATH")
    user_supplied_pdfs_path = os.path.join(user_supplied_inputs_base_path, "user_supplied_pdfs")
    user_supplid_goal_prompt_path = os.path.join(user_supplied_inputs_base_path, "goal_prompt.txt")
    with open(user_supplid_goal_prompt_path, "r") as file:
        user_goals_text = file.read()
    
    #created materials
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

    # Get semantic scholar queries
    semantic_scholar_queries = get_initial_search_queries.UserMaterialsInput(
        user_goals_text=user_goals_text,
        user_supplied_pdfs_directory=user_supplied_pdfs_path,
        num_vec_db_queries=vec_db_num_queries_to_create_s2_queries,
        vec_db_query_num_results=vec_db_query_num_results_per_query,
        num_s2_queries=num_s2_queries_to_use,
        prompt_framework=PromptFramework[os.getenv("DEFAULT_PROMPT_FRAMEWORK")],
        model_name=model_name,
        model_provider=model_provider,
        chromadb_path=run_chromadb_path,
    ).embed_initial_corpus_get_queries()
    
    # Initialize and run CorpusGatherer to embed user info/pdfs
    gather_the_corpus.CorpusGatherer(
        search_queries=semantic_scholar_queries,
        user_goals_text=user_goals_text,
        batch_size=corpus_gatherer_chunks_per_batch,
        inclusion_threshold=corpus_gatherer_inclusion_threshold,
        pdf_download_path=run_downloaded_pdfs_path,
        prompt_framework=PromptFramework[os.getenv("DEFAULT_PROMPT_FRAMEWORK")],
        model_name=model_name,
        model_provider=model_provider,
        chromadb_path=run_chromadb_path,
    ).gather_and_embed_corpus()

    # Summarize Clusters in reduced-dimension embeddings
    clusters_summary = cluster_analysis.ClusterAnalyzer(
        user_goals_text=user_goals_text,
        max_clusters_to_analyze=cluster_analyis_max_clusters_to_analyze,
        num_keywords_per_cluster=cluster_analysis_num_keywords_per_cluster,
        num_chunks_per_cluster=cluster_analysis_num_chunks_per_cluster,
        reduced_dimensions=cluster_analysis_reduced_embedding_dimensionality,
        dimensionality_reduction_method=cluster_analyis_dimensionality_reduction_method,
        clustering_method=cluster_analysis_clustering_method,
        prompt_framework=PromptFramework[os.getenv("DEFAULT_PROMPT_FRAMEWORK")],
        model_name=model_name,
        model_provider=model_provider,
        chromadb_path=run_chromadb_path,
    ).perform_full_cluster_analysis()

        
    review_outline = review_creation.ReviewAuthor(
        user_goals_text=user_goals_text,
        multi_cluster_summary=clusters_summary,
        materials_output_path=run_writeup_materials_output_path,
        theme_limit=os.getenv("DEFAULT_THEME_LIMIT"),
        prompt_framework=PromptFramework[os.getenv("DEFAULT_PROMPT_FRAMEWORK")],
        model_name=model_name,
        model_provider=model_provider,
        chromadb_path=run_chromadb_path,
    ).generate_and_save_full_writeup_and_outlines()
    
    print(review_outline)
    
    # Outline to writeup
    
    # Writeup to reviewed writeup
    
    # Reviewed writeup to formatted pdf
    
    # Visualizations of the entire process, flow of information charts that are explorable.
    
    

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Create a literature review")
    parser.add_argument("-t", "--title", type=str, help="Title of the literature review", required=True)
    args = parser.parse_args()

    # Load fresh env
    load_dotenv(override=True)
    
    # Set logging level
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Call create_literature_review with the title argument
    create_literature_review(title=args.title)
