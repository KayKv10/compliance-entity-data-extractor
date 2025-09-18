# src/data_extractor/extractor.py

import asyncio
import instructor
from openai import AsyncOpenAI
from datetime import datetime, timezone
from .schemas import ExtractionResult, ExtractedEntity

# --- vLLM Configuration ---
client = AsyncOpenAI(
    base_url="http://localhost:8000/v1",
    api_key="vllm"
)

# Instructor enables structured, validated responses
instructor_client = instructor.patch(client)


async def _extract_entities_from_chunk(
    chunk_text: str,
    document_name: str,
    semaphore: asyncio.Semaphore
) -> ExtractionResult:
    """
    Asynchronously extracts structured entity data from raw text using a local LLM.

    This function sends the text content to a vLLM server and uses the 'instructor'
    library to force the output into the Pydantic schema defined in 'schemas.py'.

    Args:
        content: The raw text content of the document to process.
        document_name: An identifier for the source document for metadata purposes.

    Returns:
        An `ExtractionResult` Pydantic object containing the extracted entities.
    """
    async with semaphore:
        return await instructor_client.chat.completions.create(
            model="llama-3.1-8b-instruct",
            response_model=ExtractionResult, # type: ignore
            messages=[
                {
                    "role": "system",
                    "content": f"""
                    You are a highly advanced and meticulous data extraction engine. You will be provided with a single, small block of text. Your task is to analyze this text and extract all distinct entities (individuals or organizations) mentioned within it.

                    For each entity, populate a profile adhering strictly to the provided JSON schema. If no entities are found, return an empty list.

                    **Key Instructions:**
                    1.  **Locations**: For attributes like citizenship or residency, create `LocationLink` objects. Use the `type` field to specify what the link represents (e.g., 'Nationality', 'Residency').
                    2.  **Dates**: For key dates like date of birth or incorporation, create `DatedEvent` objects. Use the `type` field for the event (e.g., 'Birth', 'Incorporation').
                    3.  **Assertions**: For other miscellaneous facts (like a legal role or sanction status), use the generic `Assertion` model.
                    4.  **Metadata**: Populate the `metadata` field, including a `confidence_score` between 0.0 and 1.0 for each entity.
                    5.  **Schema Adherence**: Populate all other fields like `identifiers` and `addresses` as completely as possible based *only* on the text.
                    """
                },
                {
                    "role": "user",
                    "content": chunk_text
                }
            ]
        ) 

async def process_entities_concurrently(
    chunks: list[str],
    document_name: str,
    concurrency_limit: int = 18
) -> ExtractionResult:
    """
    Processes a list of text chunks concurrently to extract entities and aggregates them.
    """
    all_entities = []
    semaphore = asyncio.Semaphore(concurrency_limit)
    
    print(f"Processing {len(chunks)} chunks with a concurrency limit of {concurrency_limit}...")

    tasks = [
        _extract_entities_from_chunk(chunk, document_name, semaphore) for chunk in chunks
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)
    current_timestamp = datetime.now(timezone.utc).isoformat()

    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"Error processing chunk {i + 1}: {result}. Skipping.")
        else:
            if result and result.entities: # type: ignore
                for entity in result.entities: # type: ignore
                    entity.raw_source_text = chunks[i]
                    entity.extraction_date = current_timestamp
                    all_entities.append(entity)

    return ExtractionResult(entities=all_entities)