"""Signoff verification (mock)"""
from app.schemas.driver import SignoffRequest, SignoffResult


def verify_signoff(req: SignoffRequest) -> SignoffResult:
    return SignoffResult(
        signature_match=True,
        seal_present=True,
        damage_detected=False,
        confidence=0.96,
    )
