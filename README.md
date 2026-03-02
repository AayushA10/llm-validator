# LLM Validator – Safe Deed Processing Pipeline

This project demonstrates a clean, production-style workflow for combining an LLM-based extraction layer with deterministic validation logic.

The goal is **not** to rely blindly on AI, but to show strong engineering hygiene:
- LLMs extract
- Deterministic code validates
- Errors are explicit
- Output is structured
- Failures return non-zero exit codes

---

## 🔎 Problem Overview

We are given messy OCR text representing a deed recording request.

The system must:

1. **Extract structured data using an LLM**
2. **Enrich the data using internal reference sources**
3. **Run strict sanity checks**
4. **Fail loudly when inconsistencies exist**

---

## 🏗 Architecture
Raw OCR Text
↓
LLM Stub (Structured Extraction Layer)
↓
Deterministic Validator
↓
JSON Result + Exit Code


### Separation of Concerns

- `llm/stub.py`  
  Responsible only for converting raw text into a structured object.

- `core/validator.py`  
  Performs deterministic checks. No parsing logic mixed in.

- `utils/text_norm.py`  
  Handles normalization and alias resolution.

- `data/counties.json`  
  Reference dataset for tax rates.

This ensures the LLM layer remains probabilistic, while validation remains deterministic.

---

## 🧠 Extraction Layer (LLM Stub)

The LLM layer parses:

- Document ID
- County
- Dates
- Amount (digits + words)
- Grantor / Grantee
- APN
- Status

In this implementation:
- A regex-based stub simulates an LLM.
- The validator consumes only the structured object returned.

This models a real-world setup where:
> AI extracts → deterministic code verifies.

---

## 📊 Data Enrichment

The OCR text contains:
County: S. Clara


Our internal database contains:
Santa Clara


### Solution

1. Normalize text (lowercase, remove punctuation)
2. Apply alias resolution (`S Clara → Santa Clara`)
3. Lookup tax rate in `counties.json`

Result: tax_rate: 
0.012


This prevents relying on AI to "guess" matching logic.

---

## ✅ Sanity Checks (Deterministic)

### 1️⃣ Date Logic Check

If:
Recorded < Signed


The system raises a `DateOrderError`.

We do not trust the LLM for date validation.

---

### 2️⃣ Amount Consistency Check

Given:
$1,250,000
One Million Two Hundred Thousand Dollars


The system:
- Extracts numeric digits
- Converts words → numeric value
- Compares strictly
- Reports exact difference

Example error:
Amount mismatch: digits=1250000 words=1200000 diff=50000


We flag inconsistencies instead of silently choosing one value.

---

## 📦 Output Format

The validator prints structured JSON:

```json
{
  "doc_id": "DEED-TRUST-0042",
  "county_raw": "S. Clara",
  "tax_rate": 0.012,
  "date_signed": "2024-01-15",
  "date_recorded": "2024-01-10",
  "amount_digits": 1250000,
  "amount_words": "One Million Two Hundred Thousand Dollars",
  "amount_words_num": 1200000,
  "errors": [
    "Recorded date is earlier than signed date",
    "Amount mismatch: digits=1250000 words=1200000 diff=50000"
  ],
  "status": "FAILED"
}
Exit code:
0 → PASSED
1 → FAILED

▶ Running the Project
From project root:
export PYTHONPATH=src
python3 -m bad_deed_validator
echo $?

Demo PASS Mode
To demonstrate both states:
DEMO_PASS=1 python3 -m bad_deed_validator
echo $?

This corrects the date and amount internally to show a successful validation.

🛠 Design Decisions
Why separate LLM and validation?

LLMs are probabilistic.
Financial and legal validation must be deterministic.
The system enforces:
AI can extract
AI cannot approve correctness
Deterministic logic must validate critical constraints

Why not trust the AI for sanity checks?
Because:
Dates can look plausible but still be invalid
Amount discrepancies must be mathematically verified
Financial systems require strict consistency

🧹 Engineering Hygiene
Clean project structure
Layered architecture
No silent error swallowing
Explicit error types
Structured output
Exit codes for automation
No unnecessary dependencies
.gitignore included

📌 Summary
This implementation demonstrates:
LLM extraction boundary
Deterministic validation layer
Safe enrichment logic
Structured CLI behavior
Clean separation of concerns

The system fails loudly when inconsistencies exist and never silently overrides conflicting financial data.

