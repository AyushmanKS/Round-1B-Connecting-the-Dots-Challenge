# Connecting the Dots Challenge - Round 1A Submission

## My Approach

This solution extracts a structured outline (Title, H1, H2, H3) from PDF documents by implementing a robust, two-pass strategy designed to handle complex documents where headings share similar styles.

The core logic operates as follows:

1.  **Pass 1: Style Analysis & Candidate Extraction:**
    *   **Style Cataloging:** The script first performs a full analysis of the document to create a catalog of all font styles (combinations of size and weight). It identifies the most common style as body text.
    *   **Heading Style Ranking:** It then identifies all styles more prominent than the body text and ranks them to create a definitive map (e.g., largest style = H1, second largest = H2, etc.).
    *   **Candidate Filtering:** The script extracts all text matching these heading styles while running it through a strict filter to remove junk data and table headers.

2.  **Pass 2: Hierarchical Correction:**
    *   The script iterates through the clean list of heading candidates and enforces a logical hierarchy. For instance, if it finds an H2 that doesn't have a parent H1, it promotes it to H1. This ensures the final output is always structurally sound.

This style-based ranking and hierarchical correction approach makes the solution resilient to documents that don't use traditional heading cues like numbering or bullet points.