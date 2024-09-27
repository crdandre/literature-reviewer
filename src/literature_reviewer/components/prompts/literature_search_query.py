def generate_literature_search_query(num_entries) -> str:
    return (
        f"""
        Please analyze the provided corpus of text and user-known relevant PDF embeddings. Extract search queries specific to the user-defined topic and/or field and/or subject that will expand this corpus using the Semantic Scholar API. Create several short and relevant search queries specific to the user-defined topic to find papers closely related to the seed material provided by the user. Ensure that the output includes only the list of queries and, below all queries, a list of explanations or references for each query which can be used to self-refine the queries, this explanation also maps back to the user goals, explaining which part of the listed user goals, recommendations, etc. are connected. 
        
        WITH NO DEVIATION FROM JSON STRUCTURE, output each list item within a json array containing {num_entries} entries assigned to the variable "s2_queries", which contains the subfields "query", "relevance_to_user_goal", "novelty", "relevance_to_initial_corpus", and "relevance_to_expanded_corpus" which are each scores of 1-10 which you rate. For now thes can be coarse ratings, I will task you to refine the rating later. For these ratings, however, consult your knowledge outside of the given corpus. Wrap the json with three tick marks ("```") such that the output is structured as, for example:
        
        ```
        {{
            "s2_queries": [
                {{
                    "query": "<query1>",
                    "relevance_to_user_goal": <1-10>,
                    "novelty": <1-10>,
                    "relevance_to_initial_corpus": <1-10>,
                    "relevance_to_expanded_corpus": <1-10>
                }},
                ...
            ]
        }}
        ```
        
        <LIST_OF_EXPLANATIONS_MAPPING_TO_USER_GOALS>
        
        """
    )
    
    
def generate_initial_corpus_search_query() -> str:
    return (
        """
        You are tasked with generating a query to fetch relevant context from embeddings based on user-specified goals and priorities. To accomplish this:

        1. Carefully analyze the content within the [LLM CONTEXT] and [END LLM CONTEXT] tags. This section provides crucial instructions on how to interpret the user's input.

        2. Pay close attention to the [USER INPUT] and [END USER INPUT] tags. This section contains the actual user-provided information, formatted according to the instructions in the LLM context.

        3. Parse the user's input, noting that each item is formatted as "item_number<input_text>". The item numbers correspond to the list in the LLM context.

        4. Pay special attention to item 10, if present, as it provides the order of importance for the other items.

        5. Based on this analysis, generate a concise, topic-focused query that captures the essence of the user's goals and priorities. This query should be optimized for retrieving relevant information from a vector database.

        6. While the query should be efficient and targeted, it doesn't necessarily need to be human-readable.

        Your output should be a single, well-crafted query that effectively represents the user's research goals and can be used to search the embedded corpus.
        
        The template described above is below:
        
        [LLM CONTEXT]
        Hello my genius researcher friend! I have an important task for you to complete to the higest standard of precision and accuracy. It's important that you understand the user's goal for the literature review and existing ideas about the topic of the literature review, and then use this to create a prompt which will be used to analyze a corpus of academic papers.
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