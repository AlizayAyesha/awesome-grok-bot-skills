---
name: data-csv-analysis
description: When exploring, summarizing, or charting a CSV or tabular dataset the user provided — cleaning notes, stats, and cautious conclusions.
---

# Data CSV Analysis

Use this skill when the user shares a CSV (or similar table) and wants a summary, quality check, or analysis. Compute from the file. Do not invent rows.

## Steps

1. Profile the file: row count, columns, types, missing rates, obvious encodings, and a few sample rows. Flag identifier columns you will not treat as numeric.
2. Check quality: duplicates, impossible values, mixed date formats, leaked PII (emails, phones). Ask before sharing raw PII back in a document that might travel.
3. Answer the user's question with aggregations they asked for (or, if open-ended: distributions, top groups, simple trends). State filters you applied.
4. Prefer simple stats and comparisons over a model. If you fit a model, say it is exploratory.
5. When you plot, label axes and units. Call out small sample sizes.

## Output

- Data profile
- Quality issues
- Findings (each with the column/filter that supports it)
- Limitations and next checks
- Optional: the exact commands or a short Python/pandas or SQL snippet they can rerun

## Rules

- No causal claims from an observational CSV (`X causes Y`) unless the user has a real design — say "associated with."
- Do not drop columns or rows silently. If you cleaned, report it.
- If the file is too large or unreadable, say what failed; do not pad with typical industry numbers.
