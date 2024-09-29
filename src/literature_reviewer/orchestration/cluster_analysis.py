"""
Given the cluster output, analyze the clusters.

Loose plan:

Cluster Analysis / Theme Identification
---------------------------------------
1. Find main themes: find densest clusters / most frequent keywords or sentence themes
2. LLM generates cluster summary of N chunks or papers closest to the cluster centroid and estimates the theme
3. Output is a list of summary dictionary containing the chunk ids involved in the summary and the summary text itself.


Theme Characterization / Connection
-----------------------------------
1. Given a set of cluster summaries, LLM summarises each theme, the connections between them, context for the themes within the field, noting what might be novel or yet to be investigated
2. Output is a list of overarching theme dictionaries containing the indices of the summary dictionary objects from the prior step, and the overarching summary text itself.

Gaps
----

Questions
---------

Future Directions
-----------------

Other Considerations
--------------------
- Connect to user_goals or any other intermediate step?
"""
import os
import logging
from literature_reviewer.components.database_operations.clustering import VectorDBClusteringTool
from literature_reviewer.components.prompts.cluster_analysis import (
    generate_single_cluster_theme_summary_sys_prompt,
    generate_multi_cluster_theme_summary_sys_prompt
)
from literature_reviewer.components.model_interaction.model_call import ModelInterface
from literature_reviewer.components.model_interaction.frameworks_and_models import (
    PromptFramework,
    Model,
)
from literature_reviewer.components.prompts.response_formats import (
    SingleClusterSummary,
    MultiClusterSummary
)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ClusterAnalyzer:
    def __init__(
        self,
        user_goals_text,
        max_clusters_to_analyze,
        num_keywords_per_cluster,
        num_chunks_per_cluster,
        reduced_dimensions,
        dimensionality_reduction_method,
        clustering_method,
        prompt_framework=None,
        model_name=None,
        model_provider=None,
    ):
        self.user_goals_text = user_goals_text
        self.max_clusters_to_analyze = max_clusters_to_analyze
        self.num_keywords_per_cluster = num_keywords_per_cluster
        self.num_chunks_per_cluster = num_chunks_per_cluster
        self.reduced_dimensions = reduced_dimensions
        self.dimensionality_reduction_method = dimensionality_reduction_method
        self.clustering_method = clustering_method
        self.prompt_framework = prompt_framework or PromptFramework[os.getenv("DEFAULT_PROMPT_FRAMEWORK")]
        self.model_name = model_name or os.getenv("DEFAULT_MODEL_NAME")
        self.model_provider = model_provider or os.getenv("DEFAULT_MODEL_PROVIDER")
        #assigned internally
        self.cluster_data = None
        self.cluster_summaries = None

    def set_cluster_data(self):
        logger.info("Setting cluster data...")
        self.cluster_data = VectorDBClusteringTool(
            num_keywords_per_cluster=self.num_keywords_per_cluster,
            num_chunks_per_cluster=self.num_chunks_per_cluster,
            reduced_dimensions=self.reduced_dimensions,
            dimensionality_reduction_method=self.dimensionality_reduction_method,
            clustering_method=self.clustering_method,
        ).process_and_get_cluster_data()
        logger.info("Cluster data set successfully.")
        
    def summarize_each_cluster(self):
        """
        Summarize the theme of each cluster using the top keywords and chunks.
        """
        logger.info("Starting cluster summarization...")
        system_prompt = generate_single_cluster_theme_summary_sys_prompt(self.user_goals_text)
        chat_model = Model(self.model_name, self.model_provider)
        chat_interface = ModelInterface(self.prompt_framework, chat_model)

        cluster_summaries = {}
        total_clusters = len(self.cluster_data['top_keywords_per_cluster'])
        clusters_to_analyze = min(self.max_clusters_to_analyze, total_clusters)

        for i, (cluster, keywords) in enumerate(list(self.cluster_data['top_keywords_per_cluster'].items())[:clusters_to_analyze], 1):
            logger.info(f"Summarizing cluster {i}/{clusters_to_analyze} (out of {total_clusters} total clusters)")
            chunks = self.cluster_data['top_chunks_per_cluster'].get(cluster, [])
            
            # Prepare the input for the LLM
            keywords_str = ", ".join(keywords)
            chunks_str = "\n\n".join(chunks)
            input_text = f"Keywords: {keywords_str}\n\nTop Chunks:\n{chunks_str}"

            # Get the summary from the LLM
            summary = chat_interface.entry_chat_call(
                system_prompt=system_prompt,
                user_prompt=input_text,
                response_format=SingleClusterSummary
            )

            cluster_summaries[cluster] = summary
            logger.info(f"Cluster {i}/{clusters_to_analyze} summarized")

        self.cluster_summaries = cluster_summaries
        logger.info(f"Summarized {clusters_to_analyze} out of {total_clusters} clusters successfully.")
        return cluster_summaries
    
    
    def summarize_cluster_summaries(self):
        """
        Generate an overarching summary of all cluster summaries.
        """
        system_prompt = generate_multi_cluster_theme_summary_sys_prompt(self.user_goals_text)
        chat_model = Model(self.model_name, self.model_provider)
        chat_interface = ModelInterface(self.prompt_framework, chat_model)

        # Prepare the input for the LLM
        cluster_summaries_str = "\n\n".join([
            f"Cluster {cluster}:\n{summary}"  # Remove .json() call
            for cluster, summary in self.cluster_summaries.items()
        ])
        input_text = f"Cluster Summaries:\n{cluster_summaries_str}"

        # Get the multi-cluster summary from the LLM
        multi_cluster_summary = chat_interface.entry_chat_call(
            system_prompt=system_prompt,
            user_prompt=input_text,
            response_format=MultiClusterSummary
        )

        self.multi_cluster_summary = multi_cluster_summary
        logger.info("Overarching summary of cluster summaries generated successfully.")
        return multi_cluster_summary

