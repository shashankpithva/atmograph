# backend/nlp_engine.py
import spacy
import re

# Load the spaCy English model
nlp = spacy.load("en_core_web_sm")

# Disruption keywords we want to detect
DISRUPTION_KEYWORDS = {
    "strike", "shutdown", "fire", "bankruptcy", "delay", 
    "flood", "shortage", "earthquake", "storm", "accident", "crisis"
}

# Regex patterns to match our synthetic node names
SYNTHETIC_PATTERNS = [
    r'\b(Supplier_\d+)\b',
    r'\b(Manufacturer_\d+)\b',
    r'\b(Product_\d+)\b',
    r'\b(Warehouse_\d+)\b',
    r'\b(Port_\d+)\b',
]

def extract_synthetic_entities(text: str) -> list[dict]:
    """Extract synthetic node names using regex patterns."""
    entities = []
    for pattern in SYNTHETIC_PATTERNS:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            entities.append({
                "text": match.group(1),
                "label": "SYNTHETIC_NODE"
            })
    return entities

def analyze_text(text: str):
    """
    Processes text to extract Named Entities (spaCy) and synthetic nodes (regex),
    plus detect disruption keywords.
    """
    doc = nlp(text)
    
    # 1. Extract real-world entities using spaCy NER
    entities = []
    for ent in doc.ents:
        entities.append({
            "text": ent.text,
            "label": ent.label_  # e.g., ORG, GPE, PERSON
        })
    
    # 2. Extract synthetic node names using regex
    synthetic_entities = extract_synthetic_entities(text)
    entities.extend(synthetic_entities)
        
    # 3. Detect Disruptions
    text_lower = text.lower()
    detected_disruptions = [word for word in DISRUPTION_KEYWORDS if word in text_lower]
    
    return {
        "original_text": text,
        "entities": entities,
        "disruptions": detected_disruptions
    }