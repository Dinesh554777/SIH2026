"""Village advisory generator (English + Tamil).

Deterministic template expansion of a Decision into the printable advisory
format required by the master build prompt:

    VILLAGE NAME | DATE | MONSOON STATUS | ACTION | WHY? | NEXT REVIEW DATE | CONTACT

Tamil copy is intentionally simple and natural for farmers; it never renders
probability jargon literally. All language is authored here - no LLM in the loop
for the deterministic advisory.
"""
from __future__ import annotations

from dataclasses import dataclass

from src.decision.engine import DECISION_ACTION, Decision

NEXT_REVIEW_FORMAT = "daily (or on next rainfall event)"

TA_MONSOON = {
    "pre_onset": "பருவமழை இன்னும் தொடங்கவில்லை",
    "onset_unstable": "பருவமழை துவங்கி உறுதியாகவில்லை",
    "onset_stable": "பருவமழை உறுதியானது",
    "active": "பருவமழை செயலில் உள்ளது",
    "dry_spell_risk": "வறட்சி ஏற்படும் அபாயம்",
    "break_risk": "மழை இடைவெளி ஏற்படும் அபாயம்",
    "recovery": "மழை மீண்டும் திரும்புகிறது",
}

TA_DECISION = {
    "SOW": "விதைப்பு செய்யலாம்",
    "WAIT": "விதைப்பை ஒத்திவையுங்கள்",
    "MONITOR": "நாள்தோறும் கண்காணியுங்கள்",
    "PREPARE": "விதைப்புக்குத் தயாரகுங்கள்",
    "IRRIGATION_PREPARE": "பாசனத் தயாரிப்பு செய்யுங்கள்",
}

TA_ACTION = {
    "SOW": "தொடர்ச்சியான மழை உறுதியான பிறகே, பயிரின் விதைப்புக் காலத்தின் உள்ளே விதைப்பை மேற்கொள்ளுங்கள். உடனடி ஒரு மழைக்காக மட்டும் விதைக்காதீர்கள்.",
    "WAIT": "விதைப்பை இன்னும் செய்ய வேண்டாம். ஒரு மழை பெய்தவுடனே விதைக்காதீர்கள்; தொடர்ச்சியான மழை உறுதியான பிறகே விதைப்பு.",
    "MONITOR": "தினமும் வானிலை அறிவிப்பைக் கவனியுங்கள். நிலமும் விதைகளும் தயாராக இருந்தால் போதும், மழை உறுதியானதும் உடனே விதைக்கலாம்.",
    "PREPARE": "நிலத்தை உழுது, விதை, உரம், இயந்திரங்கள் அனைத்தையும் தயார் நிலையில் வையுங்கள். மழை உறுதியானதும் உடனே விதைப்பு நடக்கலாம்.",
    "IRRIGATION_PREPARE": "தண்ணீரையும் பாசனக் கருவிகளையும் தயார் செய்யுங்கள். முக்கியமான பயிர் நிலையில் தண்ணீர் தேங்காமல், குறைவான அளவில் திறமையாக பாசனம் செய்யுங்கள்.",
}

TA_WHY = {
    "SOW": "பருவமழை உறுதியாவதாக தெரிகிறது; வறட்சி அபாயம் குறைவு.",
    "WAIT": "கடந்த சில நாட்களில் மழை பெய்திருந்தாலும், அது தொடர்ந்து உறுதியாகவில்லை. விதைத்தால் நிலம் காய்ந்து, விதை முளைக்காமல் போக அதிக வாய்ப்பு உள்ளது.",
    "MONITOR": "மழை அறிகுறி இன்னும் முழுமையாக உறுதியாகவில்லை. தினசரி அறிவிப்பைக் கவனிக்கவும்.",
    "PREPARE": "மழை துவங்கும் அறிகுறி தெரிகிறது; இப்போது நிலம், விதை, உரம் தயார் செய்தால், சரியான நேரத்தில் விதைக்கலாம்.",
    "IRRIGATION_PREPARE": "சமீபத்தில் மழை பெய்த பின் வறட்சி ஏற்படும் அபாயம் உள்ளது. பயிரைக் காக்க தண்ணீர் நிர்வாகத்தை முன்கூட்டியே தயார் செய்யுங்கள்.",
}

