# src/data_extractor/main.py

import argparse
from .extractor import extract_entities_from_text
from .schemas import ExtractionResult

def main():
    """
    Main entry point for the data extraction CLI.
    
    This script parses command-line arguments to get input and output file paths,
    reads the source document, invokes the LLM-based extraction process,
    and saves the resulting structured data to a JSON file.
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

    # --- 2. Run Extraction ---
    try:
        extracted_data: ExtractionResult = extract_entities_from_text(
            content=document_text,
            document_name=args.document_name
        )
    except Exception as e:
        print(f"An error occurred during the extraction process: {e}")
        return

    # --- 3. Save Output ---
    if extracted_data and extracted_data.entities:
        try:
            print(f"Saving {len(extracted_data.entities)} extracted entities to: {args.output_file}")
            with open(args.output_file, 'w', encoding='utf-8') as f:
                f.write(extracted_data.model_dump_json(indent=2))
            print("Process completed successfully!")
        except Exception as e:
            print(f"An error occurred while saving the output file: {e}")
    else:
        print("No entities were extracted from the document.")


if __name__ == "__main__":
    main()