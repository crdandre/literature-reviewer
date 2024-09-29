"""
outline --> writeup goes here
assumes completed cluster analysis which provides
an LLM tools to create the outline

Plan:
1. Takes in overarching summary of clusters and the user goals
2. Takes in a template of the aspects of the literature review paper
3. Writes an outline of the summary from (1), considering the goals and the user template

System prompt should take in the template and be given the summaries as the user prompt
I think.

Trying to reason out how to create writeup sections that intuitively use reference content in the 
embedded database. I.e. as the outline is converted, to know which papers map to it. Possibly, can
update the outline to include relevant chunks based on the cluster analysis to save time/data?

For now, just searching whole db.
"""
import os
import json

from literature_reviewer.components.prompts.review_writing import (
    generate_review_outline_sys_prompt_basic,
    generate_section_writing_sys_prompt
)
from literature_reviewer.components.model_interaction.model_call import ModelInterface
from literature_reviewer.components.model_interaction.frameworks_and_models import (
    PromptFramework,
    Model,
)
from literature_reviewer.components.prompts.response_formats import StructuredOutlineBasic, SectionWriteup
from literature_reviewer.components.database_operations.chroma_operations import query_chromadb


class ReviewAuthor:
    def __init__(
        self,
        user_goals_text,
        multi_cluster_summary,
        theme_limit=5,
        prompt_framework=None,
        model_name=None,
        model_provider=None,
    ):
        self.user_goals_text = user_goals_text
        self.multi_cluster_summary = multi_cluster_summary
        self.theme_limit = theme_limit
        self.prompt_framework = prompt_framework or PromptFramework[os.getenv("DEFAULT_PROMPT_FRAMEWORK")]
        self.model_name = model_name or os.getenv("DEFAULT_MODEL_NAME")
        self.model_provider = model_provider or os.getenv("DEFAULT_MODEL_PROVIDER")
        self.structured_outline = None

    def create_structured_outline(self):
        """
        Create a structured outline based on the cluster summary and user goals.
        """
        system_prompt = generate_review_outline_sys_prompt_basic(self.user_goals_text)
        chat_model = Model(self.model_name, self.model_provider)
        chat_interface = ModelInterface(self.prompt_framework, chat_model)

        input_text = f"Cluster Summary:\n{self.multi_cluster_summary}"
        
        structured_outline = chat_interface.entry_chat_call(
            system_prompt=system_prompt,
            user_prompt=input_text,
            response_format=StructuredOutlineBasic
        )

        self.structured_outline = structured_outline
        return structured_outline
    
    def match_relevant_papers_to_outline(self, outline: str):
        """
        Match relevant papers from the vector database to each section in the outline.
        """
        # Parse the JSON string into a dictionary
        outline_dict = json.loads(outline)
        
        enriched_outline = {}
        
        for field, content in outline_dict.items():
            relevant_chunks = query_chromadb(content, num_results=3)  # Adjust num_results as needed
            enriched_outline[field] = {
                'content': content,
                'relevant_chunks': relevant_chunks
            }
        
        return enriched_outline

    def write_section(self, section_name, section_data):
        """
        Write a section of the review using the outline content and relevant chunks.
        """
        system_prompt = generate_section_writing_sys_prompt(section_name)
        
        input_text = f"Section content: {section_data['content']}\n\n"
        input_text += "Relevant research:\n"
        for chunk in section_data['relevant_chunks']:
            input_text += f"- {chunk}\n"

        chat_model = Model(self.model_name, self.model_provider)
        chat_interface = ModelInterface(self.prompt_framework, chat_model)

        try:
            section_content = chat_interface.entry_chat_call(
                system_prompt=system_prompt,
                user_prompt=input_text,
                response_format=SectionWriteup
            )
            
            # Ensure section_content is a valid JSON string
            json.loads(section_content)  # This will raise an error if it's not valid JSON
            return section_content
        except Exception as e:
            print(f"Error in write_section for {section_name}: {e}")
            return json.dumps({"content": f"Error writing section {section_name}", "references": []})

    def assemble_writeup(self):
        """
        Assemble the full writeup by writing each section based on the enriched outline.
        """
        if self.structured_outline is None:
            self.structured_outline = self.create_structured_outline()
        
        enriched_outline = self.match_relevant_papers_to_outline(self.structured_outline)
        
        full_writeup = {}
        for section_name, section_data in enriched_outline.items():
            section_content = self.write_section(section_name, section_data)
            if section_content is None:
                print(f"Warning: write_section returned None for {section_name}")
                continue
            full_writeup[section_name] = section_content
        
        # Assemble the full writeup
        main_content = ""
        all_references = set()

        for section_name, section_data in full_writeup.items():
            try:
                # Parse the JSON string into a dictionary
                section_dict = json.loads(section_data)
                
                # Add the content to the main text body
                main_content += f"\n\n{section_name.replace('_', ' ').title()}\n"
                main_content += section_dict['content']
                
                # Add references to the set of all references
                all_references.update(section_dict['references'])
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON for {section_name}: {e}")
                print(f"Raw section data: {section_data}")
            except TypeError as e:
                print(f"TypeError for {section_name}: {e}")
                print(f"Raw section data: {section_data}")

        # Add all unique references at the bottom
        main_content += "\n\nReferences\n"
        for ref in sorted(all_references):
            main_content += f"{ref}\n"

        # Update full_writeup with the assembled content
        full_writeup = {"assembled_content": main_content}

        return full_writeup

