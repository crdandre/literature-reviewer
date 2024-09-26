from dotenv import load_dotenv
import json
import os
load_dotenv()

from literature_reviewer.data_ingestion.semantic_scholar import SemanticScholarInterface

TEST_DIRECT_REQUESTS=False

async def test_semantic_scholar_interface_search(test_query):
    query_result_length = 3

    result = SemanticScholarInterface(
        query_result_length=query_result_length
    ).search_papers_via_query(**test_query)

    # assuming that n paperIds means n results, etc.
    assert 'paperId' in result
    assert len([key for key in result if key == 'paperId']) <= query_result_length


if TEST_DIRECT_REQUESTS:
    async def test_semantic_scholar_papers_request(test_client, sample_dois):
        base_url = os.getenv("S2_BASE_GRAPH_URL")
        api_key = os.getenv("S2_API_KEY")
        fields = os.getenv("S2_PAPER_FIELDS")
        request_url = f"{base_url}/paper/batch"
        
        field_list = fields.split(',')
        
        headers = {"x-api-key": api_key}
        params = {
            "fields": fields
        }
        request_json = {
            "ids": sample_dois,
        }
        
        try:
            async with test_client.post(request_url, headers=headers, params=params, json=request_json) as response:
                data = await response.json()
                assert response.status == 200, f"API request failed with status code {response.status}"
                for paper in data:
                    if paper is not None:
                        for field in field_list:
                            assert field in paper, f"Field '{field}' is missing from the response"
                            if field == 'openAccessPdf' and paper[field] is None:
                                assert paper['isOpenAccess'] == False, "Open access PDF is None but isOpenAccess is True"
                    else:
                        print("Warning: Encountered a null paper in the response")
        except Exception as e:
            print(f"Error occurred: {str(e)}")
            raise
        
    async def test_semantic_scholar_query_search(test_client):
        base_url = os.getenv("S2_BASE_GRAPH_URL")
        api_key = os.getenv("S2_API_KEY")
        fields = os.getenv("S2_PAPER_FIELDS")
        request_url = f"{base_url}/paper/search"
        
        headers = {"x-api-key": api_key}
        query = "Christian D'Andrea Finite Element Spine Growth Simulation"
        params={
            "query": query,
            "limit": 10,
            "fields": fields,
        }
        
        try:
            async with test_client.get(request_url, headers=headers, params=params) as response:
                data = await response.json()
                print(f"Response status: {response.status}")
                print(json.dumps(data, indent=2))
                assert response.status == 200, f"API request failed with status code {response.status}"
        except Exception as e:
            print(f"Error occurred: {str(e)}")
            raise