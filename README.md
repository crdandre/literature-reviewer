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

Inspired by the agentic process utilized by [AI-Scientist] I thought it'd be a more broadly applicable first step for more fields to create an agent which searched for literature related to a topic or local corpus of papers, and review the field, noticing the main themes, effots, gaps, unanswered questions, etc., and created a publishable literature review, or at least an internally useful one, in a short time for a small cost. While science itself may not yet be doable by LLMs, I think narrative literature review is a purpose for which they are well-suited, and can produce publishable work with minimal intervention.

Generally, it'd be nice to make this prompt framework agnostic, i.e. LangChain, ell, or anything else. So these, can be relegated to specific components for prompt types. Same goes for any type of framework involved - model type, pdf parsing framework, etc. This modularity does add some complexity and separates functionality into different files more than one might have otherwise done, but the idea is to make this extensible to do anything and event meta-agent rewrite itself at some point. This way I can make the framework more like lego blocks the model can play with (hopefully, not there yet).

Temporarily, I'm using langchain/chroma db because YT shows this repeatedly and I can more easily get a feel for the data path this way. Eventually, I'd like to containerize a custom DB for this, so that the agent container can run free and the DB can be hosted in another container

## Chat Completions Approach
- Trying to make it modular and easy to work with with the tools you know
- OAI API package, ell, langchain to be supported
- OAI API chats use OpenRouter only for now, specify provider as the company that offers it. I.e. gpt-4o-mini through OpenRouter is still Model("gpt-4o-mini","OpenAI") because the model name within OpenRouter is still "openai/gpt-4o-mini". The API call is just made to OpenRouter's endpoint instead.

## Issues
- Dependency conflict with ell-ai, langchain, and numpy - the first two have no overlapping versions of the 3rd. Starting with langchain for now...

## Adjacent Reference Material
[Texas A&M LibGuide on AI-Based Literature Reviews](https://tamu.libguides.com/c.php?g=1289555)
[RAG/Agents, Good Article](https://lilianweng.github.io/posts/2023-06-23-agent/)

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
 
### Optimized RAG Frameworks instead of custom PDF Parsing?
- [PaperQA2](https://github.com/Future-House/paper-qa?tab=readme-ov-file)
- [ActiveRAG](https://github.com/OpenMatch/ActiveRAG)

### Other scraping
- [paper-scraper](https://github.com/blackadad/paper-scraper)

### More ways to guide the output of these parsing steps
- LLM checking out an image of the pdf vs the listed section headings and titles, and checking the high level things (modifying the md and json files accordingly)
- Cleaning all non-printable characters (i.e. non-space "orange-box" characters as well to keep data as consistent and clean as possible)

### Search strategies
- By subject/keyword sets
- By top N authors in keyword search, and then searching all of their publications and all of their top N most-cited collaborators' publications for similar / relevant content

### Agent frameworks
- [sentient](https://github.com/sentient-engineering/sentient)
- watch [this comparison](https://www.youtube.com/watch?v=6eDh7scJgdw) between CrewAI, AutoGen, LangGraph, and Agent Zero
- [show-me](https://github.com/marlaman/show-me.git)

### Other Tasks
- Embeddings functionality for ell - work on a PR for that
- Modularize database and embedding functionality to be untethered to langchain as it currently is
- Formalize the scheme by which the user_goals are connected to the vec db queries, connected to the s2 queries, connected to the s2 results, connected to the evaluations. Continuity of context! So far, it's checking each step against the raw user_goals prompt rather than any cross checking. between intermediate steps, I believe.
- Move pdf extraction cleaning into its own module or find another module online to do this - either from marker or langchain, there are stray unicode chars, newlines, etc.
- Consider how the user_goals and other prompt are just added together in the user prompt. maybe there is a better way here.
- Local and remote chunks (i.e. abstract only from s2 vs locally read pdf) chunk ids work differently, not sure if this is a problem, but just noting it.
- Parallelization of local tasks, downloads, requests that can be parallelized, etc. Multi-GPU support for local llama
- Style rewriting given samples of the user's writing
- Remote/containerized chromadb
- Remote/containerized agent itself!
- Optional human feedback at certain steps - email notifs depending on time required to generate review
- How to characterize performance as a function of which model is used for each step, chunk size, input tokens per prompt, number of layers of paper search (i.e. finding N related papers, then M related papers for each of the N first papers), number of reflection steps for each relevant process, type of embedding/embedding model, type of dimensionality reduction for embeddings, reduced dimensionality number, clustering method,...add all