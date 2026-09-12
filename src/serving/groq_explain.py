"""Groq explanation layer (Phase I-D).

Architecture (Groq is NEVER the forecasting model):

    Frozen ML models -> probabilities -> deterministic rules -> structured
    advisory -> Groq (optional) -> human-friendly explanation

Groq may: explain probabilities, summarize the current situation, translate/simplify
advisory text, generate multilingual explanations.

Groq must NOT: calculate/modify probabilities, invent rainfall or observations,
override the deterministic rules, claim certainty, or independently predict onset.

If Groq is unavailable (no key, timeout, malformed reply, API error), this module
falls back to a deterministic advisory built from the same rules tables, so the
application keeps working. Groq is an enhancement, not a system dependency for
numerical forecasting.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any

GROQ_MODEL_DEFAULT = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_TIMEOUT_SECONDS = 20
GROQ_MAX_TOKENS = 512

SYSTEM_PROMPT = """
You are a cautious decision-support communicator for the SIH2026 monsoon
forecast system. You only REPHRASE the structured facts supplied in the user
message. You never compute, change or invent any number.

Strict rules:
1. Never invent rainfall amounts, observations, probabilities, dates or locations.
2. Never claim certainty. Do not say "rain will definitely occur",
   "monsoon will definitely start", "safe to sow", or "guaranteed".
3. Prefer phrasing such as "X probability is elevated", "conditions indicate
   increased likelihood of ...", "continue monitoring rainfall persistence".
4. Only describe the supplied deterministic advisory; do not override it.
5. Respond in the language whose ISO-639-1 code is given as "target_lang".
6. Return ONLY a JSON object with exactly these four keys:
   {"summary": "...", "why": "...", "action": "...", "caution": "..."}
