# Connecting the Dots Challenge - Round 1B Submission

This repository contains the solution for Round 1B, which addresses the multi-document analysis challenge. The system is designed to process a collection of PDF documents and, based on a user's prompt, identify and extract the most relevant sections, presenting them in a structured and ranked format.

## Core Methodology

This solution implements a sophisticated, three-stage analysis pipeline to transform a collection of raw documents into a targeted, actionable summary. The approach was specifically engineered to maximize relevance according to the prompt and to ensure the quality of the extracted text, even from complex and poorly structured documents.

The methodology is as follows:

1.  **Multi-Document Outline Aggregation:** The system begins by processing every PDF in the input collection. It uses a high-accuracy heading extractor with strict filtering rules to generate a clean outline for each document. These individual outlines are then aggregated into a single master list of all potential sections from all documents.

2.  **High-Value Relevance Ranking:** This stage is the intelligent core of the solution, designed to directly address the "Section Relevance" scoring criterion. To rank sections by importance, the script calculates a relevance score for every heading against the user's prompt (`persona` + `job_to_be_done`). The scoring algorithm uses a **High-Value Keyword Bonus**:
    *   It first identifies key terms directly from the user's `job_to_be_done` description.
    *   Any section heading containing one of these high-value keywords receives a significant score bonus, ensuring that the most on-topic sections are always ranked at the top.
    *   A secondary word-overlap score is used to rank the remaining sections.

3.  **Intelligent Text Extraction:** To fulfill the "Sub-Section Relevance" criterion, the solution employs a robust text extractor with a built-in **repeating element detector**.
    *   Before extraction, the script analyzes each document to automatically identify text blocks that repeat across multiple pages (e.g., page headers and footers).
    *   During the extraction process, this list of "junk text" is used as an explicit filter. This ensures that the final `refined_text` is of high quality and free of repetitive, non-content elements, resulting in a clean and useful output.

## Technology Stack

*   **Libraries**:
    *   `PyMuPDF (fitz)`: This high-performance library is used for both the initial heading extraction and for the final, coordinate-based text extraction from the source PDFs. Its speed and accuracy are essential for meeting the challenge's performance constraints.
    *   `os`, `json`, `re`, `datetime`: Standard Python libraries are used for file system operations, text processing, and generating the final timestamped JSON output according to the specified schema.

*   **Models**:
    *   This solution does not use any pre-trained AI or machine learning models. The relevance ranking and text extraction logic are purely algorithmic, guaranteeing compliance with the 1GB model size limit and ensuring fast, CPU-only execution.

## Project Setup and Execution

The project is containerized using Docker and is fully compliant with the offline execution requirement. The `input` directory is designed to hold a collection of PDF files and a single `prompt.json` file.

### 1. Build the Docker Image

With Docker running, navigate to the project's root directory in your terminal and execute the following build command:

```sh
docker build --platform linux/amd64 -t mysolution-1b .
```

### 2. Run the Solution

Ensure your input directory is populated with the desired PDF collection and a prompt.json file. Execute the run command from the project root:

```sh
docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output --network none mysolution-1b
```





