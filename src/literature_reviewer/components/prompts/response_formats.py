from pydantic import BaseModel
from typing import List

class SeedDataQueryList(BaseModel):
    vec_db_queries: List[str]


class S2Query(BaseModel):
    query: str
    initial_relevance_to_user_goal: int
    initial_novelty: int
    initial_relevance_to_corpus: int
    expanded_relevance_to_user_goal: int
    expanded_novelty: int
    expanded_relevance_to_corpus: int
    connected_user_goal: str


class S2QueryList(BaseModel):
    s2_queries: List[S2Query]


class S2Response(BaseModel):
    title: str
    author: str
    year: int
    abstract: str
    keywords: List[str]


class S2ResponseList(BaseModel):
    s2_responses: List[S2Response]
    

class CorpusInclusionVerdict(BaseModel):
    verdict: bool
    reason: str


class SingleClusterSummary(BaseModel):
    theme: str
    key_points: List[str]
    representative_papers: List[str]
    relevance_to_user_goal: float

# not sure about this one yet
class MultiClusterSummary(BaseModel):
    overall_summary_narrative: str
    themes: List[str]