# Example usage
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(override=True)
    
    print("Starting review outline creation...")

    with open("/home/christian/literature-reviewer/user_inputs/goal_prompt.txt", "r") as file:
        user_goals_text = file.read()
    
    multi_cluster_summary = '{"overall_summary_narrative": "The syntheses from the clusters reveal significant insights into the efficacy of scoliosis bracing interventions, particularly for young patients and the potential benefits in adult cases. Key findings underscore the effectiveness of CAD/CAM braces when supplemented with finite element modeling for personalized treatment approaches. However, a notable gap in the literature includes a limited understanding of the mechanisms driving spine growth, which is a critical aspect to explore further. Ethical considerations surrounding research practices such as data availability and participant consent are also noted, though they hold lesser relevance to the user\'s primary focus on scoliosis treatment effectiveness. Overall, while substantial progress has been made in understanding bracing interventions, further exploration is warranted into the foundational biological mechanisms influencing spinal development and the implications of the Hueter-Volkmann Law.", "themes": ["Efficacy of Scoliosis Bracing Interventions", "Ethical Approval and Data Availability in Clinical Research"], "gaps": ["Limited understanding of the specific biological mechanisms that drive spine growth.", "Need for long-term studies analyzing the effects of bracing on adult scoliosis cases."], "unanswered_questions": ["What exactly drives spine growth in patients with scoliosis?", "How does the Hueter-Volkmann Law specifically influence the outcome of bracing interventions?"], "future_directions": ["Investigate the biological underpinnings of spinal growth to better inform treatments for scoliosis.", "Explore longitudinal outcomes of scoliosis bracing in various age groups to establish comprehensive effectiveness metrics."]}'

    outline_creator = ReviewAuthor(
        user_goals_text=user_goals_text,
        multi_cluster_summary=multi_cluster_summary,
        theme_limit=5
    )
    
    structured_outline = outline_creator.create_structured_outline()
    
    full_writeup = outline_creator.assemble_writeup()

    cwd = os.getcwd()
    
    # Create the filename and combine it with the path
    filename = "full_literature_review.md"
    filepath = os.path.join(os.getenv("REVIEW_WRITEUP_OUTPUT_PATH"), filename)
    
    # Write the content to the file
    with open(filepath, "w") as file:
        file.write(full_writeup["assembled_content"])
    
    print(f"Full writeup saved to {filepath}")
