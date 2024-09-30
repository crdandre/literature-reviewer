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
        query_response_length_limit: int = 3,
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
        self.query_response_length_limit = query_response_length_limit

    
    @staticmethod
    def _on_backoff(details):
        logger.warning(
            f"Backing off {details['wait']:0.1f} seconds after {details['tries']} tries "
            f"calling function {details['target'].__name__} at {time.strftime('%X')}"
        )


    @backoff.on_exception(
        backoff.expo, requests.exceptions.HTTPError, on_backoff=_on_backoff
    )
    def search_papers_via_queries(self, queries: List[str]) -> List[Optional[Dict]]:
        """
        Searches for papers using the Semantic Scholar API for a list of queries.
        """
        results = []
        headers = {"X-API-KEY": self.api_key}
        
        for query in queries:
            params = {
                "query": query,
                "limit": self.query_response_length_limit,
                "fields": self.fields,
            }

            request_url = f"{self.base_url}/paper/search"
            response = requests.get(request_url, headers=headers, params=params)
            logger.info(f"Searching for: {query} | Status Code: {response.status_code}")
            response.raise_for_status()

            data = response.json()
            if data.get("total", 0) == 0:
                logger.info(f"No results found for query: {query}")
                results.append(None)
            else:
                results.extend(data.get("data", []))

            time.sleep(self.rate_limit)

        return results
    

if __name__ == "__main__":
    from dotenv import load_dotenv
    import json
    from pprint import pprint
    
    load_dotenv()
    
    s2_interface = SemanticScholarInterface(query_response_length_limit=5)
    query = "Patient-specific finite element modeling of scoliotic curve progression"
    results = s2_interface.search_papers_via_queries([query])
    
    print("Search Results:")
    for result in results:
        if result:
            pprint(result, indent=2, width=120)
        else:
            print("No results found for this query.")
        print("\n" + "-"*80 + "\n")
    
    
