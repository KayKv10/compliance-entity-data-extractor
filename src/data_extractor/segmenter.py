# src/data_extractor/segmenter.py

import re
from typing import List, Tuple

def segment_document(text: str) -> List[Tuple[str, str]]:
    """
    Segments a document into classified parts (prose, list, table).

    This function uses heuristics to identify and label different sections
    of a raw text document.

    Args:
        text: The full raw text of the document.

    Returns:
        A list of tuples, where each tuple contains the segment type
        ('prose', 'list', 'table') and its content.
    """
    segments = []
    
    for segment in text.split('\n\n'):
        segment = segment.strip()
        if not segment:
            continue

        lines = segment.split('\n')
        num_lines = len(lines)

        # --- Heuristic 1: Detect Lists ---
        # If a high percentage of lines start with a common list marker,
        # classify it as a 'list'.
        list_marker_pattern = re.compile(r'^\s*(\(\w+\)|\d+\.|\*|-)\s+')
        list_line_count = sum(1 for line in lines if list_marker_pattern.match(line))
        
        if num_lines > 1 and list_line_count / num_lines > 0.7:
            segments.append(("list", segment))
            continue

        # --- Heuristic 2: Detect Tables ---
        # If lines have multiple instances of a consistent delimiter (like '|' or
        # multiple spaces), it's likely a 'table'.
        pipe_delimiter_count = sum(1 for line in lines if line.count('|') > 2)
        space_delimiter_count = sum(1 for line in lines if re.search(r'\s{2,}', line))

        if num_lines > 1 and (pipe_delimiter_count / num_lines > 0.7 or space_delimiter_count / num_lines > 0.7):
            segments.append(("table", segment))
            continue

        # --- Default: Classify as Prose ---
        segments.append(("prose", segment))

    return segments