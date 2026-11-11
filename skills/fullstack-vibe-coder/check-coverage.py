#!/usr/bin/env python3
"""Extract every topic from the vibe-coder topics file and verify each appears
in the fullstack-vibe-coder skill files. Writes COVERAGE.md."""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
# When this file lives in skills/fullstack-vibe-coder/, that is the skill root.
# When it lives in repo scripts/, fall back to the skill directory.
if (SCRIPT_DIR / "SKILL.md").exists():
    SKILL_ROOT = SCRIPT_DIR
elif (SCRIPT_DIR.parent / "skills/fullstack-vibe-coder/SKILL.md").exists():
    SKILL_ROOT = SCRIPT_DIR.parent / "skills/fullstack-vibe-coder"
else:
    SKILL_ROOT = Path("/workspace/awesome-grok-bot-skills-build/repo/skills/fullstack-vibe-coder")
TOPICS_FILE = SKILL_ROOT / "topics.md"
MAP_FILE = SCRIPT_DIR / "topic-layer-map.json"
if not MAP_FILE.exists():
    MAP_FILE = Path("/workspace/awesome-grok-bot-skills-build/scripts/topic-layer-map.json")

LAYERS = {
    1: ("Frontend", "references/01-frontend.md"),
    2: ("APIs & Backend Logic", "references/02-apis-backend.md"),
    3: ("Database & Storage", "references/03-database-storage.md"),
    4: ("Auth & Permissions", "references/04-auth-permissions.md"),
    5: ("Hosting & Deployment", "references/05-hosting-deployment.md"),
    6: ("Cloud & Compute", "references/06-cloud-compute.md"),
    7: ("CI/CD & Version Control", "references/07-cicd-version-control.md"),
    8: ("Security & RLS", "references/08-security-rls.md"),
    9: ("Rate Limiting", "references/09-rate-limiting.md"),
    10: ("Caching & CDN", "references/10-caching-cdn.md"),
    11: ("Load Balancing & Scaling", "references/11-load-balancing-scaling.md"),
    12: ("Error Tracking & Logs", "references/12-error-tracking-logs.md"),
    13: ("Availability & Recovery", "references/13-availability-recovery.md"),
    14: ("AI-Assisted Coding & Process", "references/14-ai-process.md"),
}

# Obvious synonyms / OCR forms accepted in addition to the canonical topic string.
SYNONYMS = {
    "hallucinated apis/packages": [
        "hallucinated reading traces",
        "hallucinated apis",
        "hallucinated packages",
    ],
    "agent instructions files / readmes": [
        "agents.md",
        "agni readmes",
        "agent instructions files",
    ],
    "evaluating llm output (evals)": [
        "llm evals",
        "evaluating llm output",
    ],
    "query plans (explain)": ["explain (analyze", "query plans"],
    "cookie flags (httponly/secure/samesite)": [
        "httponly",
        "samesite",
        "cookie flags",
    ],
    "compression (gzip/brotli)": ["gzip", "brotli", "compression (gzip"],
    "security scanning (sast/dast)": ["sast", "dast", "security scanning"],
    "data privacy (gdpr)": ["gdpr", "data privacy"],
    "https/tls": ["https/tls", "tls"],
    "code comments & refactoring": ["code comments", "refactoring"],
}


def extract_topics(text: str) -> list[str]:
    topics: list[str] = []
    if "## Clean list" in text:
        for line in text.split("## Clean list", 1)[1].splitlines():
            if line.startswith("- "):
                t = line[2:].strip()
                if t:
                    topics.append(t)
        return topics
    for line in text.splitlines():
        if line.startswith("#") or not line.strip():
            continue
        if ":" not in line:
            continue
        _, rest = line.split(":", 1)
        rest = re.sub(r"\s*\([^)]*in OCR\)", "", rest)
        for raw in rest.split(","):
            t = raw.strip()
            if t:
                topics.append(t)
    return topics


def normalize(s: str) -> str:
    s = s.lower()
    s = s.replace("&", "&")
    s = re.sub(r"\s+", " ", s)
    return s