"""  # noqa: E501

BANNED_CERTAINTY = (
    "rain will definitely",
    "monsoon will definitely",
    "will definitely start",
    "will definitely occur",
    "safe to sow",
    "guaranteed",
    "certainly occur",
    "definitely rain",
)

_OUTLINE_MSG = (
    "Guidance comes from frozen monsoon models plus deterministic decision-support "
    "rules; it is not certainty and should be confirmed against local rainfall."
)

CK = ("summary", "why", "action", "caution")


class GroqExplainerError(Exception):
    pass


def build_explanation_input(cell_id: str, forecast_date: str, probabilities: dict,
                            bundle: dict, provenance: dict, model_version: str) -> dict:
    """Assemble ONLY structured, faithful inputs for the LLM. No free text guesses."""
    cards = []
    for c in bundle["cards"]:
        cards.append({
            "target": c["state"],
            "label": c["state_label"],
            "probability": c["probability"],
            "probability_pct": c["probability_pct"],
            "band": c["band"],
            "band_meaning": c["band_meaning"],
            "interpretation": c["interpretation"],
            "suggested_action": c["suggested_action"],
        })
    return {
        "cell_id": cell_id,
        "forecast_date": forecast_date,
        "probabilities": {t: round(float(probabilities[t]), 4) for t in probabilities},
        "current_signal": bundle["current_signal"],
        "deterministic_advisory": {
            "summary": None,  # Groq composes the summary from the cards below
            "dominant_state": bundle["dominant"],
            "cards": cards,
            "disclaimer": bundle["disclaimer"],
        },
        "model_provenance": {
            "freeze_digest": provenance.get("freeze_digest"),
            "model_version": model_version,
            "models": {c["state"]: c["model"] for c in bundle["cards"]},
        },
    }


def _sanitize_json_text(text: str) -> str:
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE)
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise GroqExplainerError("no JSON object found in model reply")
    return text[start:end + 1]


def _clean_value(value: Any) -> str:
    s = str(value).strip().strip("\"'")
    return re.sub(r"\s+", " ", s)[:500]


def parse_and_validate(raw_text: str) -> dict:
    """Parse the LLM reply into a safe {summary, why, action, caution} dict.

    Raises GroqExplainerError on any structural/safety failure so callers fall back.
    """
    data = json.loads(_sanitize_json_text(raw_text))
    if not isinstance(data, dict):
        raise GroqExplainerError("expected a JSON object")
    cleaned = {}
    for key in CK:
        if key not in data or not str(data.get(key, "")).strip():
            raise GroqExplainerError(f"missing/empty key: {key}")
        cleaned[key] = _clean_value(data[key])
    joined = " ".join(cleaned.values()).lower()
    for banned in BANNED_CERTAINTY:
        if banned in joined:
            raise GroqExplainerError(f"certainty phrase rejected: {banned!r}")
    if not cleaned["caution"].endswith((".", "!", "?")):
        cleaned["caution"] += "."
    cleaned["caution"] += f" {_OUTLINE_MSG}"
    return cleaned


class GroqExplainer:
    """Thin, guarded client. Every failure returns None (caller uses fallback)."""

    def __init__(self, api_key: str | None = None, model: str | None = None,
                 timeout: int = GROQ_TIMEOUT_SECONDS, client: Any | None = None):
        self.api_key = api_key if api_key is not None else os.environ.get("GROQ_API_KEY", "")
        self.model = model or GROQ_MODEL_DEFAULT
        self.timeout = timeout
        self._client = client if client is not None else self._make_client()

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def _make_client(self):
        if not self.available:
            return None
        from groq import Groq
        return Groq(api_key=self.api_key, timeout=self.timeout)

    def _messages(self, payload: dict) -> list[dict]:
        user = {
            **payload,
            "instructions": (
                "Keep the explanation faithful to the supplied probabilities and "
                "deterministic advisory. Express likelihood with calibrated "
                "probabilities and bands only. Reply in JSON with summary, why, "
                "action, caution.")
        }
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(user)},
        ]

    def explain(self, payload: dict) -> dict | None:
        """Request a structured explanation. Returns None on any failure."""
        if not self.available or self._client is None:
            return None
        try:
            reply = self._client.chat.completions.create(
                model=self.model,
                messages=self._messages(payload),
                temperature=0.0,
                max_tokens=GROQ_MAX_TOKENS,
                response_format={"type": "json_object"},
            )
            text = reply.choices[0].message.content
            if not text:
                return None
            return parse_and_validate(text)
        except Exception:
            return None


def fallback_explanation(bundle: dict, lang: str = "en") -> dict:
    """Deterministic advisory when Groq is absent/failed. Uses ONLY rules tables."""
    cards = {c["state"]: c for c in bundle["cards"]}
    dom = bundle["dominant"]
    card = cards[dom]
    sig = bundle["current_signal"]
    why = (
        f"Observed conditions at the cell: {sig['rain_t_mm']:.1f} mm of rain today, "
        f"7-day sum {sig['sum7_mm']:.1f} mm, trend {sig['rainfall_trend'].lower()}, "
        f"regime {sig['rainfall_regime'].lower()}, dry streak {sig['dry_streak_days']} "
        f"day(s). These are the observed inputs used by the frozen models.")
    lang_note = "" if lang == "en" else f" (Fallback advisory generated in English; " \
                                         f"requested language '{lang}' requires Groq.)"
    return {
        "summary": (f"{card['state_label']} probability is {card['probability_pct']:.0f}% "
                    f"({card['band']}, {card['band_meaning'].lower()}). "
                    f"{card['interpretation']}"),
        "why": why,
        "action": card["suggested_action"],
        "caution": f"{bundle['disclaimer']}{lang_note}",
    }


def explain_block(explainer: "GroqExplainer | None", payload: dict, bundle: dict,
                  lang: str = "en") -> dict:
    """Orchestrate: prefer Groq, else deterministic fallback.

    Returns {"source": "groq"|"fallback", "summary", "why", "action", "caution",
             "status", "note"} - never includes the API key.
    """
    ex = explainer if explainer is not None else GroqExplainer()
    if not ex.available:
        return {"source": "fallback", "status": "not_configured",
                "note": "GROQ_API_KEY not set; deterministic advisory used.",
                **fallback_explanation(bundle, lang)}
    try:
        explained = ex.explain({**payload, "target_lang": lang})
    except Exception:
        explained = None
    if explained is None:
        return {"source": "fallback", "status": "error",
                "note": "Groq unavailable/failed; deterministic advisory used.",
                **fallback_explanation(bundle, lang)}
    return {"source": "groq", "status": "ok",
            "note": f"Generated by {ex.model} from frozen model output.",
            **explained}