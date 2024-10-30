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
from literature_reviewer.tools.basetool import BaseTool, ToolResponse
from literature_reviewer.tools.components.database_operations.clustering import VectorDBClusteringTool
from literature_reviewer.tools.components.prompts.cluster_analysis import (
    generate_single_cluster_theme_summary_sys_prompt,
    generate_multi_cluster_theme_summary_sys_prompt
)
from literature_reviewer.agents.components.model_call import ModelInterface
from literature_reviewer.agents.components.frameworks_and_models import Model
from literature_reviewer.tools.components.input_output_models.response_formats import (
    SingleClusterSummary,
    MultiClusterSummary
)
import logging
from typing import Any

class ClusterAnalyzer(BaseTool):
    def __init__(
        self,
        model_interface: ModelInterface,
        user_goals_text: str,
        max_clusters_to_analyze: int,
        num_keywords_per_cluster: int,
        num_chunks_per_cluster: int,
        reduced_dimensions: int,
        dimensionality_reduction_method: str,
        clustering_method: str,
        chromadb_path: str = None,
    ):
        super().__init__(
            model_interface=model_interface
        )
        self.user_goals_text = user_goals_text
        self.max_clusters_to_analyze = max_clusters_to_analyze
        self.num_keywords_per_cluster = num_keywords_per_cluster
        self.num_chunks_per_cluster = num_chunks_per_cluster
        self.reduced_dimensions = reduced_dimensions
        self.dimensionality_reduction_method = dimensionality_reduction_method
        self.clustering_method = clustering_method
        self.chromadb_path = chromadb_path
        self.cluster_data = None
        self.cluster_summaries = None

    def use(self, step: Any) -> ToolResponse:
        try:
            multi_cluster_summary = self.perform_full_cluster_analysis()
            return ToolResponse(
                output=str(multi_cluster_summary),
                explanation="Successfully performed cluster analysis and generated summaries."
            )
        except Exception as e:
            return ToolResponse(
                output="",
                explanation=f"Error during cluster analysis: {str(e)}"
            )

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
            summary = self.model_interface.chat_completion_call(
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

        # Prepare the input for the LLM
        cluster_summaries_str = "\n\n".join([
            f"Cluster {cluster}:\n{summary}"
            for cluster, summary in self.cluster_summaries.items()
        ])
        input_text = f"Cluster Summaries:\n{cluster_summaries_str}"

        # Get the multi-cluster summary from the LLM
        multi_cluster_summary = self.model_interface.chat_completion_call(
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
