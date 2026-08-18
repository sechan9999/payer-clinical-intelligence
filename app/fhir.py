from datetime import datetime
from typing import Dict, List, Optional
import uuid


def build_fhir_patient_resource(patient_id_hash: str) -> Dict:
    """
    Constructs an HL7 FHIR v4 Patient Resource with anonymized identifier hash.
    Complies with HIPAA Privacy Rule Safe Harbor de-identification standards.
    """
    return {
        "resourceType": "Patient",
        "id": f"pt-{patient_id_hash[:12]}",
        "meta": {
            "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient"]
        },
        "identifier": [
            {
                "system": "urn:oid:2.16.840.1.113883.4.1",
                "value": patient_id_hash
            }
        ],
        "active": True,
        "gender": "unknown",
        "managingOrganization": {
            "display": "Governed Healthcare Network"
        }
    }


def build_fhir_prior_auth_bundle(
    cpt_code: str,
    icd10_code: str,
    clinical_rationale: str,
    patient_id_hash: str,
    submitting_provider: str
) -> Dict:
    """
    Constructs an HL7 FHIR v4 Claim / CoverageEligibilityRequest Bundle for Prior Authorization.
    Conforms to Da Vinci PAS (Prior Authorization Support) FHIR Implementation Guide.
    """
    bundle_id = f"bundle-pa-{uuid.uuid4().hex[:8]}"
    now_iso = datetime.utcnow().isoformat() + "Z"

    patient_res = build_fhir_patient_resource(patient_id_hash)

    coverage_req = {
        "resourceType": "CoverageEligibilityRequest",
        "id": f"req-{uuid.uuid4().hex[:8]}",
        "status": "active",
        "purpose": ["auth-requirements", "benefits"],
        "patient": {
            "reference": f"Patient/{patient_res['id']}"
        },
        "created": now_iso,
        "provider": {
            "display": submitting_provider
        },
        "item": [
            {
                "category": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/ex-benefitcategory",
                            "code": "medical",
                            "display": "Medical Care"
                        }
                    ]
                },
                "productOrService": {
                    "coding": [
                        {
                            "system": "http://www.ama-assn.org/go/cpt",
                            "code": cpt_code,
                            "display": f"CPT Procedure {cpt_code}"
                        }
                    ]
                },
                "diagnosis": [
                    {
                        "diagnosisCodeableConcept": {
                            "coding": [
                                {
                                    "system": "http://hl7.org/fhir/sid/icd-10-cm",
                                    "code": icd10_code,
                                    "display": f"ICD-10 Diagnosis {icd10_code}"
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }

    claim_res = {
        "resourceType": "Claim",
        "id": f"claim-pa-{uuid.uuid4().hex[:8]}",
        "status": "draft",
        "type": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/claim-type",
                    "code": "professional",
                    "display": "Professional"
                }
            ]
        },
        "use": "preauthorization",
        "patient": {
            "reference": f"Patient/{patient_res['id']}"
        },
        "created": now_iso,
        "supportingInfo": [
            {
                "sequence": 1,
                "category": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/claiminformationcategory",
                            "code": "clinicalrationale"
                        }
                    ]
                },
                "valueString": clinical_rationale
            }
        ]
    }

    return {
        "resourceType": "Bundle",
        "id": bundle_id,
        "type": "collection",
        "timestamp": now_iso,
        "entry": [
            {"resource": patient_res},
            {"resource": coverage_req},
            {"resource": claim_res}
        ]
    }


def build_fhir_care_gap_observation(patient_id_hash: str, measure_name: str, priority: str) -> Dict:
    """
    Constructs an HL7 FHIR v4 Observation resource representing a quality care gap (HEDIS/mIPS).
    """
    return {
        "resourceType": "Observation",
        "id": f"obs-gap-{uuid.uuid4().hex[:8]}",
        "status": "final",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "survey",
                        "display": "Quality Measure"
                    }
                ]
            }
        ],
        "code": {
            "coding": [
                {
                    "system": "http://ncqa.org/hedis",
                    "code": measure_name,
                    "display": f"HEDIS Quality Measure {measure_name}"
                }
            ]
        },
        "subject": {
            "reference": f"Patient/pt-{patient_id_hash[:12]}"
        },
        "valueString": f"Priority: {priority} - Recommended Telehealth Navigation"
    }
