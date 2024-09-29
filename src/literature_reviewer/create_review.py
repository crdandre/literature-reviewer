"""
Top-level orchestration
"""

from literature_reviewer.orchestration import (
    get_initial_search_queries,
    gather_the_corpus,
    cluster_analysis,
)
import json
import os
import pprint
from dotenv import load_dotenv

def create_literature_review():
    # Load environment variables
    load_dotenv()

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
        inclusion_threshold=0.85
    ).gather_and_embed_corpus()


    clusters_summary = cluster_analysis.ClusterAnalyzer(
        user_goals_text=user_goals_text,
        max_clusters_to_analyze=1,
        num_keywords_per_cluster=1,
        num_chunks_per_cluster=1,
        reduced_dimensions=100,
        dimensionality_reduction_method="PCA",
        clustering_method="HDBSCAN"
    ).perform_full_cluster_analysis()
    
    
    # TEMP
    # Pretty print clusters_summary

    print("\nClusters Summary:")
    print("=================\n")

    try:
        # Attempt to parse the string as JSON
        summary_dict = json.loads(clusters_summary)
        
        # Use pprint for a formatted output
        pprint.pprint(summary_dict, indent=2, width=120)
    except json.JSONDecodeError:
        # If parsing fails, print the raw string
        print("Raw clusters summary:")
        pprint.pprint(clusters_summary, indent=2, width=120)
    
    # Themes to outline
    
    # Outline to writeup
    
    # Writeup to reviewed writeup
    
    # Reviewed writeup to formatted pdf
    
    # Visualizations of the entire process, flow of information charts that are explorable.
    
    

if __name__ == "__main__":
    create_literature_review()
