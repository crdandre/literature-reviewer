"""
Handles dimensionality reduction and clustering for
trying to find themes in a corpus

Claude and 
https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10541641/
https://ieeexplore.ieee.org/document/8851280
as inspiration so far
TF-IDF use somewhere?
1. Dimensionality Reduction (optional? if using it, PaCMAP, UMAP, t-SNE, PCA, SVD, Autoencoder)
2. Clustering embeddings from (1) using techniques such as HDBSCAN
3. Cluster analysis to identify themes (visualize clusters, i.e. t-SNE plots)
    a. further reduced dimensionality
    
Todo:
- Collapse redundant logic
- Solidity clustering logic with hdbscan    

"""
from collections import defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

from literature_reviewer.tools.components.database_operations.chroma_operations import get_full_chromadb_collection


class VectorDBClusteringTool:
    def __init__(
        self,
        num_keywords_per_cluster,
        num_chunks_per_cluster,
        reduced_dimensions,
        dimensionality_reduction_method: str = "PCA",
        clustering_method: str = "",
        chroma_path: str = "chroma_db",
        model: str = "text-embedding-3-small"
    ):
        self.num_keywords_per_cluster = num_keywords_per_cluster
        self.num_chunks_per_cluster = num_chunks_per_cluster
        self.reduced_dimensions = reduced_dimensions
        self.dimensionality_reduction_method = dimensionality_reduction_method
        self.clustering_method = clustering_method
        self.chroma_path = chroma_path
        self.model = model
        
        #defined internally
        self.num_clusters = None
        self.chunk_ids = None
        self.embeddings = None
        self.reduced_embeddings = None
        self.chunks = None
        self.top_keywords = None
        self.top_chunks = None

    def load_data(self):
        collection = get_full_chromadb_collection(chroma_path=self.chroma_path)
        self.chunk_ids = collection.get("ids")
        self.embeddings = collection.get("embeddings")
        self.chunks = collection.get("documents")
        print(f"{len(collection['ids'])} Chunks Loaded")

    def reduce_dimensionality(self):
        if self.embeddings is None:
            raise ValueError("No embeddings found. Ensure successful call to load_data() first.")
                
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

    
    #TODO: this is sloppy, fix
    def form_clusters(self):
        if self.reduced_embeddings is None:
            raise ValueError("No reduced embeddings found. Ensure successful call to reduce_dimensionality() first.")

        if self.clustering_method == "HDBSCAN":
            import hdbscan
            # Create HDBSCAN clusterer
            self.clusterer = hdbscan.HDBSCAN(min_cluster_size=5, min_samples=3)
            # Fit the clusterer to the reduced embeddings
            self.cluster_labels = self.clusterer.fit_predict(self.reduced_embeddings)
            # Print clustering results
            unique_labels = set(self.cluster_labels)
            self.num_clusters = len(unique_labels) - (1 if -1 in unique_labels else 0)  # Exclude noise points
        else:
            raise ValueError(f"Unsupported clustering method: {self.clustering_method}")
        
        print(f"Number of clusters formed: {self.num_clusters}")
        print(f"Number of noise points: {list(self.cluster_labels).count(-1)}")


    def extract_top_keywords_per_cluster(self):
        if self.chunks is None or not hasattr(self, 'cluster_labels'):
            raise ValueError("Clustering has not been performed. Call process_and_get_cluster_data() first.")

        # Group chunks by cluster
        cluster_chunks = defaultdict(list)
        for chunk, label in zip(self.chunks, self.cluster_labels):
            cluster_chunks[label].append(chunk)

        # Initialize TF-IDF vectorizer
        vectorizer = TfidfVectorizer(stop_words='english')

        cluster_keywords = {}
        for cluster, texts in cluster_chunks.items():
            if cluster == -1:  # Skip noise points
                continue

            # Fit and transform the texts for this cluster
            tfidf_matrix = vectorizer.fit_transform(texts)

            # Get feature names (words)
            feature_names = vectorizer.get_feature_names_out()

            # Calculate the average TF-IDF score for each word across all documents in the cluster
            word_scores = tfidf_matrix.sum(axis=0).A1

            # Sort words by score and get top N
            n = self.num_keywords_per_cluster
            top_indices = word_scores.argsort()[-n:][::-1]
            top_words = [feature_names[i] for i in top_indices]

            cluster_keywords[cluster] = top_words

        self.top_keywords = cluster_keywords
    
    
    def extract_top_chunks_per_cluster(self):
        if self.chunks is None or not hasattr(self, 'cluster_labels'):
            raise ValueError("Clustering has not been performed. Call process_and_get_cluster_data() first.")

        # Group chunks by cluster
        cluster_chunks = defaultdict(list)
        cluster_embeddings = defaultdict(list)
        for chunk, embedding, label in zip(self.chunks, self.reduced_embeddings, self.cluster_labels):
            if label != -1:  # Exclude noise points
                cluster_chunks[label].append(chunk)
                cluster_embeddings[label].append(embedding)

        top_chunks = {}
        for cluster in cluster_chunks.keys():
            # Calculate centroid for the cluster
            centroid = np.mean(cluster_embeddings[cluster], axis=0)
            
            # Calculate distances from each point to the centroid
            distances = [np.linalg.norm(embedding - centroid) for embedding in cluster_embeddings[cluster]]
            
            # Get indices of top N closest points
            n = self.num_chunks_per_cluster
            top_indices = np.argsort(distances)[:n]
            
            # Get the corresponding chunks
            top_chunks[cluster] = [cluster_chunks[cluster][i] for i in top_indices]

        self.top_chunks = top_chunks
    
    
    def get_cluster_data(self):
        if self.reduced_embeddings is None or not hasattr(self, 'cluster_labels'):
            raise ValueError("Clustering has not been performed. Call reduce_dimensionality() and form_clusters() first.")
        
        return {
            'reduced_embeddings': self.reduced_embeddings,
            'cluster_labels': self.cluster_labels,
            'num_clusters': self.num_clusters,
            # 'chunk_ids': self.chunk_ids,
            # 'chunks': self.chunks,
            'top_keywords_per_cluster': self.top_keywords,
            'top_chunks_per_cluster': self.top_chunks
        }
        

    def process_and_get_cluster_data(self):
        """
        Performs all steps of the clustering process and returns the cluster data.
        """
        self.load_data()
        self.reduce_dimensionality()
        self.form_clusters()
        self.extract_top_keywords_per_cluster()
        self.extract_top_chunks_per_cluster()
        cluster_data = self.get_cluster_data()
        return cluster_data


if __name__ == "__main__":
    # Example usage
    clustering_tool = VectorDBClusteringTool(
        num_keywords_per_cluster=5,
        num_chunks_per_cluster=5,
        reduced_dimensions=50,
        dimensionality_reduction_method="PCA",
        clustering_method="HDBSCAN",
    )
    cluster_data = clustering_tool.process_and_get_cluster_data()
    print("Cluster data obtained:", cluster_data.keys())

