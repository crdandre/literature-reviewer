import os
import json
import time
import requests
import backoff
import logging
from typing import List, Dict, Optional
import re

# Set up logging
logger = logging.getLogger(__name__)

class SemanticScholarInterface:
    """
    A class to search Semantic Scholar API for a list of references.
    """
    def __init__(
        self,
        rate_limit: float = 1.0,
        query_result_length: int = 3,
    ):
        """
        Initializes the searcher with the given API key and rate limit.

        :param api_key: Semantic Scholar API key. If None, it will attempt to read from the environment variable 'S2_API_KEY'.
        :param rate_limit: Time in seconds to wait between API requests to respect rate limits.
        """
        self.api_key = os.getenv("S2_API_KEY")
        if not self.api_key:
            raise ValueError("Semantic Scholar API key must be provided via parameter or 'S2_API_KEY' environment variable.")
        self.rate_limit = rate_limit
        self.base_url = os.getenv("S2_BASE_GRAPH_URL")
        self.fields = os.getenv("S2_PAPER_FIELDS")
        self.query_result_length = query_result_length

    
    @staticmethod
    def _on_backoff(details):
        logger.warning(
            f"Backing off {details['wait']:0.1f} seconds after {details['tries']} tries "
            f"calling function {details['target'].__name__} at {time.strftime('%X')}"
        )


    @backoff.on_exception(
        backoff.expo, requests.exceptions.HTTPError, on_backoff=_on_backoff
    )
    def search_papers_via_query(self, title: str, authors: str, year: str) -> Optional[Dict]:
        """
        Searches for a paper using the Semantic Scholar API.

        :param title: The title of the paper.
        :param authors: The authors of the paper.
        :param year: The publication year of the paper.
        :return: A dictionary containing paper details or None if not found.
        """
        if not title:
            logger.warning("Empty title provided.")
            return None

        headers = {"X-API-KEY": self.api_key}
        query = f"{title} {authors} {year}"
        params = {
            "query": query,
            "limit": self.query_result_length,
            "fields": self.fields,
        }

        request_url = f"{self.base_url}/paper/search"
        response = requests.get(request_url, headers=headers, params=params)
        logger.info(f"Searching for: {query} | Status Code: {response.status_code}")
        response.raise_for_status()

        data = response.json()
        if data.get("total", 0) == 0:
            logger.info(f"No results found for query: {query}")
            return None

        return data.get("data", [])[0] if data.get("data") else None

    


# Example Usage
if __name__ == "__main__":
    # Set up logging configuration
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Initialize the searcher
    searcher = SemanticScholarSearcher(api_key=os.getenv("S2_API_KEY"))

    # Define input and output paths
    reference_file = "path/to/your/reference_list.txt"
    output_file = "search_results.json"

    # Run the search
    searcher.run(reference_file, output_file)