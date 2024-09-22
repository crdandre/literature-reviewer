What AI-Scientist Does:

I'd like to flip this process around. I'd like to start with a known corpus of documents/papers/data, etc. Something that a resarcher would have on their own subject. I'd like to embed these papers into a vector database, and start a dialogue between the local context, semantic scholar API, and LLMs, such that rather than specifying the ideas themselves, the agent framework is tasked with finding the relevant ideas, gaps, unanswered questions, etc.

There are three main parts: Literature Search, Scientific Opportunity Extraction, Synthesis of Review Narrative to Connect the Opportunities to the Relevant Literature

My proposal is (MVP):
1. Define a topic of reasonable scope for a specialist literature review. Example: "Vertebral growth plate changes during progression of scoliosis"
2. Gather questions, papers, data, etc. that might be helpful for this topic.
3. Embed into a vector DB as "user-provided topic and context"
4. Prompt an LLM to review the papers, extract the gaps, opportunities, and unanswered questions, and store these as objects w.r.t. the process that created them (user-defined topic, questions, materials --> db, agent prompt history, outputs) and rate all of these items on novelty and feasibility (i.e. how large of a contribution to a field bridging the gap or answering the question would be, and a relative ranking of estimated difficulty)

Then to expand:
5. Query Semantic Scholar for a broarder picture of the same topic, and expand the same kind of analysis
6. Follow a writeup template to produce a narrative review that is publishable.
7. Create a review process which implements review criteria for the paper to emulate that which would be required by peer-reviewers.
8. Output a well-formatted .docx or .pdf (latex)
