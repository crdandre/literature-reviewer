# Literature Reviewer

## Functionality
1. Takes User Input
2. Searches for Similar Publications
3. Embeds all in a vector DB
4. Clusters the vector DB to find relevant topics and gaps
5. Outlines the structure of a review to address the topics and gaps
6. Writes a full literature review using PRISMA based on this outline, using a format tailored to desired journal, and using a style inherited from example review publications using PRISMA, all accurately including relevant citations from step 2, and including relevant plots generated from data obtained from the publications
7. Self-peer-reviews the output from varying perspectives using PRISMA
8. Typesets the final product into a latex template for a particular journal/format + uses image analysis to check this

## Notes
It's assumed the user is using Ubuntu for the commands below.

## Setup
1. Copy `.env.example` into `.env` and fill in `S2_API_KEY`, `OPENAI_API_KEY`, and `OPENROUTER_API_KEY` if using that. The others can be left alone at the moment.  
2. Create a virtual environment with `python3 -m venv .venv`
3. Activate the virtual environment with `source ./.venv/bin/activate`
4. Install the packages in `pyproject.toml` using `pip install -e ".[dev]"`

## Use
At the moment there are two avenues (in-development) to using this framework:
- Deterministic workflow, tasks are ordered one by one: `src/literature_reviewer/workflow/create_review_deterministic.py`
- Agentic workflow, graph is defined, but can be retraced per `Agent` decisions: `src/literature_reviewer/graph/agent_create_review.py`

I'm building both, one is a simpler way to understand how the individual pieces of the workflow work, the other is an exercise in seeing how I can guide LLMs to reach the goal by their own decisions. Ultimately for more complex tasks I'd rather have the agentic workflow be able to form a plan and self-correct toward the desired outcome, but I believe both can be useful.

## Future Directions as of November 2024
1. Hone the search strategy to better obtain relevant papers by using both query and keyword searches, improving filtering of the papers that are found via these searches, and broadening the search to various sources beyond semantic scholar and arxiv. This could look like using perplexity or wikipedia or something else to do initial searches for context and associated citations, and combining that effort with the keyword/query search in literature databases.
2. Hone knowledge storage and organization. Currently there is just a process of finding relevant papers, and embedding chunks of them. This is flat organization of the knowledge. Hierarchical organization in tandem or instead may be more helpful. Additionally there are new methods surfacing like using knowledge graphs. The framework should be extensible and modular so that any additional method of knowledge organization can be accomodated. However, first, taking inspiration from [STORM](https://github.com/stanford-oval/storm), I'd like to incorporate a knowledge tree to have flat+hierarchical knowledge.
3. Hone citation mapping back to text. In the case of using material from a chunk directly, this should map back to the paper from which the chunk was chunked. In the hierarchical scenario, same, any information associated with a source should be able to be traced back to it so it's guaranteed that any material that ends up in the writeup can be accurately cited.
4. Hone the deterministic workflow, while ensuring that it can be expanded to the agentic workflow. I think the deterministic workflow may be sufficient to get fairly far with generating something interesting. Then, expanding into the agentic version of the workflow may provide the additional reflection, review, and modifications necessary to make a useful topic review.
5. Hone the agentic workflow. Ensure tool use is guaranteed when desired, as well as output formats, etc. Demonstrate self-correction at plan and output levels. More TBD here, this is a ways away.