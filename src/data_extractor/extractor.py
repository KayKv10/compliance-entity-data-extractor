# src/data_extractor/extractor.py

import asyncio
import json
from openai import AsyncOpenAI
from datetime import datetime, timezone
import re

# --- vLLM Configuration ---
client = AsyncOpenAI(
    base_url="http://localhost:8000/v1",
    api_key="vllm"
)


def _extract_json_from_response(response_text: str) -> str:
    """
    Extracts a JSON string from text that might include markdown code fences
    or other conversational text.
    """
    # Pattern to find JSON within ```json ... ```
    match = re.search(r'```json\s*([\s\S]*?)\s*```', response_text)
    if match:
        return match.group(1).strip()

    # Fallback for JSON that is not in a markdown block, finding the outer-most brackets
    start_index = response_text.find('[')
    if start_index == -1:
        start_index = response_text.find('{')
    
    if start_index != -1:
        # Find the corresponding closing bracket
        if response_text[start_index] == '[':
            end_char = ']'
        else:
            end_char = '}'
        
        end_index = response_text.rfind(end_char)
        if end_index > start_index:
            return response_text[start_index : end_index + 1]


async def _extract_entities_from_chunk(
    chunk_text: str,
    semaphore: asyncio.Semaphore
) -> dict:
    """
    Asynchronously extracts entities from a text chunk by instructing the LLM
    to generate a simple JSON output.

    This function uses a streamlined prompt that focuses on extracting only the
    most critical entity information to ensure reliability and speed.

    Args:
        chunk_text: The raw text content of the document chunk to process.
        semaphore: An asyncio.Semaphore to limit concurrent API calls.

    Returns:
        A dictionary parsed from the LLM's JSON output.
    """
    async with semaphore:
        try:
            response = await client.chat.completions.create(
                model="llama-3.1-8b-instruct",
                messages=[
                    {
                        "role": "system",
                        "content": """
                        You are an efficient data extraction engine. Your task is to find all individuals and organizations in the user's text, and extract as much information as possible about them.

                        Please include:
                        - `entity_name`: The full name of the person or organization.
                        - `entity_type`: Either "Individual" or "Organization".
                        - `confidence_score`: A float between 0 and 1 indicating your confidence in the accuracy of this extraction.
                        - Any other relevant fields you can extract, as key-value pairs.

                        For each entity, create a JSON object. 

                        Your output must be a single, valid JSON object. This object should be a list of entities. If no entities are found, return an empty list: []
                        """
                    },
                    {
                        "role": "user",
                        "content": chunk_text
                    }
                ],
                temperature=0.0,
            )
            response_text = response.choices[0].message.content
            json_str = _extract_json_from_response(response_text)
            try:
                data = json.loads(json_str)
                #Expecting {"entities": [...]}
                if isinstance(data, dict) and 'entities' in data and isinstance(data['entities'], list):
                    return data['entities']
                # Handle cases where the LLM might just return the list
                elif isinstance(data, list):
                    return data
                else:
                    # If the structure is wrong, we'll let it fall through to the fixing mechanism
                    raise json.JSONDecodeError("Incorrect JSON structure", json_str, 0)
            except json.JSONDecodeError as e:
                fixed_response = await client.chat.completions.create(
                    model="llama-3.1-8b-instruct",
                    messages=[
                        {
                            "role": "system",
                            "content": """
                            You are a JSON-fixing engine. The user has provided you with a string that is supposed to be a JSON object, but it contains errors. Your task is to correct these errors and return a valid JSON object.
                            """
                        },
                        {
                            "role": "user",
                            "content": response_text
                        }
                    ],
                    temperature=0.0,
                )
                fixed_response_text = fixed_response.choices[0].message.content
                fixed_json_str = _extract_json_from_response(fixed_response_text)
                try:
                    data = json.loads(fixed_json_str)
                    if isinstance(data, dict) and 'entities' in data and isinstance(data['entities'], list):
                        return data['entities']
                    elif isinstance(data, list):
                        return data
                    return [] # Return empty if fixed JSON is still not the right structure
                except json.JSONDecodeError as e:
                    print(f"Error decoding fixed JSON: {e}\nRaw response: '{fixed_response_text}'")
                    return []
        except Exception as e:
            print(f"An unexpected error occurred during LLM call: {e}")
            raise

async def process_entities_concurrently(
    chunks: list[str],
    document_name: str,
    concurrency_limit: int = 18
) -> dict:
    """
    Processes a list of text chunks concurrently, extracts entities from each,
    and aggregates them into a final dictionary.

    Args:
        chunks: A list of text strings to be processed.
        document_name: The name of the source document for metadata.
        concurrency_limit: The maximum number of concurrent API calls.

    Returns:
        A dictionary containing a list of all extracted entities with enriched metadata.
    """
    all_entities = []
    semaphore = asyncio.Semaphore(concurrency_limit)
    current_timestamp = datetime.now(timezone.utc).isoformat()
    
    print(f"Processing {len(chunks)} chunks with a concurrency limit of {concurrency_limit}...")

    tasks = [
        _extract_entities_from_chunk(chunk, semaphore) for chunk in chunks
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"Error processing chunk {i + 1}: {result}. Skipping.")
            continue
        
        # Check if the result is a dictionary and contains the 'entities' key
        # The extractor now consistently returns a list of entities.
        if isinstance(result, list):
            for entity in result:
                if isinstance(entity, dict):
                    entity['raw_source_text'] = chunks[i]
                    entity['extraction_date'] = current_timestamp
                    entity['source_document_name'] = document_name
                    all_entities.append(entity)
        else:
            print(f"Skipping malformed result for chunk {i + 1}: Expected a list, but got {type(result)}")

    return {"entities": all_entities}