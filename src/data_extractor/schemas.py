# src/data_extractor/schemas.py

import uuid
from datetime import date
from typing import Any, List, Literal, Optional, Dict
from pydantic import BaseModel, Field

def generate_uuid() -> str:
    """Generate a unique identifier."""
    return str(uuid.uuid4())

class Identifier(BaseModel):
    """A unique identifier associated with an entity."""
    type: str = Field(..., description="The type of identifier, e.g., 'Passport No.', 'Tax ID', 'Corporate ID'.")
    value: str = Field(..., description="The value of the identifier.")
    issuing_country: Optional[str] = Field(None, description="The ISO 3166-1 alpha-2 country code that issued the identifier.")
    notes: Optional[str] = Field(None, description="Any additional notes about the identifier.")

class LocationLink(BaseModel):
    """
    Describes a non-physical link between an entity and a location,
    such as nationality or country of jurisdiction.
    """
    type: Literal[
        "Nationality", "Residency", "Jurisdiction", "Birth Country", "Conviction Country"
    ] = Field(..., description="The type of link to the location.")
    country: str = Field(..., description="The country associated with this link (ISO 3166-1 alpha-2 code preferred).")
    notes: Optional[str] = Field(None, description="Any relevant context or notes.")

class Address(BaseModel):
    """A structured physical address associated with an entity."""
    street: Optional[str] = Field(None, description="Street address line.")
    city: Optional[str] = Field(None, description="City or town.")
    state_province: Optional[str] = Field(None, description="State, province, or region.")
    postal_code: Optional[str] = Field(None, description="Postal or ZIP code.")
    country: str = Field(..., description="The country of the address.")
    full_address: str = Field(..., description="The complete, original address string from the source document.")

class DatedEvent(BaseModel):
    """A significant event with an associated date."""
    type: Literal["Birth", "Death", "Incorporation", "Founding"] = Field(..., description="The type of event.")
    event_date: date = Field(..., description="The date of the event.")
    notes: Optional[str] = Field(None, description="Any relevant context.")

class Assertion(BaseModel):
    """A generic statement or claim about an entity for less common facts."""
    type: str = Field(..., description="The category of the assertion, e.g., 'Legal Role', 'Sanction Status', 'Known Associate'.")
    description: str = Field(..., description="A detailed description of the assertion.")
    source_citation: Optional[str] = Field(None, description="A citation for where this assertion is made.")
    properties: Dict[str, Any] = Field(default_factory=dict, description="A flexible dictionary for other key-value pairs.")

class Relationship(BaseModel):
    """A documented relationship between this entity and another entity."""
    related_entity_name: str = Field(..., description="The name of the other entity in the relationship.")
    relationship_type: str = Field(..., description="The nature of the relationship, e.g., 'Affiliation', 'Partnership', 'Family'.")

class Metadata(BaseModel):
    """Metadata about the extraction process."""
    source_document_name: str = Field(..., description="The name or identifier of the source document.")
    confidence_score: float = Field(..., description="The LLM's confidence in the accuracy of the extracted data.")

class ExtractedEntity(BaseModel):
    """A comprehensive, generalized model representing a single entity."""
    record_id: str = Field(default_factory=generate_uuid, description="A unique UUID for this data record.")
    extraction_date: str = Field(..., description="The timestamp (ISO 8601 format) when the data was extracted.")
    entity_type: Literal["Individual", "Organization", "Unknown"] = Field(..., description="The classification of the entity.")
    primary_name: str = Field(..., description="The primary legal or most common name of the entity.")
    aliases: List[str] = Field(default_factory=list, description="Alternative names or spelling variations.")

    # --- Core Data Components ---
    locations: List[LocationLink] = Field(default_factory=list, description="Links to locations like nationality or residency.")
    addresses: List[Address] = Field(default_factory=list, description="Physical addresses.")
    dates: List[DatedEvent] = Field(default_factory=list, description="Key dates like birth or incorporation.")
    identifiers: List[Identifier] = Field(default_factory=list)
    assertions: List[Assertion] = Field(default_factory=list, description="A list of other facts or claims about the entity.")
    relationships: List[Relationship] = Field(default_factory=list)

    # --- Audit and Source ---
    metadata: Metadata
    raw_source_text: str = Field(..., description="The original text block from which this data was extracted.")
 
class ExtractionResult(BaseModel):
    """The root model for a full extraction run."""
    entities: List[ExtractedEntity]
