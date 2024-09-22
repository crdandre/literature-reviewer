from dotenv import load_dotenv
load_dotenv()

import sys
import os

import aiohttp
from pytest import fixture

# Add the src directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

@fixture
async def test_client():
    async with aiohttp.ClientSession() as session:
        yield session

@fixture
def sample_pdfs() -> list[str]:
    pdf_folder = os.getenv('LOCAL_PDF_PATH')
    if not os.path.isdir(pdf_folder):
        raise FileNotFoundError(f"The directory {pdf_folder} does not exist.")    
    pdf_files = [f for f in os.listdir(pdf_folder) if f.lower().endswith('.pdf')]    
    return pdf_files

@fixture
def sample_dois() -> list[str]:
    return(
        [
            "10.1038/s42254-020-00273-3",
            "10.1038/s41598-024-53586-z",
            "10.1016/j.matt.2022.09.025",
            ""
        ]
    )
    
@fixture
def test_query() -> dict:
    return {
        "title": "Finite Element Spine Growth Simulation",
        "authors": "Christian D'Andrea",
        "year": "2023"
    }
    