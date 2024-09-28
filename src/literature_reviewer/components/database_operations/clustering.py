"""
Handles dimensionality reduction and clustering for
trying to find themes in a corpus

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

from literature_reviewer.components.database_operations.chroma_operations import get_full_chromadb_collection
import numpy as np

class VectorDBClusteringTool:
    def __init__(
        self,
        num_clusters,
        reduced_dimensions,
        dimensionality_reduction_method,
        clustering_method,
        chroma_path: str = "chroma_db",
        model: str = "text-embedding-3-small"
    ):
        self.num_clusters = num_clusters,
        self.reduced_dimensions = reduced_dimensions
        self.dimensionality_reduction_method = dimensionality_reduction_method
        self.clustering_method = clustering_method
        self.chroma_path = chroma_path
        self.model = model
        self.chunk_ids = None
        self.embeddings = None
        self.reduced_embeddings = None
        self.chunks = None

    def load_data(self):
        collection = get_full_chromadb_collection()
        self.chunk_ids = collection.get("ids")
        self.embeddings = collection.get("embeddings")
        self.chunks = collection.get("documents")
        print(f"{len(collection['ids'])} Chunks Loaded")

    def reduce_dimensionality(self):
        if self.embeddings is None:
            raise ValueError("No embeddings found. Ensure successful call to load_data() first.")
        
        print(f"Data type for self.embeddings: {type(self.embeddings)}")
        print(f"Shape of self.embeddings: {self.embeddings.shape}")
        print("First 5 embeddings:")
        print(self.embeddings[:5])
        
        # Implement dimensionality reduction
        if self.dimensionality_reduction_method == "PCA":
            from sklearn.decomposition import PCA
            pca = PCA(n_components=self.reduced_dimensions)
            self.reduced_embeddings = pca.fit_transform(self.embeddings)
        elif self.dimensionality_reduction_method == "UMAP":
            import umap
            reducer = umap.UMAP(n_components=self.reduced_dimensions)
            self.reduced_embeddings = reducer.fit_transform(self.embeddings)
        elif self.dimensionality_reduction_method == "t-SNE":
            from sklearn.manifold import TSNE
            tsne = TSNE(n_components=self.reduced_dimensions)
            self.reduced_embeddings = tsne.fit_transform(self.embeddings)
        else:
            raise ValueError(f"Unsupported dimensionality reduction method: {self.dimensionality_reduction_method}")
        print(f"Dimensionality reduced from {self.embeddings.shape[1]} to {self.reduced_embeddings.shape[1]}")
        print(f"Data type for self.reduced_embeddings: {type(self.reduced_embeddings)}")
        print("First 5 reduced embeddings:")
        print(self.reduced_embeddings[:5])
    
    #TODO: this is sloppy, fix
    def form_clusters(self):
        if self.reduced_embeddings is None:
            raise ValueError("No reduced embeddings found. Ensure successful call to reduce_dimensionality() first.")

        import hdbscan

        # Create HDBSCAN clusterer
        self.clusterer = hdbscan.HDBSCAN(min_cluster_size=5, min_samples=3)
        
        # Fit the clusterer to the reduced embeddings
        self.cluster_labels = self.clusterer.fit_predict(self.reduced_embeddings)

        # Print clustering results
        unique_labels = set(self.cluster_labels)
        self.num_clusters = len(unique_labels) - (1 if -1 in unique_labels else 0)  # Exclude noise points
        print(f"Number of clusters formed: {self.num_clusters}")
        print(f"Number of noise points: {list(self.cluster_labels).count(-1)}")

    def get_plot_data(self):
        if self.reduced_embeddings is None or not hasattr(self, 'cluster_labels'):
            raise ValueError("Clustering has not been performed. Call reduce_dimensionality() and form_clusters() first.")
        
        return {
            'reduced_embeddings': self.reduced_embeddings,
            'cluster_labels': self.cluster_labels,
            'num_clusters': self.num_clusters,
            'chunk_ids': self.chunk_ids,
            'chunks': self.chunks
        }

if __name__ == "__main__":
    # Example usage
    clustering_tool = VectorDBClusteringTool(
        num_clusters=5,
        reduced_dimensions=50,
        dimensionality_reduction_method="PCA",
        clustering_method="KMeans",
    )
    clustering_tool.load_data()
    clustering_tool.reduce_dimensionality()
    
