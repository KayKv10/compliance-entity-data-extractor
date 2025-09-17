import instructor
from openai import OpenAI
from datetime import datetime, timezone
from .schemas import ExtractionResult

# --- vLLM Configuration ---
client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="vllm"
)

# Instructor enables structured, validated responses
instructor_client = instructor.patch(client)


def extract_entities_from_text(
    content: str, 
    document_name: str = "Unknown Document"
) -> ExtractionResult:
    """
    Extracts structured entity data from raw text using a local LLM.

    This function sends the text content to a vLLM server and uses the 'instructor'
    library to force the output into the Pydantic schema defined in 'schemas.py'.

    Args:
        content: The raw text content of the document to process.
        document_name: An identifier for the source document for metadata purposes.

    Returns:
        An `ExtractionResult` Pydantic object containing the extracted entities.
    """
    print("Initializing extraction process...")
    
    try:
        response = instructor_client.chat.completions.create(
            model="meta-llama/Meta-Llama-3.1-8B-Instruct",
            response_model=ExtractionResult,
            max_retries=2,
            messages=[
                {
                    "role": "system",
                    "content": f"""
                    You are a highly advanced and meticulous data extraction engine. Your task is to analyze the user-provided text and extract all distinct entities (individuals or organizations) mentioned.

                    For each entity you identify, you must populate a detailed profile adhering strictly to the provided JSON schema.

                    Key Instructions:
                    1.  **Entity Identification**: Identify every unique individual and organization.
                    2.  **Schema Adherence**: Populate all fields of the `ExtractedEntity` model as completely as possible based *only* on the text. Do not infer or add information that is not present.
                    3.  **Create Assertions**: For each entity, create `Assertion` objects to capture its roles, statuses, attributes, or any other significant facts mentioned in the text. An assertion could be a legal role (e.g., 'Borrower'), a compliance status (e.g., 'Listed on a watchlist'), or a relationship (e.g., 'Employee of XYZ Corp').
                    4.  **Populate Metadata**:
                        - Set the `source_document_name` to '{document_name}'.
                        - Set the `extraction_date` to the current UTC time in ISO 8601 format.
                        - Provide a `confidence_score` between 0.0 and 1.0, representing your confidence in the accuracy and completeness of the extraction for each entity.
                    5.  **Raw Source Text**: For each entity, include the specific block of raw text from which its information was primarily extracted in the `raw_source_text` field.
                    """
                },
                {
                    "role": "user",
                    "content": f"Please extract all entities from the following document content:\n\n---\n\n{content}"
                }
            ]
        )
        print("Extraction successful and validated against schema.")
        return response
    except Exception as e:
        print(f"An error occurred during LLM call or data validation: {e}")
        raise

def get_current_utc_timestamp() -> str:
    """Returns the current UTC time in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()