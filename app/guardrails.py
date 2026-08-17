import re
from typing import Dict, List, Tuple


INJECTION_PATTERNS = [
    r"ignore .*(instructions|directions|rules|system prompt)",
    r"disregard .*(restrictions|limits|controls|permissions|roles)",
    r"override .*(permissions|role|access)",
    r"system prompt reveal",
    r"you are now an unrestricted",
    r"bypass .*(guardrails|approvals)",
]

PHI_PATTERNS = [
    r"\b\d{3}-\d{2}-\d{4}\b",  # SSN pattern
    r"\bpatient_ssn\b",
    r"\bunmasked_name\b",
]


def validate_input_query(query: str) -> Tuple[bool, str]:
    """
    Checks user input query for prompt injections or malicious override attempts.
    Returns (is_safe, reason).
    """
    query_lower = query.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, query_lower):
            return False, f"Prompt injection pattern detected: '{pattern}'"
    
    for pattern in PHI_PATTERNS:
        if re.search(pattern, query_lower):
            return False, f"Raw PHI/PII pattern detected: '{pattern}'"

    return True, "PASS"


def validate_output_response(response: str, expected_citations: List[str]) -> Tuple[bool, str]:
    """
    Ensures agent output adheres to clinical/payer governance and citation rules.
    Returns (is_valid, validation_note).
    """
    if not response:
        return False, "Empty response generated"

    # Citation enforcement: Must cite at least one document ID if citations were available
    if expected_citations:
        has_citation = any(doc_id in response for doc_id in expected_citations)
        if not has_citation:
            return False, f"Citation enforcement failed. Expected reference to one of: {expected_citations}"

    return True, "PASS"
