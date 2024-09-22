"""
This file should demonstrate the expected text extraction
format from a given research paper PDF. It should be robust
to extra title pages, varying formats, differing section
names, etc. such that one can be reasonably sure most
research papers will be successfully parsed in the desired
format.
"""

import pytest
import os
from literature_reviewer.preprocessing.extract_from_pdf import PDFExtractor

def test_extract_single_pdf_to_markdown_success(sample_pdfs):
    extractor = PDFExtractor(
        pdf_inputs_folder=os.getenv("LOCAL_PDF_PATH"),
        marker_single_input_filename=sample_pdfs[0],
        marker_num_workers=2,
    )

    result = extractor.extract_single_pdf_to_markdown()
    print(f"RESULT: {result}")

    # Check if the result is not None
    assert result is not None
    raise ValueError

    

