from dotenv import load_dotenv
load_dotenv()

import subprocess
import os
import logging

logger = logging.getLogger(__name__)

class PDFExtractor:
    def __init__(
        self,
        pdf_inputs_folder: str,
        marker_min_length: int = None,
        marker_num_workers: int = 1,
        marker_single_input_filename: str = None,
        marker_single_batch_multiplier: int = 2,
        marker_single_max_pages: int = 10,
    ):
        self.pdf_inputs_folder = pdf_inputs_folder
        self.marker_min_length = marker_min_length
        self.marker_num_workers = marker_num_workers
        self.markdown_conversions_folder = os.getenv('MARKDOWN_CONVERSIONS_FOLDER_NAME')
        self.marker_single_input_filename = marker_single_input_filename
        self.marker_single_batch_multiplier = marker_single_batch_multiplier
        self.marker_single_max_pages = marker_single_max_pages


    def extract_folder_pdfs_to_markdown(self):
        input_folder = self.pdf_inputs_folder
        output_folder = os.path.join(input_folder, self.markdown_conversions_folder)
        os.makedirs(output_folder, exist_ok=True)

        command = [
            "marker",
            input_folder,
            output_folder,
        ]
        if self.marker_min_length is not None:
            command.extend(["--workers", str(self.marker_num_workers)])
        if self.marker_min_length is not None:
            command.extend(["--min_length", str(self.marker_min_length)])
            
        try:
            subprocess.run(command, check=True)
            logger.info(f"Marker extraction completed for {self.pdf_inputs_folder}")
        except subprocess.CalledProcessError as e:
            logger.info(f"Error running marker: {e}")
        
        filename = os.path.basename(self.pdf_inputs_folder)
        extracted_file = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}.md")
        
        if os.path.exists(extracted_file):
            return extracted_file
        else:
            logger.info(f"Extracted markdown file not found: {extracted_file}")
            return None
        
    def extract_single_pdf_to_markdown(self):
        input_folder = self.pdf_inputs_folder
        input_file = os.path.join(self.pdf_inputs_folder, self.marker_single_input_filename)
        output_folder = os.path.join(input_folder, self.markdown_conversions_folder)
        os.makedirs(output_folder, exist_ok=True)

        filename = os.path.basename(self.pdf_inputs_folder)
        output_file = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}.md")

        command = [
            "marker_single",
            input_file,
            output_folder,
        ]
        if self.marker_single_batch_multiplier is not None:
            command.extend(["--batch_multiplier", str(self.marker_single_batch_multiplier)])
        if self.marker_single_max_pages is not None:
            command.extend(["--max_pages", str(self.marker_single_max_pages)])


        try:
            subprocess.run(command, check=True)
            logger.info(f"Marker extraction completed for {self.pdf_inputs_folder}")
            if os.path.exists(output_file):
                return output_file
            else:
                logger.info(f"Extracted markdown file not found: {output_file}")
                return None
        except subprocess.CalledProcessError as e:
            logger.info(f"Error running marker_single: {e}")
            return None

