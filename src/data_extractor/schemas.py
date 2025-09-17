# src/data_extractor/schemas.py

import uuid
from datetime import date
from typing import Any, List, Literal, Optional, Dict
from pydantic import BaseModel, Field

def generate_uuid() -> str:
    """Generate a unique identifier."""
    return str(uuid.uuid4())

class Identifier(BaseModel):
    """
    A unique indentifier associated with an entity. This could be a legal document,
    a registration number, or any other form of official identification.

    """

    type: str = Field(
        ...,
        description="The type of identifier e.g. 'Passport', 'Driver's License', 'Tax ID'",
    )
    value: str = Field(..., description="The value of the identifier")
    issuing_country: Optional[str] = Field(
        None, description="The ISO 3166-1 alpha-2 country code that issued the identifier."
    )
    notes: Optional[str] = Field(
        None, description="Any additional notes or comments about the identifier."
    )

class Address(BaseModel):
    """
    A structured physical address associated with an entity.
    """
    street: Optional[str] = Field(None, description="Street address line.")
    city: Optional[str] = Field(None, description="City or town.")
    state_province: Optional[str] = Field(None, description="State, province, or region.")
    postal_code: Optional[str] = Field(None, description="Postal or ZIP code.")
    country: str = Field(..., description="The country of the address.")
    full_address: str = Field(..., description="The complete, original address string from the source document.")

class Assertion(BaseModel):
    """
    A generic statement, fact, or claim about an entity found in a document.
    """
    type: str = Field(..., description="The category of the assertion, e.g., 'Legal Role', 'Sanction Status', 'Financial Record', 'Employment'.")
    description: str = Field(..., description="A detailed description of the assertion.")
    source_citation: Optional[str] = Field(None, description="A citation for where this assertion is made in the source document, e.g., 'Section 2.1, Page 3'.")
    effective_date: Optional[date] = Field(None, description="The date this assertion becomes effective.")
    end_date: Optional[date] = Field(None, description="The date this assertion ends or expires.")
    properties: Dict[str, Any] = Field(default_factory=dict, description="A flexible dictionary for any other key-value pairs related to this assertion.")

class Relationship(BaseModel):
    """
    A documented relationship between this entity and another entity.
    """
    related_entity_name: str = Field(..., description="The name of the other entity in the relationship.")
    related_entity_id: Optional[str] = Field(None, description="A unique ID for the related entity, if available.")
    relationship_type: str = Field(..., description="The nature of the relationship, e.g., 'Affiliation', 'Partnership', 'Employment'.")

class Metadata(BaseModel):
    """
    Metadata about the extraction process and source document.
    """
    source_document_name: str = Field(..., description="The name or identifier of the source document.")
    extraction_date: str = Field(..., description="The timestamp (ISO 8601 format) when the data was extracted.")
    confidence_score: float = Field(..., description="The LLM's confidence in the accuracy of the extracted data (0.0 to 1.0).")
    notes: Optional[str] = Field(None, description="Any additional notes about the extraction process or data quality.")

class ExtractedEntity(BaseModel):
    """
    A comprehensive, generalized model representing a single entity
    """
    record_id: str = Field(default_factory=generate_uuid, description="A unique UUID for this data record.")
    entity_type: Literal["Individual", "Organization", "Unknown"] = Field(..., description="The classification of the entity.")
    primary_name: str = Field(..., description="The primary legal or most common name of the entity.")
    aliases: List[str] = Field(default_factory=list, description="Alternative names, 'a.k.a.', or spelling variations.")

    # --- Core Data Components ---
    identifiers: List[Identifier] = Field(default_factory=list)
    addresses: List[Address] = Field(default_factory=list)
    assertions: List[Assertion] = Field(default_factory=list, description="A list of facts or claims made about the entity in the document.")
    relationships: List[Relationship] = Field(default_factory=list)

    # --- Audit and Source ---
    metadata: Metadata
    raw_source_text: str = Field(..., description="The original, unmodified text block from which this data was extracted.")
  
class ExtractionResult(BaseModel):
    """
    The root model for a full extraction run, containing a list of all entities found.
    """
    entities: List[ExtractedEntity]
