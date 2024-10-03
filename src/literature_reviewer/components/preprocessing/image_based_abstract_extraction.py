import base64, io, json
from pdf2image import convert_from_path, convert_from_bytes
from pdf2image.exceptions import (
    PDFInfoNotInstalledError,
    PDFPageCountError,
    PDFSyntaxError
)
from literature_reviewer.components.model_interaction.model_call import ModelInterface
from literature_reviewer.components.model_interaction.frameworks_and_models import PromptFramework, Model
from literature_reviewer.components.input_output_models.response_formats import AbstractExtractionResponse
from literature_reviewer.components.prompts.literature_search_query import generate_abstract_extraction_from_image_sys_prompt


def extract_abstract_from_pdf(pdf_path: str, model_interface: ModelInterface, page_limit: int=2) -> str | None:
    images = convert_from_path(pdf_path)
    
    abstract = ""
    full_abstract_found = False
    for page_num, page in enumerate(images):
        # Convert the current page image to base64
        buffered = io.BytesIO()
        page.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        # Prepare the system and user prompts
        system_prompt = generate_abstract_extraction_from_image_sys_prompt()
        user_prompt = f"Please analyze this image (page {page_num + 1}) and fill the AbstractExtractionResponse as requested. If the abstract continues from a previous page, append to it."
        # Call the model to analyze the image and extract the abstract
        response_json = model_interface.entry_chat_call(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            image_string=img_str,
            response_format=AbstractExtractionResponse
        )

        response = json.loads(response_json)
        abstract += response["abstract_text"].strip() + " "
        full_abstract_found = response["contains_full_abstract"]

        # Check if the abstract is complete
        if full_abstract_found or page_num >= page_limit:  # Assume abstract doesn't go beyond 3rd page
            break

    return abstract.strip() if abstract else None



if __name__ == "__main__":
    pdf_path = "/home/christian/literature-reviewer/framework_outputs/gpt4o_mini_mechanobiology_lg_embedding_more_pdfs_20240930_031238/downloaded_pdfs/ee64c41ea80a3c869a940465f271b54a3e6a36e0.pdf"
    model_interface = ModelInterface(PromptFramework.OAI_API, Model("gpt-4o-mini", "OpenAI"))
    abstract = extract_abstract_from_pdf(pdf_path, model_interface)
    print("Extracted Abstract:")
    print(abstract)


