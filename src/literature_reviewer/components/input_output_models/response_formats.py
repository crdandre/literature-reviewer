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
    gaps: List[str]
    unanswered_questions: List[str]
    future_directions: List[str]
    
class CitationObject(BaseModel):
    id: int
    citation: str
    
class SectionWriteup(BaseModel):
    content: str
    references: List[CitationObject]
    
# This is a placeholder/basic review outline model
# There could be a way to expand on this to have a model per review type
# i.e. per specific journal structure requirements
class StructuredOutlineBasic(BaseModel):
    introduction_section: str
    literature_overview_section: str
    overarching_themes_section: str
    gaps_section: str
    unanswered_questions_section: str
    future_directions_section: str
    conclusion_section: str
    
    
class AbstractExtractionResponse(BaseModel):
    contains_full_abstract: bool
    abstract_text: str
