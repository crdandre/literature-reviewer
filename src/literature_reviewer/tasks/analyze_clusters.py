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
from literature_reviewer.components.input_output_models.response_formats import (
    SingleClusterSummary,
    MultiClusterSummary
)


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
        chromadb_path=None,
    ):
        self.user_goals_text = user_goals_text
        self.max_clusters_to_analyze = max_clusters_to_analyze
        self.num_keywords_per_cluster = num_keywords_per_cluster
        self.num_chunks_per_cluster = num_chunks_per_cluster
        self.reduced_dimensions = reduced_dimensions
        self.dimensionality_reduction_method = dimensionality_reduction_method
        self.clustering_method = clustering_method
        self.prompt_framework = prompt_framework or PromptFramework[os.getenv("DEFAULT_PROMPT_FRAMEWORK")]
        self.model_name = model_name
        self.model_provider = model_provider
        self.chromadb_path = chromadb_path
        #assigned internally
        self.cluster_data = None
        self.cluster_summaries = None

    def set_cluster_data(self):
        logging.info("Setting cluster data...")
        self.cluster_data = VectorDBClusteringTool(
            num_keywords_per_cluster=self.num_keywords_per_cluster,
            num_chunks_per_cluster=self.num_chunks_per_cluster,
            reduced_dimensions=self.reduced_dimensions,
            dimensionality_reduction_method=self.dimensionality_reduction_method,
            clustering_method=self.clustering_method,
            chroma_path=self.chromadb_path
        ).process_and_get_cluster_data()

        
    def summarize_each_cluster(self):
        """
        Summarize the theme of each cluster using the top keywords and chunks.
        """
        logging.info("Starting cluster summarization...")
        system_prompt = generate_single_cluster_theme_summary_sys_prompt(self.user_goals_text)
        chat_model = Model(self.model_name, self.model_provider)
        chat_interface = ModelInterface(self.prompt_framework, chat_model)

        cluster_summaries = {}
        total_clusters = len(self.cluster_data['top_keywords_per_cluster'])
        clusters_to_analyze = min(self.max_clusters_to_analyze, total_clusters)

        for i, (cluster, keywords) in enumerate(list(self.cluster_data['top_keywords_per_cluster'].items())[:clusters_to_analyze], 1):
            logging.info(f"Summarizing cluster {i}/{clusters_to_analyze} (out of {total_clusters} total clusters)")
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
            logging.info(f"Cluster {i}/{clusters_to_analyze} summarized")
            logging.debug(f"SUMMARY: {summary}")

        self.cluster_summaries = cluster_summaries
        return cluster_summaries
    
    
    def summarize_cluster_summaries(self):
        """
        Generate an overarching summary of all cluster summaries, including themes,
        gaps, unanswered questions, and future directions.
        """
        system_prompt = generate_multi_cluster_theme_summary_sys_prompt(self.user_goals_text)
        chat_model = Model(self.model_name, self.model_provider)
        chat_interface = ModelInterface(self.prompt_framework, chat_model)

        # Prepare the input for the LLM
        cluster_summaries_str = "\n\n".join([
            f"Cluster {cluster}:\n{summary}"
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
        return multi_cluster_summary
    
    
    def perform_full_cluster_analysis(self):
        """
        Performs the full cluster analysis process by calling set_cluster_data,
        summarize_each_cluster, and summarize_cluster_summaries in sequence.
        
        Returns:
            MultiClusterSummary: The result of summarize_cluster_summaries.
        """
        logging.info("Starting full cluster analysis...")
        
        # Step 1: Set cluster data
        self.set_cluster_data()
        logging.info("Cluster data set successfully.")
        
        # Step 2: Summarize each cluster
        cluster_summaries = self.summarize_each_cluster()
        logging.info(f"Generated summaries for {len(cluster_summaries)} clusters.")
        
        # Step 3: Summarize cluster summaries
        multi_cluster_summary = self.summarize_cluster_summaries()
        logging.info("Multi-cluster summary generated successfully.")
        
        return multi_cluster_summary

# example usage
if __name__ == "__main__":
    import json
    import pprint
    from dotenv import load_dotenv
    load_dotenv(override=True)
    
    print("Starting cluster analysis...")

    with open("/home/christian/literature-reviewer/user_inputs/goal_prompt.txt", "r") as file:
        user_goals_text = file.read()
    
    # Example usage
    cluster_analyzer = ClusterAnalyzer(
        user_goals_text=user_goals_text,
        max_clusters_to_analyze=2,
        num_keywords_per_cluster=5,
        num_chunks_per_cluster=5,
        reduced_dimensions=100,
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
    
    print("\n")
    print(f"{colors[0]}\n================================================")
    print("Multi-cluster summary:")
    print("================================================\n")
    try:
        # Attempt to parse the string as JSON
        summary_dict = json.loads(multi_cluster_summary)
        
        print(f"{colors[1]}Overall Summary Narrative:")
        print(pprint.pformat(summary_dict["overall_summary_narrative"], indent=2, width=120))
        
        print(f"\n{colors[2]}Themes:")
        for theme in summary_dict["themes"]:
            print(f"- {theme}")
        
        print(f"\n{colors[3]}Gaps:")
        for gap in summary_dict["gaps"]:
            print(f"- {gap}")
        
        print(f"\n{colors[4]}Unanswered Questions:")
        for question in summary_dict["unanswered_questions"]:
            print(f"- {question}")
        
        print(f"\n{colors[5]}Future Directions:")
        for direction in summary_dict["future_directions"]:
            print(f"- {direction}")
    except json.JSONDecodeError:
        # If parsing fails, print the raw string
        print("Raw multi-cluster summary:")
        print(pprint.pformat(multi_cluster_summary, indent=2, width=120))
    
    print(reset_color)
    print("Cluster analysis completed.")

