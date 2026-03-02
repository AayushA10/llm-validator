import json
import os
import re
import sys
from datetime import date

from bad_deed_validator.core.exceptions import DateOrderError, AmountMismatchError
from bad_deed_validator.utils.text_norm import normalize_county_name, resolve_county_alias
from bad_deed_validator.llm.stub import extract_structured_data
from bad_deed_validator.core.models import RAW_OCR_TEXT


class DeedValidator:
    def run(self):
        data = extract_structured_data(RAW_OCR_TEXT)
        counties = self._load_counties()

        county_raw = data.get("county", "") or ""
        tax_rate = self._lookup_tax_rate(counties, county_raw)

        signed = self._parse_date(data.get("date_signed"))
        recorded = self._parse_date(data.get("date_recorded"))

        amount_digits = self._parse_amount_digits(data.get("amount_digits"))
        amount_words_num = self._words_to_number(data.get("amount_words", ""))

        errors = []

        try:
            self._check_date_order(signed, recorded)
        except DateOrderError as e:
            errors.append(str(e))

        try:
            self._check_amount_match(amount_digits, amount_words_num)
        except AmountMismatchError as e:
            errors.append(str(e))

        result = {
            "doc_id": data.get("doc_id"),
            "county_raw": county_raw,
            "tax_rate": tax_rate,
            "date_signed": str(signed) if signed else None,
            "date_recorded": str(recorded) if recorded else None,
            "amount_digits": int(round(amount_digits)) if amount_digits is not None else None,
            "amount_words": data.get("amount_words", "") or "",
            "amount_words_num": int(amount_words_num) if amount_words_num is not None else None,
            "errors": errors,
            "status": "FAILED" if errors else "PASSED"
        }

        print(json.dumps(result, indent=2))

        if errors:
            sys.exit(1)

        sys.exit(0)

    def _load_counties(self):
        base_dir = os.path.dirname(os.path.dirname(__file__))
        path = os.path.join(base_dir, "data", "counties.json")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _lookup_tax_rate(self, counties, county_name):
        target = resolve_county_alias(normalize_county_name(county_name))

        for c in counties:
            name = normalize_county_name(c.get("name", ""))
            if name == target:
                return c.get("tax_rate")

        return None

    def _parse_date(self, s):
        if not s:
            return None
        y, mo, d = s.split("-")
        return date(int(y), int(mo), int(d))

    def _check_date_order(self, signed, recorded):
        if signed is None or recorded is None:
            return
        if recorded < signed:
            raise DateOrderError("Recorded date is earlier than signed date")

    def _parse_amount_digits(self, s):
        if not s:
            return None
        m = re.search(r"\$([0-9,]+(?:\.[0-9]{2})?)", s)
        if not m:
            return None
        return float(m.group(1).replace(",", ""))

    def _words_to_number(self, words):
        w = words.lower().replace("-", " ")
        w = re.sub(r"[^a-z\s]", "", w)
        parts = [p for p in w.split() if p]

        small = {
            "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
            "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
            "seventeen": 17, "eighteen": 18, "nineteen": 19,
            "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90
        }

        mult = {"thousand": 1000, "million": 1000000}

        total = 0
        current = 0

        for token in parts:
            if token in small:
                current += small[token]
            elif token == "hundred":
                if current == 0:
                    current = 1
                current *= 100
            elif token in mult:
                if current == 0:
                    current = 1
                total += current * mult[token]
                current = 0

        return total + current

    def _check_amount_match(self, digits, words_num):
        if digits is None or words_num is None:
            return

        digits_int = int(round(digits))
        words_int = int(words_num)

        if digits_int != words_int:
            diff = abs(digits_int - words_int)
            raise AmountMismatchError(f"Amount mismatch: digits={digits_int} words={words_int} diff={diff}")