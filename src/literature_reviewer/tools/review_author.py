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
from typing import Any

from literature_reviewer.tools.components.prompts.review_writing import (
    generate_review_outline_sys_prompt_basic,
    generate_section_writing_sys_prompt
)
from literature_reviewer.agents.components.model_call import ModelInterface
from literature_reviewer.agents.components.frameworks_and_models import Model
from literature_reviewer.tools.components.input_output_models.response_formats import StructuredOutlineBasic, SectionWriteup
from literature_reviewer.tools.components.database_operations.chroma_operations import query_chromadb
from literature_reviewer.tools.basetool import BaseTool, ToolResponse


class ReviewAuthor(BaseTool):
    def __init__(
        self,
        user_goals_text,
        multi_cluster_summary,
        materials_output_path,
        model_interface: ModelInterface,
        theme_limit=5,
        refs_found_per_outline_item=3,
        chromadb_path=None,
    ):
        super().__init__(model_interface=model_interface)
        self.user_goals_text = user_goals_text
        self.multi_cluster_summary = multi_cluster_summary
        self.materials_output_path = materials_output_path
        self.theme_limit = theme_limit
        self.refs_found_per_outline_item = refs_found_per_outline_item
        self.structured_outline = None
        self.chromadb_path = chromadb_path

    def use(self, step: Any) -> ToolResponse:
        """
        Implements the abstract method from BaseTool.
        Generates and saves the full writeup and outlines.
        """
        try:
            self.generate_and_save_full_writeup_and_outlines()
            
            return ToolResponse(
                output="Successfully generated and saved review materials",
                explanation=f"Generated and saved:\n"
                           f"- Full writeup at {os.path.join(self.materials_output_path, 'full_writeup.md')}\n"
                           f"- Enriched outline at {os.path.join(self.materials_output_path, 'enriched_outline.json')}\n"
                           f"- Initial outline at {os.path.join(self.materials_output_path, 'initial_outline.json')}"
            )
        except Exception as e:
            return ToolResponse(
                output="Error generating review materials",
                explanation=f"An error occurred: {str(e)}"
            )

    def create_structured_outline(self):
        """
        Create a structured outline based on the cluster summary and user goals.
        """
        system_prompt = generate_review_outline_sys_prompt_basic(self.user_goals_text)
        input_text = f"Cluster Summary:\n{self.multi_cluster_summary}"
        
        structured_outline = self.model_interface.chat_completion_call(
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
            # Adjust num_results as needed
            relevant_chunks = query_chromadb(
                content,
                num_results=self.refs_found_per_outline_item,
                chroma_path=self.chromadb_path
            )
            enriched_outline[field] = {
                'content': content,
                'relevant_chunks': relevant_chunks
            }
        self.enriched_outline = enriched_outline
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

        try:
            section_content = self.model_interface.chat_completion_call(
                system_prompt=system_prompt,
                user_prompt=input_text,
                response_format=SectionWriteup
            )
            
            # Ensure section_content is a valid JSON string
            json.loads(section_content)
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
        main_content = ""
        all_references = {}
        current_ref_id = 1

        for section_name, section_data in enriched_outline.items():
            section_content = self.write_section(section_name, section_data)
            if section_content is None:
                print(f"Warning: write_section returned None for {section_name}")
                continue
            
            try:
                # Parse the JSON string into a dictionary
                section_dict = json.loads(section_content)
                
                # Add the content to the main text body
                main_content += f"\n\n{section_name.replace('_', ' ').title()}\n"
                
                # Update reference numbers in the content
                updated_content = section_dict['content']
                for ref in section_dict['references']:
                    old_id = ref['id']
                    if ref['citation'] not in all_references:
                        all_references[ref['citation']] = current_ref_id
                        current_ref_id += 1
                    new_id = all_references[ref['citation']]
                    updated_content = updated_content.replace(f"[{old_id}]", f"[{new_id}]")
                
                main_content += updated_content
                
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON for {section_name}: {e}")
                print(f"Raw section data: {section_content}")
            except TypeError as e:
                print(f"TypeError for {section_name}: {e}")
                print(f"Raw section data: {section_content}")

        # Add all unique references at the bottom
        main_content += "\n\nReferences\n"
        sorted_references = sorted(all_references.items(), key=lambda x: x[1])
        for citation, ref_id in sorted_references:
            main_content += f"[{ref_id}] {citation}\n"

        # Update full_writeup with the assembled content
        full_writeup = {"assembled_content": main_content}
        self.full_writeup = full_writeup
        return full_writeup
    
    
    def generate_and_save_full_writeup_and_outlines(self):
        if not hasattr(self, 'full_writeup') or not self.full_writeup:
            self.create_structured_outline()
            self.assemble_writeup()

        if not hasattr(self, 'materials_output_path') or not self.materials_output_path:
            raise ValueError("Output path is not set.")

        os.makedirs(self.materials_output_path, exist_ok=True)

        # Save full writeup
        full_writeup_path = os.path.join(self.materials_output_path, "full_writeup.md")
        with open(full_writeup_path, "w") as file:
            file.write(self.full_writeup["assembled_content"])

        # Save enriched outline
        enriched_outline_path = os.path.join(self.materials_output_path, "enriched_outline.json")
        with open(enriched_outline_path, "w") as file:
            json.dump(self.enriched_outline, file, indent=2)

        # Save initial outline
        initial_outline_path = os.path.join(self.materials_output_path, "initial_outline.json")
        with open(initial_outline_path, "w") as file:
            json.dump(self.structured_outline, file, indent=2)

        print(f"Full writeup saved to {full_writeup_path}")
        print(f"Enriched outline saved to {enriched_outline_path}")
        print(f"Initial outline saved to {initial_outline_path}")
    
    

# Example usage
if __name__ == "__main__":
    from dotenv import load_dotenv
    from literature_reviewer.agents.components.frameworks_and_models import PromptFramework, Model
    load_dotenv(override=True)
    
    print("Starting review outline creation...")

    with open("user_inputs/goal_prompt.txt", "r") as file:
        user_goals_text = file.read()
    
    multi_cluster_summary = '{"overall_summary_narrative": "The syntheses from the clusters reveal significant insights into the efficacy of scoliosis bracing interventions, particularly for young patients and the potential benefits in adult cases. Key findings underscore the effectiveness of CAD/CAM braces when supplemented with finite element modeling for personalized treatment approaches. However, a notable gap in the literature includes a limited understanding of the mechanisms driving spine growth, which is a critical aspect to explore further. Ethical considerations surrounding research practices such as data availability and participant consent are also noted, though they hold lesser relevance to the user\'s primary focus on scoliosis treatment effectiveness. Overall, while substantial progress has been made in understanding bracing interventions, further exploration is warranted into the foundational biological mechanisms influencing spinal development and the implications of the Hueter-Volkmann Law.", "themes": ["Efficacy of Scoliosis Bracing Interventions", "Ethical Approval and Data Availability in Clinical Research"], "gaps": ["Limited understanding of the specific biological mechanisms that drive spine growth.", "Need for long-term studies analyzing the effects of bracing on adult scoliosis cases."], "unanswered_questions": ["What exactly drives spine growth in patients with scoliosis?", "How does the Hueter-Volkmann Law specifically influence the outcome of bracing interventions?"], "future_directions": ["Investigate the biological underpinnings of spinal growth to better inform treatments for scoliosis.", "Explore longitudinal outcomes of scoliosis bracing in various age groups to establish comprehensive effectiveness metrics."]}'

    # Create model interface
    model_interface = ModelInterface(
        prompt_framework=PromptFramework.OAI_API,
        model=Model("gpt-4o-mini","OpenAI"),
    )
    
    review_author = ReviewAuthor(
        user_goals_text=user_goals_text,
        multi_cluster_summary=multi_cluster_summary,
        materials_output_path="outputs/test_writing",
        model_interface=model_interface,
        theme_limit=5
    )
    review_author.generate_and_save_full_writeup_and_outlines()
    
    

    