# example usage
if __name__ == "__main__":
    import json
    import pprint
    from dotenv import load_dotenv
    load_dotenv()
    
    print("Starting cluster analysis...")

    with open("/home/christian/literature-reviewer/user_inputs/goal_prompt.txt", "r") as file:
        user_goals_text = file.read()
    
    # Example usage
    cluster_analyzer = ClusterAnalyzer(
        user_goals_text=user_goals_text,
        max_clusters_to_analyze=5,
        num_keywords_per_cluster=5,
        num_chunks_per_cluster=5,
        reduced_dimensions=200,
        dimensionality_reduction_method="PCA",
        clustering_method="HDBSCAN"
    )
    
    cluster_analyzer.set_cluster_data()
    
    cluster_analyzer.summarize_each_cluster()
    print("Cluster summaries generated:")
    print("Cluster summaries:")
    colors = ['\033[91m', '\033[92m', '\033[93m', '\033[94m', '\033[95m', '\033[96m']  # ANSI color codes
    reset_color = '\033[0m'
    
    for i, (cluster, summary) in enumerate(cluster_analyzer.cluster_summaries.items()):
        color = colors[i % len(colors)]
        print(f"{color}Cluster {cluster}:")
        print(pprint.pformat(summary, indent=2, width=120))
        print("")  # Add a blank line between clusters for readability
    
    
    multi_cluster_summary = cluster_analyzer.summarize_cluster_summaries()
    
    print(f"{color}Multi-cluster summary:")
    color = '\033[96m'  # Cyan color for multi-cluster summary
        
    try:
        # Attempt to parse the string as JSON
        summary_dict = json.loads(multi_cluster_summary)
        
        print("Overall Summary Narrative:")
        print(pprint.pformat(summary_dict["overall_summary_narrative"], indent=2, width=120))
        print("\nThemes:")
        for theme in summary_dict["themes"]:
            print(f"- {theme}")
    except json.JSONDecodeError:
        # If parsing fails, print the raw string
        print("Raw multi-cluster summary:")
        print(pprint.pformat(multi_cluster_summary, indent=2, width=120))
    
    print(reset_color)
    
    print("Cluster analysis completed.")

