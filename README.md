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

## Orchestration and Agent Creation
- Using [`controlflow`](https://github.com/PrefectHQ/ControlFlow)

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
- [pdf2image](https://pypi.org/project/pdf2image/)
    - Great for creating input images to pass into models to extract text from a page with confusing formatting.
 
### Optimized RAG Frameworks instead of custom PDF Parsing?
- [PaperQA2](https://github.com/Future-House/paper-qa?tab=readme-ov-file)
- [ActiveRAG](https://github.com/OpenMatch/ActiveRAG)

### Other scraping
- [paper-scraper](https://github.com/blackadad/paper-scraper)

### Other literature review related
- [OpenRead in Video](https://www.youtube.com/watch?v=fYZaMXA8Ss0)
- [Alternatives to Semantic Scholar](https://www.youtube.com/watch?v=cN_gqxLMkNY&t=382s)
    - Using Lens, Research Rabbit, even Perplexity could be nice ways to search! Does perplexity have an API? [yes](https://docs.perplexity.ai/home)
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

### Other Tasks/Good Features to Add
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
- Saving model run data at intermediate points to loop based on a prior state / loop portions of the whole flow, to not over-use API calls. Possibly by writing detailed logs all in one file each run or saving certain details to a database.
- [x] timestamped runs to not overwrite anything
- [ ] ability to restart or build on an existing run
- make consistent the way the user goals are used in the system prompt like the later examples
- reporting on missing pdfs for otherwise potentially relevant research
- other sources than semanic scholar, to have better chances at finding the research - what other APIs are there?
- Review AI-Scientist for reflection and revision tactics, there's definitely more that can be done beyond my deterministic flow
- Handling PDF Stream Errors...trying again on successful call but interrupted stream...
- Don't redo redundant embeddings on loops for gathering corpus. Also, delete unusable papers, logging what the initial search brought in and what was removed.
- Implement AI-Scientist-like Convergence Behavior to better reflect/self modify throughout the process
- Ways to regulate how many papers are brought in. Need more papers and more relevant papers! Get inspiration for this too.
- Branching through the papers near the centers of clusters to extract the exact method details, and lower level cross-themes
- Perhaps papers should be included on a per-paper basis? or find a better threshold (maybe something like 0.3 is better?)
- Define meta-agent tasks. I.e. define a keyword search strategy given the user prompts, from X sources, then (2) define an inclusion criteria for the found papers, (3) develop an N level clustering approach to find the main themes, (4) define an approach to go from this to a writeup in the style of the specified journal
- Define ways to use a different model at each step - i.e. maybe something cheaper for the paper inclusion checks and a better model for the writing tasks / query creations, etc. using 4o for the inclusion checks is a bit much, and there will be more later refinement based on AI-Scientist techniques.
- Systematic review publication exclution diagram generation! Important.
- Grabbing relevant figures from the best papers.

NEW
- Standardized way to make non OAI models adhere to schema
- generic state for langgraph

---
# Digested To-Do From Above
## Overall
- Optimal reflection connections (i.e. reflect between which steps, how many times, with what type of prompt, with what type of corrective action or lack thereof?)
- Degree of deterministic workflow vs agent permissions to rewrite code, change steps around etc (this would require making sure the "blocks" are modular and can be rearranged while maintaining data format compatability)
- For iterative analysis of an idea, text, etc, add the prior chat context to the current prompt rather than using a new naive prompt
- Prompt Engineering
    - [Video Overview](https://www.youtube.com/watch?v=5k1zkYCuF-8)
        - Zero-shot (no example, just task request, relies on model training data) vs Few-shot prompting (given an example, do the thing)
        - Chain of though (CoT), each step is analyzed (each step can be few-shot as well), but the incremental steps are the main idea here, to get the model to reason
    - [xjdr X post on CoT tokens](https://x.com/_xjdr/status/1840782196921233871)
        - Literally tell the model to "Wait..." at key points
    - Clarify system vs assistant vs user optimization (noting that o1 doesn't have anything but the user I think)
    - Effect of obscuration by moderation (try unmoderated models, if possible)
- Saving every piece of information from start to end, so that parameters, models, flow structure, etc. can all be connected and analyzed
    - Sensitivity study. Establish a gold-standard for a current possible novel literature review from a human expert and establish a metric (i.e. number of topics hit, or points from studies discussed) which can estimate how well the framework is doing as a f(some input(s)).

## Literature Search
- Refining query generation
- Expanding avenues to find relevant research
    - [Google Scholar API (unofficial)](https://serpapi.com/google-scholar-api)
    - [Perplexity API](https://docs.perplexity.ai/home)
    - [arXiv API](https://info.arxiv.org/help/api/index.html)/
    - ...several others
- Method to ensure no duplicates
- Improving analysis of abstracts to determine whether they're related to the seed ideas/corpus
- Improving analysis of each paper to extract the key themes/blurbs wrt user goals

## Literature Analysis
- Optimal Chunking/embedding approach
- Optimal dimensionality reduction strategy
- Optimal clustering strategy
- Optimal idea generation from the clustering analysis (both for keywords and chunks)
- Reflections with found corpus + other sources (maybe perplexity here) to rate the novelty of an idea (to check whether or not literature can be found which significantly overlaps with an idea proposal)

## Writing
- Flexible flow for turning a grouping of ideas/keywords into an outline, and gathering the specific details to turn that outline into a full writeup.
- Means to gather relevant figures from key papers to illustrate the strongest points.
- Means to generate a flowchart for literature searching

## Review
- Gather relevant publications on guidance for systematic literature review, or established review criteria.
- Reflect to the relevant steps to iterate on certain parts of the process. I.e. at step 5, reflect on step 2, then propagate back through to step 5. This step determines the correct level to reflect back toward.

## Output Formatting
- Given a structured writeup format, fill a template (i.e. arxiv, journal format, etc.). Use a model to evaluate whether the target format has been correctly filled with the output review material.


# Oct 4 2024 Considerations
## Architecture
- Tasks, Task Manager kind of orchestration. Possible to use custom solution or a package like controlflow (prefect)
- Where to implement reflection. Use an off-the-shelf agent framework?

## Model Interaction
- Make the RAG operations more modular to implement new RAG techniques such as [ActiveRAG](https://github.com/OpenMatch/ActiveRAG) to make each piece updateable
    - [open-retrievals](https://github.com/LongxingTan/open-retrievals) discusses multiple embedding and reranking approaches. more to learn here
    - generally, refined and reranked vector db is the way to go?
- Ensure any type of model interaction and any type of reflectin can be added at any point in the workflow
- Ensure the reasoning process and prompt design decisions are clearly logged so they can be learned from
- Ideally, make the agents as configurable as possible so that a meta-agent can design and insert agents. I.e. the meta-agent knows the format of each agent it will spawn. Ensure that every hand-created agent is compatible to be replaced with agent design such as that shown in the [ADAS repo](https://github.com/ShengranHu/ADAS)
- Possible Agent frameworks:
    - [livekit](https://github.com/ChenLiu-1996/CitationMap)
    - [controlflow](https://controlflow.ai/concepts/agents)
    - [show-me](https://github.com/marlaman/show-me)
    - leaning toward controlflow at the moment, or just custom flows


## Corpus Gathering Techniques
- Vector DB vs Knowledge Graph vs Both (then how to combine them?)
- Explore other tools for various APIs including arxiv, perplexity, google scholar etc.
- Explore graph creation tools like [this](https://github.com/ChenLiu-1996/CitationMap) to find chains of work, maybe