TA_DISCLAIMER = "இது ஆலோசனை மட்டுமே; உறுதியான விவசாய உத்தரவாதம் அல்ல."


@dataclass(frozen=True)
class VillageAdvisory:
    village_id: str | None
    village_name: str
    location_hint: str
    issue_date: str
    monsoon_status: str
    monsoon_status_label: str
    decision: str
    decision_label: str
    next_review: str
    messages: dict
    disclaimer: str

    def as_dict(self) -> dict:
        return {
            "village_id": self.village_id,
            "village_name": self.village_name,
            "location_hint": self.location_hint,
            "issue_date": self.issue_date,
            "monsoon_status": self.monsoon_status,
            "monsoon_status_label": self.monsoon_status_label,
            "decision": self.decision,
            "decision_label": self.decision_label,
            "next_review": self.next_review,
            "messages": self.messages,
            "disclaimer": self.disclaimer,
        }


def _split_reasons(decision: Decision) -> list[str]:
    if not decision.critical_reasons:
        return []
    return [t for t in decision.critical_reasons if t][:4]


def generate_village_advisory(
    decision: Decision,
    issue_date: str,
    village_id: str | None = None,
    village_name: str | None = None,
    location_hint: str | None = None,
    crop: str | None = None,
) -> VillageAdvisory:
    """Expand a Decision into the bilingual advisory message set."""
    d = decision.decision
    reasons = _split_reasons(decision)

    if crop:
        english_reason = reasons and reasons[0] or decision.explanation.strip()
        english = "\n".join(
            [
                f"Advisory for {village_name or 'this village'} (crop: {crop}).",
                f"Monsoon status: {decision.monsoon_status_label.lower()}.",
                f"Decision: {decision.decision_label}.",
                english_reason,
            ]
        )
        tamil = "\n".join(
            [
                f"{TA_DECISION.get(d, d)} - {TA_ACTION.get(d, '')}",
                TA_WHY.get(d, ""),
            ]
        )
    else:
        english = "\n".join(
            [
                f"Monsoon status: {decision.monsoon_status_label.lower()}.",
                f"Decision: {decision.decision_label}. {DECISION_ACTION.get(d, d)}",
            ]
            + [("- " + r) for r in reasons]
        )
        tamil = "\n".join(
            [
                f"{TA_DECISION.get(d, d)} - {TA_ACTION.get(d, '')}",
                TA_WHY.get(d, ""),
            ]
            + [("- " + r) for r in reasons][:2]
        )

    return VillageAdvisory(
        village_id=village_id,
        village_name=village_name or "Village",
        location_hint=location_hint or "",
        issue_date=issue_date,
        monsoon_status=decision.monsoon_status,
        monsoon_status_label=decision.monsoon_status_label,
        decision=d,
        decision_label=decision.decision_label,
        next_review=NEXT_REVIEW_FORMAT,
        messages={
            "en": {"title": "Village Monsoon Advisory",
                   "block": english,
                   "print_head": _print_header(village_name or "Village", issue_date,
                                               decision.monsoon_status_label, decision.decision_label,
                                               decisions_reasons=reasons, next_review=NEXT_REVIEW_FORMAT)},
            "ta": {"title": "ஊர் வானிலை ஆலோசனை",
                   "block": tamil,
                   "print_head": _print_header(village_name or "ஊர்", issue_date,
                                               TA_MONSOON.get(decision.monsoon_status, ""),
                                               TA_DECISION.get(d, ""),
                                               decisions_reasons=[TA_WHY.get(d, "")],
                                               next_review=NEXT_REVIEW_FORMAT)},
        },
        disclaimer=TA_DISCLAIMER if True else "",
    )


def _print_header(village: str, date: str, status: str, action: str,
                  decisions_reasons: list[str], next_review: str) -> str:
    lines = [
        "+-------------------------------------------------------------+",
        f"|  VILLAGE: {village}",
        f"|  DATE   : {date}",
        f"|  MONSOON STATUS: {status}",
        f"|  ACTION : {action}",
    ]
    for r in decisions_reasons:
        lines.append(f"|  WHY    : {r}")
    lines.append(f"|  NEXT REVIEW: {next_review}")
    lines.append("|")
    lines.append("|  SOURCE: District Monsoon Decision Support (demo)")
    lines.append("+-------------------------------------------------------------+")
    return "\n".join(lines)