from dotenv import load_dotenv
load_dotenv()

import sys
import os

from pytest import fixture

# Add the src directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

@fixture
def sample_pdfs() -> list[str]:
    pdf_folder = os.getenv('LOCAL_PDF_PATH')
    if not os.path.isdir(pdf_folder):
        raise FileNotFoundError(f"The directory {pdf_folder} does not exist.")    
    pdf_files = [f for f in os.listdir(pdf_folder) if f.lower().endswith('.pdf')]    
    return pdf_files
    