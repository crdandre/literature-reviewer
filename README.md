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
