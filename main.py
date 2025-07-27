import fitz
import json
import os
import re
from datetime import datetime
from collections import defaultdict

INPUT_DIR = "/app/input"
OUTPUT_DIR = "/app/output"
STOP_WORDS = {'a', 'an', 'the', 'is', 'are', 'was', 'were', 'in', 'on', 'of', 'for', 'to', 'and', 'or', 'but'}

def extract_headings_from_pdf(doc, doc_name):
    styles = defaultdict(int)
    for page in doc:
        for block in page.get_text("dict")["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        styles[(round(span["size"]), "bold" in span["font"].lower())] += 1
    
    if not styles: return []
    body_style = max(styles, key=styles.get)
    heading_styles = {s for s in styles if s[0] > body_style[0] or (s[0] == body_style[0] and s[1] and not body_style[1])}
    ranked_styles = sorted(list(heading_styles), key=lambda s: (s[0], s[1]), reverse=True)
    style_level_map = {style: f"H{i+1}" for i, style in enumerate(ranked_styles)}

    headings = []
    seen_text = set()
    for page_num, page in enumerate(doc, start=1):
        blocks = sorted(page.get_text("dict")["blocks"], key=lambda b: b['bbox'][1])
        for block in blocks:
            if "lines" in block:
                full_text = " ".join(s['text'] for l in block['lines'] for s in l['spans']).strip()
                if not full_text or len(full_text.split()) > 10 or full_text.strip().endswith(('.', ':', ',')) or full_text.lower() in seen_text:
                    continue
                
                first_span = block["lines"][0]["spans"][0]
                style_tuple = (round(first_span["size"]), "bold" in first_span["font"].lower())

                if style_tuple in style_level_map:
                    headings.append({'document': doc_name, 'section_title': full_text, 'page_number': page_num, 'bbox': block['bbox']})
                    seen_text.add(full_text.lower())
    return headings


def detect_repeating_elements(doc):
    positions = defaultdict(list)
    page_count = len(doc)
    for page_num, page in enumerate(doc):
        if page_num > 2 and page_num < page_count - 2: continue
        for block in page.get_text("blocks"):
            text = block[4].strip()
            if len(text) > 10:
                positions[text].append(page_num)
    
    return {text for text, pages in positions.items() if len(set(pages)) > 1}

def get_clean_text_for_section(doc, current_section, next_section, junk_texts):
    start_page_num = current_section['page_number'] - 1
    start_y = current_section['bbox'][3] 
    end_page_num = next_section['page_number'] - 1 if next_section else len(doc) - 1
    end_y = next_section['bbox'][1] if next_section and next_section['page_number'] == start_page_num else float('inf')

    text_blocks = []
    for page_num in range(start_page_num, end_page_num + 1):
        if page_num >= len(doc): continue
        page = doc[page_num]
        
        page_start_y = start_y if page_num == start_page_num else 0
        page_end_y = end_y if page_num == end_page_num else float('inf')

        for block in page.get_text("blocks"):
            block_y_top = block[1]
            block_text = block[4].replace('\n', ' ').strip()
            
            if block_text not in junk_texts and block_y_top > page_start_y and block_y_top < page_end_y:
                text_blocks.append(block_text)

    return " ".join(text_blocks)


def calculate_relevance_score(text, query_words, high_value_words):
    text_words = set(re.findall(r'\w+', text.lower()))
    
    score = 0
    for word in high_value_words:
        if word in text_words:
            score += 100
            
    common_words = (text_words - STOP_WORDS).intersection(query_words)
    score += len(common_words)
    return score

def main():
    print("Starting Round 1B: Multi-Document Relevance Ranking...")
    
    pdf_files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(".pdf")]
    prompt_path = os.path.join(INPUT_DIR, "prompt.json")

    if not pdf_files or not os.path.exists(prompt_path):
        print("Error: Input must contain PDFs and a 'prompt.json' file.")
        return

    with open(prompt_path, 'r', encoding='utf-8') as f: prompt = json.load(f)
    
    persona, job_to_be_done = prompt.get("persona"), prompt.get("job_to_be_done")
    query_text = f"{persona} {job_to_be_done}"
    query_words = set(re.findall(r'\w+', query_text.lower()))
    high_value_words = query_words - STOP_WORDS # Use non-stop words as high-value

    all_sections = []
    docs = {name: fitz.open(os.path.join(INPUT_DIR, name)) for name in pdf_files}
    junk_texts_by_doc = {name: detect_repeating_elements(doc) for name, doc in docs.items()}

    for name, doc in docs.items():
        all_sections.extend(extract_headings_from_pdf(doc, name))

    for section in all_sections:
        section['relevance_score'] = calculate_relevance_score(section['section_title'], query_words, high_value_words)

    ranked_sections = sorted(all_sections, key=lambda s: s['relevance_score'], reverse=True)

    top_n_sections = 5
    
    metadata = { "input_documents": pdf_files, "persona": persona, "job_to_be_done": job_to_be_done, "processing_timestamp": datetime.now().isoformat() }
    extracted_sections_out = [{"document": s['document'], "section_title": s['section_title'], "importance_rank": i + 1, "page_number": s['page_number']} for i, s in enumerate(ranked_sections[:top_n_sections])]
    
    subsection_analysis_out = []
    headings_by_doc = {name: sorted([s for s in all_sections if s['document'] == name], key=lambda h: (h['page_number'], h['bbox'][1])) for name in pdf_files}
    
    for section in ranked_sections[:top_n_sections]:
        doc_name = section['document']
        original_doc_headings = headings_by_doc[doc_name]
        next_section = None
        try:
            current_index = original_doc_headings.index(section)
            if current_index + 1 < len(original_doc_headings):
                next_section = original_doc_headings[current_index + 1]
        except ValueError: pass
        
        refined_text = get_clean_text_for_section(docs[doc_name], section, next_section, junk_texts_by_doc[doc_name])
        subsection_analysis_out.append({"document": doc_name, "refined_text": refined_text, "page_number": section['page_number']})

    final_output = {"metadata": metadata, "extracted_sections": extracted_sections_out, "subsection_analysis": subsection_analysis_out}

    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
    output_path = os.path.join(OUTPUT_DIR, "challenge1b_output.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_output, f, indent=4, ensure_ascii=False)

    print(f"Successfully created {output_path}")
    
    for doc in docs.values(): doc.close()

if __name__ == "__main__":
    main()