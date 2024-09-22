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

Generally, it'd be nice to make this prompt framework agnostic, i.e. LangChain, ell, or anything else. So these, can be relegated to specific components for prompt types. Same goes for any type of framework involved - model type, pdf parsing framework, etc.

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

## Things to look into
### PDF Parsing Framework, which is best? Ideal: Proficient and able to run locally.
- [Marker](https://github.com/VikParuchuri/marker)
    - Really nice, runs locally on GPU, flexible resource allocation, some bugs with unicode characters and file extensions, which are correctable. Reads equations and tables reasonably well.
- [nougat](https://github.com/facebookresearch/nougat)
    - Yet to try. Described as a slower version of Marker...
- [LlamaParse](https://github.com/run-llama/llama_parse)
    - Yet to try. Seems only cloud-based...
- [unstructured](https://github.com/Unstructured-IO/unstructured)
    - Yet to try. Seems related.

### More ways to guide the output of these parsing steps
- LLM checking out an image of the pdf vs the listed section headings and titles, and checking the high level things (modifying the md and json files accordingly)
- Cleaning all non-printable characters (i.e. non-space "orange-box" characters as well to keep data as consistent and clean as possible)

### Search strategies
- By subject/keyword sets
- By top N authors in keyword search, and then searching all of their publications and all of their top N most-cited collaborators' publications for similar / relevant content