"""
Top-level orchestration
"""

from literature_reviewer.orchestration import (
    get_initial_search_queries,
    gather_the_corpus
)
import json
import os
from dotenv import load_dotenv

def create_literature_review():
    # Load environment variables
    load_dotenv()

    # Read user goals
    with open("/home/christian/literature-reviewer/user_inputs/goal_prompt.txt", "r") as file:
        user_goals_text = file.read()

    # Initialize UserMaterialsInput
    user_materials_input = get_initial_search_queries.UserMaterialsInput(
        user_goals_text=user_goals_text,
        user_supplied_pdfs_directory="/home/christian/literature-reviewer/input_pdfs",
        num_vec_db_queries=3,
        vec_db_query_num_results=2,
        num_s2_queries=10,
        model_name=os.getenv("DEFAULT_MODEL_NAME"),
        model_provider=os.getenv("DEFAULT_MODEL_PROVIDER")
    )

    # Embed user-supplied PDFs and generate initial search queries
    user_materials_input.embed_user_supplied_pdfs()
    semantic_scholar_queries = user_materials_input.search_initial_corpus_for_queries_based_on_goals()

    # Parse the JSON string to get the list of queries
    query_objects = json.loads(semantic_scholar_queries)["s2_queries"]
    queries = [obj.get('query') for obj in query_objects]

    # Initialize CorpusGatherer
    corpus_gatherer = gather_the_corpus.CorpusGatherer(
        search_queries=queries,
        user_goals_text=user_goals_text
    )

    # Search Semantic Scholar and process results
    search_results = corpus_gatherer.search_s2_for_queries()
    formatted_search_results, all_chunks_with_ids = corpus_gatherer.populate_s2_search_results_text(search_results)

    # Evaluate and filter search results
    approved_paper_ids = corpus_gatherer.evaluate_formatted_s2_results(
        results=formatted_search_results,
        batch_size=12,
        inclusion_threshold=0.85
    )

    # Embed approved search results into the database
    corpus_gatherer.embed_approved_search_results(
        approved_paper_ids=approved_paper_ids,
        all_chunks_with_ids=all_chunks_with_ids
    )
    
    # Create prompts to write a literature review using the embedded database
    # RAG HERE
    # maybe use the user_goals, along with any other interesting questions, to craft a list of the final review themes
    # this might use intermediate materials, user_goals, and direct searches to the database
    # can i reasonably ask this database "what are the main themes of the papers you have?"
    # I think i'd need more targeted vectors than that but not sure.
    
    """
    Claude and 
    https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10541641/
    https://ieeexplore.ieee.org/document/8851280
    as inspiration so far
    TF-IDF use somewhere?
    1. Dimensionality Reduction (optional? if so, PaCMAP, UMAP, t-SNE, PCA, SVD, Autoencoder)
    2. Clustering embeddings from (1) using techniques such as HDBSCAN
        a. choose a clustering algorithm
        b. determine optimal number of clusters if this helps
        c. assigning to clusters based on membership value maybe?
    3. Cluster analysis to identify themes (visualize clusters, i.e. t-SNE plots)
        a. further reduced dimensionality
    """
    
    
    # Themes to outline
    
    # Outline to writeup
    
    # Writeup to reviewed writeup
    
    # Reviewed writeup to formatted pdf
    
    # Visualizations of the entire process, flow of information charts that are explorable.
    
    

if __name__ == "__main__":
    create_literature_review()
