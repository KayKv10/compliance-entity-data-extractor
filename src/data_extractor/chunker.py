# src/data_extractor/chunker.py

import re
from typing import List, Tuple

def _chunk_list_segment(content: str) -> List[str]:
    """Chunks a list segment by treating each list item as a chunk."""
    # This regex is effective for identifying individual items in a formatted list.
    pattern = re.compile(r'^\s*(\(\w+\)|\d+\.|\*|-)\s+(.*?)(?=\n\s*(?:\(\w+\)|\d+\.|\*|-)|$)', re.DOTALL | re.MULTILINE)
    chunks = [match[1] for match in pattern.findall(content)]
    return [chunk.strip().replace('\n', ' ') for chunk in chunks]

def _chunk_table_segment(content: str) -> List[str]:
    """Chunks a table segment by treating each row as a chunk."""
    # A simple approach: split by lines and ignore empty ones.
    return [line.strip() for line in content.split('\n') if line.strip()]

def _chunk_prose_segment(content: str, max_chunk_size: int = 256) -> List[str]:
    """
    Chunks a prose segment using a basic recursive approach.
    Splits by paragraphs, then sentences, then combines to respect max_chunk_size.
    """
    chunks = []
    # First, split by paragraphs
    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
    
    for paragraph in paragraphs:
        # Simple sentence split
        sentences = paragraph.split('. ')
        current_chunk = ""
        for sentence in sentences:
            # A simple token count heuristic (split by space)
            if len(current_chunk.split()) + len(sentence.split()) <= max_chunk_size:
                current_chunk += sentence + '. '
            else:
                chunks.append(current_chunk.strip())
                current_chunk = sentence + '. '
        if current_chunk:
            chunks.append(current_chunk.strip())
            
    return chunks

def chunk_segments(segments: List[Tuple[str, str]]) -> List[str]:
    """
    Takes a list of classified segments and applies the appropriate
    chunking strategy to each.

    Args:
        segments: A list of tuples from the segmenter, e.g., [('prose', '...'), ...].

    Returns:
        A single flat list of all text chunks ready for processing.
    """
    all_chunks = []
    for seg_type, seg_content in segments:
        if seg_type == "list":
            chunks = _chunk_list_segment(seg_content)
            all_chunks.extend(chunks)
        elif seg_type == "table":
            chunks = _chunk_table_segment(seg_content)
            all_chunks.extend(chunks)
        elif seg_type == "prose":
            chunks = _chunk_prose_segment(seg_content)
            all_chunks.extend(chunks)
            
    return all_chunks