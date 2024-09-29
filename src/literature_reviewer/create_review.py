"""
Top-level orchestration
"""
from dotenv import load_dotenv
import logging
import os
from literature_reviewer.orchestration import (
    get_initial_search_queries,
    gather_the_corpus,
    cluster_analysis,
    review_creation
)

def create_literature_review():
    # Read user goals
    with open("/home/christian/literature-reviewer/user_inputs/goal_prompt.txt", "r") as file:
        user_goals_text = file.read()

    # Get semantic scholar queries
    semantic_scholar_queries = get_initial_search_queries.UserMaterialsInput(
        user_goals_text=user_goals_text,
        user_supplied_pdfs_directory="/home/christian/literature-reviewer/input_pdfs",
        num_vec_db_queries=1,
        vec_db_query_num_results=1,
        num_s2_queries=1,
        model_name=os.getenv("DEFAULT_MODEL_NAME"),
        model_provider=os.getenv("DEFAULT_MODEL_PROVIDER")
    ).embed_initial_corpus_get_queries()

    # Initialize and run CorpusGatherer to embed user info/pdfs
    gather_the_corpus.CorpusGatherer(
        search_queries=semantic_scholar_queries,
        user_goals_text=user_goals_text,
        batch_size=12,
        inclusion_threshold=0.85,
        pdf_download_path=os.getenv("PDF_DOWNLOAD_PATH"),
        model_name=os.getenv("DEFAULT_MODEL_NAME"),
        model_provider=os.getenv("DEFAULT_MODEL_PROVIDER"),
        vector_db_path=os.getenv("CHROMA_DB_PATH"),
    ).gather_and_embed_corpus()

    # Summarize Clusters in reduced-dimension embeddings
    clusters_summary = cluster_analysis.ClusterAnalyzer(
        user_goals_text=user_goals_text,
        max_clusters_to_analyze=1,
        num_keywords_per_cluster=1,
        num_chunks_per_cluster=1,
        reduced_dimensions=50,
        dimensionality_reduction_method="PCA",
        clustering_method="HDBSCAN"
    ).perform_full_cluster_analysis()
    
    review_outline = review_creation.ReviewAuthor(
        user_goals_text=user_goals_text,
        multi_cluster_summary=clusters_summary,
        theme_limit=os.getenv("DEFAULT_THEME_LIMIT")
    ).create_structured_outline()
    
    print(review_outline)
    
    # Outline to writeup
    
    # Writeup to reviewed writeup
    
    # Reviewed writeup to formatted pdf
    
    # Visualizations of the entire process, flow of information charts that are explorable.
    
    

if __name__ == "__main__":
    #load fresh env
    load_dotenv(override=True)
    
    #set logging level
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    create_literature_review()
