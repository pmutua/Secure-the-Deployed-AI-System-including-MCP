"""Governance evidence: pin a knowledge file against silent poisoning.

Poisoning, for AfyaPlus, means the retrieval corpus (the FAQ files) is
contaminated -- not training a network from scratch. The realistic
defence is not "detect a bad edit"; it is "make a silent edit impossible
to hide": hash the file now, freeze the hash, and let CI refuse to build
if the bytes ever move without the pin moving with them.
"""
import hashlib
import json
from pathlib import Path

KNOWLEDGE = Path("governance/knowledge/ors_faq.md")
PIN_PATH = Path("governance/knowledge/pin.json")


def sha(path: Path) -> str:
    # read_bytes(), not read_text(): sha256 over bytes is reproducible
    # across a laptop and a CI runner with a different default encoding.
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    KNOWLEDGE.parent.mkdir(parents=True, exist_ok=True)
    if not KNOWLEDGE.exists():
        KNOWLEDGE.write_text("ORS is oral rehydration. Seek clinic care if unsure.\n")
    pin = {"governance/knowledge/ors_faq.md": sha(KNOWLEDGE)}
    PIN_PATH.write_text(json.dumps(pin, indent=2))
    print("wrote governance/knowledge/pin.json", pin)
