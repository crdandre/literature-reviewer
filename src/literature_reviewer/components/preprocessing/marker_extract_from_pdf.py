from dotenv import load_dotenv
load_dotenv()

import json
import logging
import os
import re
import subprocess

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')


class MarkerPDFTextExtractor:
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

        existing_files = set(os.listdir(output_folder))

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
            logger.info(f"Starting marker extraction for {self.pdf_inputs_folder}")
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            logger.info(f"Marker extraction completed for {self.pdf_inputs_folder}")
            logger.debug(f"Marker output: {result.stdout}")
            
            logger.info(f"Starting corrections for {output_folder}")
            self._correct_new_files(output_folder, existing_files)
            logger.info(f"Corrections completed for {output_folder}")

        except subprocess.CalledProcessError as e:
            logger.error(f"Error running marker: {e}")
            logger.error(f"Marker stderr: {e.stderr}")
        
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

        existing_files = self._get_existing_file_sets(output_folder)

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
            # Use subprocess.run with capture_output=True and text=True
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            logger.info(f"Marker extraction completed for {self.pdf_inputs_folder}")
            logger.debug(f"Marker output: {result.stdout}")
            
            # Apply corrections after the subprocess has finished
            self._correct_new_files(output_folder, existing_files)
            
            if os.path.exists(output_file):
                return output_file
            else:
                logger.info(f"Extracted markdown file not found: {output_file}")
                return None
        except subprocess.CalledProcessError as e:
            logger.error(f"Error running marker_single: {e}")
            logger.error(f"Marker stderr: {e.stderr}")
            return None
     
    @staticmethod
    def _get_existing_file_sets(parent_output_folder: str): 
        existing_files = {}
        for folder_name in os.listdir(parent_output_folder):
            folder_path = os.path.join(parent_output_folder, folder_name)
            if os.path.isdir(folder_path):
                existing_files[folder_name] = set(os.listdir(folder_path))
        return existing_files
     
    def _correct_new_files(self, output_folder: str, existing_files: dict):
        logger.info(f"Existing files: {existing_files}")
        
        new_files = {}
        for folder_name in os.listdir(output_folder):
            folder_path = os.path.join(output_folder, folder_name)
            if os.path.isdir(folder_path):
                folder_files = set(os.listdir(folder_path))
                new_files[folder_name] = folder_files - existing_files.get(folder_name, set())
        
        logger.info(f"New files to correct: {new_files}")
        
        for folder_name, files in new_files.items():
            folder_path = os.path.join(output_folder, folder_name)
            for filename in files:
                file_path = os.path.join(folder_path, filename)
                logger.info(f"Processing file: {file_path}")
                if filename.endswith('.md'):
                    self._postprocess_converted_md(file_path)
                elif filename.endswith('.json'):
                    self._postprocess_converted_json(file_path)
                else:
                    logger.warning(f"Unrecognized file type: {filename}")

    @staticmethod
    def _postprocess_converted_md(filename):
        logger.info(f"Starting MD corrections for {filename}")
        """
        Corrects some easy errors in converted markdown file.
        Corrections are defined as tuples of (pattern, replacement).
        """
        corrections = (
            ('.Png', '.png'),
            ('.Jpg', '.jpg'),
            ('.Jpeg', '.jpeg'),
            ('.Gif', '.gif'),
            ('**', ''),
            ('__', ''),
            ('\u0aa0', ' '),
            ('_Image_', '_image_'),
        )

        with open(filename, 'r', encoding='utf-8') as file:
            content = file.read()

        for pattern, replacement in corrections:
            content = content.replace(pattern, replacement)

        with open(filename, 'w', encoding='utf-8') as file:
            file.write(content)
        
        logger.info(f"Completed MD corrections for {filename}")

    @staticmethod
    def _postprocess_converted_json(filename):
        logger.info(f"Starting JSON corrections for {filename}")
        """
        Corrects common errors in the converted JSON file.
        Corrections are defined as tuples of (pattern, replacement).
        """
        corrections = (
            ('\u0aa0', ' '),
            ('\r\n', ' '),
            ('\n', ' '),
            ('\r', ' '),
            ('\t', ' '),
            ('\v', ' '),
            ('\f', ' '),
        )

        with open(filename, 'r', encoding='utf-8') as file:
            data = json.load(file)

        def apply_corrections(obj):
            if isinstance(obj, str):
                for pattern, replacement in corrections:
                    obj = obj.replace(pattern, replacement)
                # Replace any remaining control characters with space
                obj = re.sub(r'[\x00-\x1F\x7F-\x9F]', ' ', obj)
                # Collapse multiple spaces into a single space
                obj = re.sub(r'\s+', ' ', obj)
                # Trim leading and trailing spaces
                obj = obj.strip()
                return obj
            elif isinstance(obj, list):
                return [apply_corrections(item) for item in obj]
            elif isinstance(obj, dict):
                return {key: apply_corrections(value) for key, value in obj.items()}
            else:
                return obj

        corrected_data = apply_corrections(data)

        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(corrected_data, file, ensure_ascii=False, indent=2)
        
        logger.info(f"Completed JSON corrections for {filename}")
        
        """
        TODO: Somehow, for strange formats there has to be an image +
        LLM loop to apply formatting diffs to the markdown and json
        """
