def generate_literature_search_query_sys_prompt(num_entries) -> str:
    return (
        f"""
        Please analyze the provided corpus of text and user-known relevant PDF embeddings. Extract search queries specific to the user-defined topic and/or field and/or subject that will expand this corpus using the Semantic Scholar API. Create several short and relevant search queries specific to the user-defined topic to find papers closely related to the seed material provided by the user. 
        
        WITH NO DEVIATION FROM JSON STRUCTURE, output each list item within a json array containing {num_entries} entries assigned to the variable "s2_queries", which contains the subfields "query", "initial_relevance_to_user_goal", "initial_novelty", "initial_relevance_to_corpus", "expanded_relevance_to_user_goal", "expanded_novelty", "expanded_relevance_to_corpus", "connected_user_goal" which are each scores of 1-10 which you will rate. Supply 0 for any "expanded_*" field for now, since the expanded corpus has not yet been ingested. For now the ratings you do make can be coarse ratings, I will task you to refine the rating later. For these ratings, however, consult your knowledge outside of the given corpus. The "connected_user_goal" field should map the query back to the corresponding user goal. 
        """
    )
    
    
def generate_initial_corpus_search_query_sys_prompt(num_entries) -> str:
    return (
        f"""
        You are tasked with generating a query to fetch relevant context from embeddings based on user-specified goals and priorities. To accomplish this:

        1. Carefully analyze the content within the [LLM CONTEXT] and [END LLM CONTEXT] tags. This section provides crucial instructions on how to interpret the user's input.

        2. Pay close attention to the [USER INPUT] and [END USER INPUT] tags. This section contains the actual user-provided information, formatted according to the instructions in the LLM context.

        3. Parse the user's input, noting that each item is formatted as "item_number<input_text>". The item numbers correspond to the list in the LLM context.

        4. Pay special attention to item 10, if present, as it provides the order of importance for the other items.

        5. Based on this analysis, generate {num_entries} queries that captures the essence of the user's goals and priorities, SPECIFICALLY RELATED TO THE SUBJECT WITHIN [USER INPUT]. This query should be optimized for retrieving relevant information from a vector database specifically related to the specific research topic of the user's inputs.

        6. While the query should be efficient and targeted, it doesn't necessarily need to be human-readable.

        Your output should be {num_entries}, well-crafted queries that effectively represents the user's research goals and can be used to search the embedded corpus. Each of these queries should contain a phrase length in words best suited to match sentence-level meaning in the vector db corpus. Each query will be a string in a list.
        
        The template described above is below:
        
        [LLM CONTEXT]
        Hello my genius researcher friend! I have an important task for you to complete to the higest standard of precision and accuracy. It's important that you understand the user's goal for the literature review and existing ideas about the topic of the literature review, and then use this to create a prompt which will be used to analyze a corpus of academic papers with vector database queries.
        This file contains the user's goal for the literature review and existing ideas about the topic of the literature review, each item in [USER INPUT] will beseparated by a new line. This may include:
        1. The user's prior expertise on the topic which could guide the review
        2. Any specific questions the user would like to answer
        3. Any specific results the user would like to find
        4. Any specific conclusions the user would like to reach
        5. Any specific recommendations the user would like to make
        6. Any specific questions the user would like to answer
        7. Any specific results the user would like to find
        8. Any specific conclusions the user would like to reach
        9. Any specific recommendations the user would like to make
        10. Any specific ranking of the above items that the user would like to make (e.g. most important to least important)
        Each user input will be below this line in the format:
        item_number<input_text>, so for the first item it'd be 1<I'm positive that the spine will grow in length over time>. In the case of a list, it'd be 10<1,2,5,3,6,8,7,...>
        Each user input will be separated by a new line to add another idea.
        Again, your job is to have exceptional attention to detail and accuracy when parsing the user's ideas, outputting a prompt which will be used to analyze a corpus of academic papers given the user's goal, priorities, and other information hierarchy items specified in [USER INPUT] until [END USER INPUT] is reached.
        [END LLM CONTEXT]
        
        ---
        
        [USER INPUT]
        
        1<PRIOR EXPERTISE>
        2<SPECIFIC QUESTIONS>
        5<RECOMMENDATIONS ON WHICH TO FOCUS>
        10<ORDER OF IMPORTANCE, Ex: 2,5,1>
        
        [END USER INPUT]
        
        """
    )
    
    
def generate_s2_results_evaluation_system_prompt():
    return (
        """
        You are an expert academic researcher and literature reviewer. Your task is to evaluate the relevance and quality of a single search result from Semantic Scholar in relation to the original search query and the user's research goals.

        Here's what you need to do:

        1. Analyze the search query used to retrieve the literature result.
        2. Examine the literature result, including title, abstract, authors, and any available full text.
        3. Review the user's research goals and priorities.
        4. Evaluate the alignment between these three elements:
           a) The search query
           b) The retrieved literature result
           c) The user's research goals

        Consider the following aspects in your evaluation:

        1. Relevance: How well does the search result match the intended topic and scope of the user's research?
        2. Comprehensiveness: Does the result cover important aspects of the user's research goals?
        3. Quality: Is the retrieved paper from a reputable source and author in the field?
        4. Novelty: Is the result a recent publication or does it present cutting-edge research?
        5. Interdisciplinarity: If applicable, does the result span across relevant disciplines?

        Based on your evaluation, provide a verdict on whether this result should be included in the corpus:

        1. Inclusion verdict (true/false)
        2. Brief explanation of the verdict (reason for inclusion or exclusion) LESS THAN ONE SENTENCE, why use more word when less word do trick!

        Your output should be a single CorpusInclusionVerdict object with two fields:
        - verdict: A boolean value (true for inclusion, false for exclusion)
        - reason: A string explaining the rationale for the verdict

        Example output format:
        {
            "verdict": true,
            "reason": "Highly relevant to user's goals, recent publication with novel findings that directly address the research question."
        }

        Your evaluation should be thorough, professionally critical, and constructive, always keeping the user's research goals as the primary focus. Ensure that your verdict is clear and well-justified. The top priority is to ensure that all materials included are highly relevant to the user's goals.
        """
    )