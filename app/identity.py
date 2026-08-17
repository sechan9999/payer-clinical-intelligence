from typing import Dict, Optional
from app.domain import DomainDomain, UserIdentity, UserRole


# Server-controlled identity map. Cannot be manipulated via model inputs.
DEV_TOKEN_MAP: Dict[str, UserIdentity] = {
    "tok-payer-admin": UserIdentity(
        token="tok-payer-admin",
        user_id="user_101",
        name="Sarah Jenkins (Payer Admin)",
        role=UserRole.PAYER_ADMIN,
        department="Payer Strategy & Contracting",
        allowed_domains=[DomainDomain.PAYER],
    ),
    "tok-claims-spec": UserIdentity(
        token="tok-claims-spec",
        user_id="user_102",
        name="Marcus Vance (Claims Specialist)",
        role=UserRole.CLAIMS_SPECIALIST,
        department="Revenue Cycle Management",
        allowed_domains=[DomainDomain.PAYER],
    ),
    "tok-clinician": UserIdentity(
        token="tok-clinician",
        user_id="user_201",
        name="Dr. Elena Rostova (Attending Physician)",
        role=UserRole.CLINICIAN,
        department="Cardiology & Internal Medicine",
        allowed_domains=[DomainDomain.CLINICAL],
    ),
    "tok-growth-lead": UserIdentity(
        token="tok-growth-lead",
        user_id="user_202",
        name="David Kim (Clinical Growth Manager)",
        role=UserRole.GROWTH_LEAD,
        department="Clinical Strategy & Population Health",
        allowed_domains=[DomainDomain.CLINICAL],
    ),
    "tok-medical-director": UserIdentity(
        token="tok-medical-director",
        user_id="user_301",
        name="Dr. Arthur Pendelton (Chief Medical Officer)",
        role=UserRole.MEDICAL_DIRECTOR,
        department="Executive Medical Oversight",
        allowed_domains=[DomainDomain.PAYER, DomainDomain.CLINICAL, DomainDomain.CROSS_DOMAIN],
    ),
}


def derive_identity(token: Optional[str]) -> UserIdentity:
    """
    Derives user identity and role from bearer token server-side.
    Falls back to anonymous identity with zero privileges if token invalid.
    """
    if not token:
        return UserIdentity(
            token="anonymous",
            user_id="anon",
            name="Anonymous Guest",
            role=UserRole.ANONYMOUS,
            department="None",
            allowed_domains=[],
        )
    
    clean_token = token.replace("Bearer ", "").strip()
    return DEV_TOKEN_MAP.get(clean_token, UserIdentity(
        token=clean_token,
        user_id="unknown",
        name="Unverified User",
        role=UserRole.ANONYMOUS,
        department="None",
        allowed_domains=[],
    ))
