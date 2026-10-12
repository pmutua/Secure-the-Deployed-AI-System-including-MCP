# triage_model.py - a deterministic, zero-cost stand-in for the Week 5/6
# LLM call. The capstone's own cost budget asks for stubbed model calls
# this week ("stub the model calls... do not call a model to test
# override phrasing"), and the injection guard in app/main.py already
# runs before this function, so there is nothing security-relevant a
# real model call would add here. Swapping in a real provider call
# (Week 6's health_tip_api.py pattern) is a one-function change and does
# not touch anything in encryption/, access_control/, logging_/, or dpa/.

from __future__ import annotations

URGENT_WORDS = ("chest pain", "bleeding", "unconscious", "cannot breathe")


def triage_model(patient_message: str) -> dict[str, str]:
    text = patient_message.lower()
    if any(word in text for word in URGENT_WORDS):
        return {"urgency": "high", "advice": "Please go to the nearest clinic now."}
    return {"urgency": "low", "advice": "Rest, drink fluids, and monitor your symptoms."}
