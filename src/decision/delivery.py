"""Last-mile delivery simulation (channel payload generators).

Mock delivery channels for the prototype. Each generator returns a structured,
persistable payload (text + language + channel metadata); real transport (SMS,
IVR, WhatsApp, print) is out of scope here and clearly labelled MOCK. Nothing
here fabricates delivery success - the persistence layer records only generation.
"""
from __future__ import annotations

from dataclasses import dataclass

CHANNELS = ("field_worker", "panchayat", "notice_print", "sms", "ivr", "whatsapp", "fpo")


@dataclass(frozen=True)
class DeliveryPayload:
    channel: str
    language: str
    message: str
    recipient_scope: str
    via: str
    mock_notice: str

    def as_dict(self) -> dict:
        return {
            "channel": self.channel,
            "language": self.language,
            "message": self.message,
            "recipient_scope": self.recipient_scope,
            "via": self.via,
            "mock_notice": self.mock_notice,
        }


def _tamil_prefix() -> str:
    return "ஊர் வானிலை ஆலோசனை"


def deliver(channel: str, text_en: str, text_ta: str, ts: str) -> dict:
    """Build one channel payload (lang-aware). Return dict, never sends anything."""
    if channel not in CHANNELS:
        raise ValueError(f"unknown delivery channel: {channel}")
    lang, text = ("ta", text_ta) if len(text_ta) < len(text_en) else ("en", text_en)
    # Prefer Tamil for farmer-facing channels; keep both for the record.
    payloads = {
        "en": {"message": text_en},
        "ta": {"message": text_ta},
    }
    meta = {
        "field_worker": ("Field Worker", "person-to-person briefing (MOCK)"),
        "panchayat": ("Panchayat Office", "notice-board announcement (MOCK)"),
        "notice_print": ("Village", "printable A4 notice (see print_head)"),
        "sms": ("Farmer group / individual", "SMS text (MOCK gateway)"),
        "ivr": ("Caller station", "IVR voice script (MOCK)"),
        "whatsapp": ("Farmer group", "WhatsApp message (MOCK)"),
        "fpo": ("FPO", "FPO advisory bulletin (MOCK)"),
    }
    scope, via = meta[channel]
    mock = (
        f"[MOCK {channel.upper()}] No real transport is used in the prototype. "
        f"Payload generated for traceability at {ts}."
    )
    return DeliveryPayload(
        channel=channel,
        language=lang,
        message=payloads[lang]["message"],
        recipient_scope=scope,
        via=via,
        mock_notice=mock,
    ).as_dict()


def ivr_script(decision_label: str, tamil_block: str) -> str:
    """IVR voice script with a single-play advisory (per master prompt §14)."""
    return "\n".join(
        [
            "*** IVR SCRIPT (MOCK) ***",
            "",
            "▶ PLAY ADVISORY",
            f"Scheme: {decision_label}",
            "",
            tamil_block,
            "",
            "Press 1 to replay. Press 2 to hear date and village. Press 9 for help.",
        ]
    )