def gather_corpus() -> dict[str, str]:
    files = {}
    for p in [SKILL_ROOT / "SKILL.md", SKILL_ROOT / "references" / "extras.md"]:
        if p.exists():
            files[str(p.relative_to(SKILL_ROOT))] = p.read_text()
    for i, (_, rel) in LAYERS.items():
        p = SKILL_ROOT / rel
        files[rel] = p.read_text()
    return files


def find_topic(topic: str, corpus: dict[str, str]) -> list[str]:
    needle = normalize(topic)
    hits = []
    synonyms = SYNONYMS.get(needle, [])
    for rel, text in corpus.items():
        ntext = normalize(text)
        if needle in ntext or any(normalize(syn) in ntext for syn in synonyms):
            hits.append(rel)
    return hits


def main() -> int:
    topics = extract_topics(TOPICS_FILE.read_text())
    layer_map = json.loads(MAP_FILE.read_text())["layer"]
    corpus = gather_corpus()

    rows = []
    missing = []
    by_layer = defaultdict(list)
    for topic in topics:
        hits = find_topic(topic, corpus)
        intended = layer_map.get(topic)
        intended_rel = LAYERS[intended][1] if intended else None
        ok = bool(hits)
        if not ok:
            missing.append(topic)
        primary = intended_rel if intended_rel in hits else (hits[0] if hits else "MISSING")
        layer_name = LAYERS[intended][0] if intended else "UNMAPPED"
        layer_no = intended or 0
        rows.append((layer_no, layer_name, topic, primary, hits))
        by_layer[layer_no].append(topic)

    # Write COVERAGE.md
    out = []
    out.append("# Full-Stack Vibe Coder — topic coverage")
    out.append("")
    out.append("This file is generated by `scripts/check-coverage.py`. It maps every topic in")
    out.append("`vibe-coder-survival-topics.md` to a production layer and the skill file that covers it.")
    out.append("")
    out.append(f"- Topics extracted: **{len(topics)}**")
    out.append(f"- Topics found in skill files: **{len(topics) - len(missing)}**")
    out.append(f"- Gaps: **{len(missing)}**")
    out.append("")
    if missing:
        out.append("## Gaps")
        out.append("")
        for t in missing:
            out.append(f"- {t}")
        out.append("")
    out.append("## Counts per layer")
    out.append("")
    out.append("| Layer | Name | Topics |")
    out.append("| ---: | --- | ---: |")
    for i, (name, _) in LAYERS.items():
        out.append(f"| {i} | {name} | {len(by_layer[i])} |")
    extras_note = "See [references/extras.md](references/extras.md) for production extras not in the original list (SPF/DKIM/DMARC, payments/webhook idempotency, i18n, SEO basics, analytics consent, legal pages, env-specific config)."
    out.append("")
    out.append(extras_note)
    out.append("")
    out.append("## Topic map")
    out.append("")
    out.append("| Topic | Layer | Primary file | Also found in |")
    out.append("| --- | --- | --- | --- |")
    for layer_no, layer_name, topic, primary, hits in rows:
        also = ", ".join(h for h in hits if h != primary) or "—"
        label = f"{layer_no} {layer_name}" if layer_no else layer_name
        # escape pipes in topic names
        t = topic.replace("|", "\\|")
        out.append(f"| {t} | {label} | `{primary}` | {also} |")
    out.append("")

    dest = SKILL_ROOT / "COVERAGE.md"
    dest.write_text("\n".join(out))
    print(f"topics={len(topics)} found={len(topics)-len(missing)} missing={len(missing)}")
    if missing:
        print("MISSING:")
        for t in missing:
            print(f"  - {t}")
    print(f"wrote {dest}")
    for i, (name, _) in LAYERS.items():
        print(f"  L{i:02d} {len(by_layer[i]):3d}  {name}")
    unmapped = [t for t in topics if t not in layer_map]
    if unmapped:
        print("UNMAPPED:", unmapped)
    return 1 if missing or unmapped else 0


if __name__ == "__main__":
    sys.exit(main())
