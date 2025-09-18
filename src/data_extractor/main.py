# src/data_extractor/main.py

import argparse
import asyncio
import json
from .segmenter import segment_document
from .chunker import chunk_segments
from .extractor import process_entities_concurrently

async def main():
    """
    Main entry point for the data extraction CLI.
    
    This script orchestrates a multi-stage pipeline:
    1. Segments the document into structural parts (prose, list, table).
    2. Chunks each segment into smaller, manageable pieces.
    3. Processes all chunks concurrently to extract entities using an LLM.
    4. Aggregates and saves the final structured data to a JSON file.
    """
    parser = argparse.ArgumentParser(
        description="Extract structured data from a compliance or legal document using a local LLM."
    )
    parser.add_argument(
        "--input-file",
        type=str,
        required=True,
        help="Path to the input text file to be processed."
    )
    parser.add_argument(
        "--output-file",
        type=str,
        required=True,
        help="Path to save the output JSON file."
    )
    parser.add_argument(
        "--document-name",
        type=str,
        default="Unnamed Document",
        help="An optional name for the source document to be included in the metadata."
    )
    
    args = parser.parse_args()

    # --- 1. Read Input File ---
    try:
        print(f"Reading content from: {args.input_file}")
        with open(args.input_file, 'r', encoding='utf-8') as f:
            document_text = f.read()
    except FileNotFoundError:
        print(f"Error: The file {args.input_file} was not found.")
        return
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
        return

    # --- 2. Segment Document ---
    print("\nStage 1: Segmenting the document into structural parts...")
    segments = segment_document(document_text)

    if not segments:
        print("No segments were found in the document.")
        return
    
    print(f"Found {len(segments)} segments. Types found:")
    # Print a summary of what was found
    segment_types = [seg[0] for seg in segments]
    type_counts = {t: segment_types.count(t) for t in set(segment_types)}
    print(f"   -> {type_counts}")


    # For demonstration, let's print a preview of the content of each segment
    for seg_type, seg_content in segments:
        print(f"\n--- Segment: {seg_type.upper()} ---")
        print(f"{seg_content[:200]}...")

    # --- 3. Chunk Segments ---
    print("\nStage 2: Breaking segments into smaller chunks...")

    chunks = chunk_segments(segments)
    if not chunks:
        print("No chunks were created from the segments.")
        return
    
    print(f"Created a total of {len(chunks)} chunks ready for processing.")

    # For demonstration, let's print a preview of the content of each chunk
    print("\n--- Example Chunks ---")
    for i, chunk in enumerate(chunks[:3]):
        print(f"Chunk {i+1}: {chunk[:100]}...")


    # --- 4. Stage 3: Concurrent Extraction ---
    print(f"\nStage 3: Starting concurrent extraction on {len(chunks)} chunks...")
    final_result = await process_entities_concurrently(
        chunks=chunks,
        document_name=args.document_name
    )

    # --- 5. Stage 4: Save Output ---
    if final_result and final_result.get("entities"):
        print(f"\nSaving {len(final_result['entities'])} extracted entities to: {args.output_file}")
        try:
            with open(args.output_file, 'w', encoding='utf-8') as f:
                # Use json.dumps() to convert the dictionary to a JSON formatted string
                json.dump(final_result, f, indent=2)
            print("Process completed successfully!")
        except Exception as e:
            print(f"An error occurred while saving the output file: {e}")
    else:
        print("No entities were successfully extracted from the document.")


if __name__ == "__main__":
    asyncio.run(main())