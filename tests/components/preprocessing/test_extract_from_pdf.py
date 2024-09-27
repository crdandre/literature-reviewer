"""
This file should demonstrate the expected text extraction
format from a given research paper PDF. It should be robust
to extra title pages, varying formats, differing section
names, etc. such that one can be reasonably sure most
research papers will be successfully parsed in the desired
format.
"""
import os
from literature_reviewer.preprocessing.extract_from_pdf import LocalPDFTextExtractor

def test_extract_single_pdf_to_markdown_success(sample_pdfs):
    extractor = LocalPDFTextExtractor(
        pdf_inputs_folder=os.getenv("LOCAL_PDF_PATH"),
        marker_single_input_filename=sample_pdfs[0],
        marker_num_workers=2,
    )

    result = extractor.extract_single_pdf_to_markdown()
    print(f"RESULT: {result}")

    # Check if the result is not None
    assert result is not None


if __name__ == "__main__":
    import logging
    import sys
    from dotenv import load_dotenv
    logging.basicConfig(level=logging.DEBUG, 
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    load_dotenv()
    
    sample_pdfs = ["Arthur_2021_Foundations_of_Complexity_Economics.pdf"]#["Guy_Aubin_Bracing_2024.pdf"]
    try:
        test_extract_single_pdf_to_markdown_success(sample_pdfs)
        logging.info("Test completed successfully!")
    except Exception as e:
        logging.error(f"Test failed: {str(e)}")
        raise


