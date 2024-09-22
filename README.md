# Literature Reviewer

## Start
```bash
#create virtual env
python -m venv .venv

#activate virtual env
./.venv/scripts/Activate.ps1 (Windows) | source ./.venv/bin/activate (Ubuntu or similar)

#install dependencies
#to use
pip install -e .

#to dev
pip install -e ".[dev]"

#review a topic
python askdjhalksdjhalksjd.py --topic "why sky blue? you tell Joe."

```

Inspired by the agentic process utilized by [AI-Scientist] I thought it'd be a more broadly applicable first step for more fields to create an agent which searched for literature related to a topic or local corpus of papers, and review the field, noticing the main themes, effots, gaps, unanswered questions, etc., and created a publishable literature review, or at least an internally useful one, in a short time for a small cost.

Generally, it'd be nice to make this prompt framework agnostic, i.e. LangChain, ell, or anything else. So these, can be relegated to specific components for prompt types.

The steps followed in AI-Scientist are:
Similarly, the steps that would make sense in this case are:

## Some possible steps. Formalize the task list soon.

- [ ] Extract PDF text with RAG and Semantic Scholar search in mind
- [ ] Set-up databases for text embeddings and chat history
- [ ] Embed topic info/known corpus in vector DB
---
- [ ] Search for similar papers using Semantic Scholar
- [ ] Extract salient themes, gaps, unanswered questions, proposed useful future directions, etc.
- [ ] Analyze the output of the above step to review and sort the found themes by novelty and feasibility
---
- [ ] Rate Limit Handling

## Issues
- Dependency conflict with ell-ai, langchain, and numpy - the first two have no overlapping versions of the 3rd. Starting with langchain for now...

## Adjacent Reference Material
[Texas A&M LibGuide on AI-Based Literature Reviews](https://tamu.libguides.com/c.php?g=1289555)