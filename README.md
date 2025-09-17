# Compliance Data Extractor

A service to extract structured data from unstructured compliance documents using a local LLM, served with vLLM.

## Features

- Extracts entities from raw text into a structured JSON format.
- Uses a local LLM (Llama 3.1) for data privacy and local execution.
- Employs Pydantic for schema definition and robust data validation.
- Served with vLLM for high-performance inference.

## Project Setup

1. **Clone the repository:**

    ```bash
    git clone [https://github.com/KayKv10/compliance-data-extractor.git](https://github.com/KayKv10/compliance-data-extractor.git)
    cd compliance-data-extractor
    ```

2. **Create and activate a virtual environment:**

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3. **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

## Usage

1. **Start the vLLM Server:**

    *(Instructions on how to start the server will go here)*

2. **Run the Extraction:**
    Place your document file in the `data/` directory.

    ```bash
    python src/data_extractor/main.py --input-file data/your_document.txt --output-file output.json
    ```
