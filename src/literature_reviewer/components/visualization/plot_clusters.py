"""
This file handles plotting the clustering result created
in ../database_operations/clustering.py
"""

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from literature_reviewer.components.database_operations.clustering import VectorDBClusteringTool

def plot_clusters(clustering_tool: VectorDBClusteringTool):
    plot_data = clustering_tool.get_plot_data()
    
    reduced_embeddings = plot_data['reduced_embeddings']
    cluster_labels = plot_data['cluster_labels']
    num_clusters = plot_data['num_clusters']

    # Create a 2D or 3D plot based on the number of dimensions
    if reduced_embeddings.shape[1] == 2:
        plt.figure(figsize=(10, 8))
        scatter = plt.scatter(reduced_embeddings[:, 0], reduced_embeddings[:, 1], c=cluster_labels, cmap='viridis')
        plt.colorbar(scatter)
        plt.title(f'2D Cluster Visualization ({num_clusters} clusters)')
        plt.xlabel('Dimension 1')
        plt.ylabel('Dimension 2')
        filename = 'cluster_visualization_2d.png'
    elif reduced_embeddings.shape[1] == 3:
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')
        scatter = ax.scatter(reduced_embeddings[:, 0], reduced_embeddings[:, 1], reduced_embeddings[:, 2], c=cluster_labels, cmap='viridis')
        fig.colorbar(scatter)
        ax.set_title(f'3D Cluster Visualization ({num_clusters} clusters)')
        ax.set_xlabel('Dimension 1')
        ax.set_ylabel('Dimension 2')
        ax.set_zlabel('Dimension 3')
        filename = 'cluster_visualization_3d.png'
    else:
        raise ValueError("Reduced embeddings should have 2 or 3 dimensions for visualization")

    # Save the plot as an image in the current working directory
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Plot saved as {filename}")


if __name__ == "__main__":
    # Example usage
    clustering_tool = VectorDBClusteringTool(
        num_clusters=5,
        reduced_dimensions=2,  # Change to 2 for 2D visualization
        dimensionality_reduction_method="PCA",
        clustering_method="HDBSCAN",
    )
    clustering_tool.load_data()
    clustering_tool.reduce_dimensionality()
    clustering_tool.form_clusters()
    plot_clusters(clustering_tool)