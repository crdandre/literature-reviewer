def generate_literature_search_query() -> str:
    return (
        """
        Please analyze the provided corpus of text and user-known relevant PDF embeddings. Extract search queries that will expand this corpus using the Semantic Scholar API. Create several short and relevant search queries to find papers related to the seed material provided by the user. Ensure that the output includes only the list of queries and, below all queries, a list of explanations or references for each query which can be used to self-refine the queries.
        """
    )