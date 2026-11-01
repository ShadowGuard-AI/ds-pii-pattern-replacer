#!/usr/bin/env python3
"""ds-pii-pattern-replacer: I read a text file, find the personally
identifiable information hiding in it, and replace each match with a
plain token like [EMAIL] so the file can be shared without sharing
the people in it.

What I catch: email addresses, US phone numbers, US Social Security
numbers, and payment card numbers. Card candidates have to pass the
Luhn check, because a long number is not automatically a card and I
do not redact arithmetic.

The matched values are never printed anywhere, not in the summary,
not in an error. Counts only. A file with nothing to replace is a
run that processed nothing: I exit non-zero and write no output.
"""

import argparse
import json
import re
import sys
from pathlib import Path

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")
SSN_RE = re.compile(r"\b(\d{3})-(\d{2})-(\d{4})\b")
CARD_RE = re.compile(r"\b(?:\d[ \-]?){12,18}\d\b")
PHONE_RE = re.compile(
    r"(?:\+?1[\s.\-]?)?(?:\(\d{3}\)\s?|\d{3}[\s.\-])\d{3}[\s.\-]\d{4}\b")


def luhn_ok(digits):
    """The checksum every real card number carries."""
    total = 0
    for i, ch in enumerate(reversed(digits)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def valid_ssn(area, group, serial):
    """Reject the ranges the SSA never issues, so order numbers and
    ZIP-plus-four fragments survive untouched."""
    area_n = int(area)
    return area_n not in (0, 666) and area_n < 900 \
        and group != "00" and serial != "0000"


def replace_all(text, kinds):
    """Run the replacers in an order that keeps them out of each
    other's way: cards first (their digit runs contain everything
    else's shape), then SSNs, then emails, then phones."""
    counts = {}

    def card_sub(m):
        digits = re.sub(r"\D", "", m.group(0))
        if 13 <= len(digits) <= 19 and luhn_ok(digits):
            counts["card"] = counts.get("card", 0) + 1
            return "[CARD]"
        return m.group(0)

    def ssn_sub(m):
        if valid_ssn(*m.groups()):
            counts["ssn"] = counts.get("ssn", 0) + 1
            return "[SSN]"
        return m.group(0)

    def email_sub(m):
        counts["email"] = counts.get("email", 0) + 1
        return "[EMAIL]"

    def phone_sub(m):
        counts["phone"] = counts.get("phone", 0) + 1
        return "[PHONE]"

    if "card" in kinds:
        text = CARD_RE.sub(card_sub, text)
    if "ssn" in kinds:
        text = SSN_RE.sub(ssn_sub, text)
    if "email" in kinds:
        text = EMAIL_RE.sub(email_sub, text)
    if "phone" in kinds:
        text = PHONE_RE.sub(phone_sub, text)
    return text, counts


def run(args):
    kinds = {k.strip() for k in args.types.split(",") if k.strip()}
    unknown = kinds - {"email", "phone", "ssn", "card"}
    if unknown:
        print(f"error: unknown types: {sorted(unknown)}", file=sys.stderr)
        return 2
    if args.input == "-":
        text = sys.stdin.read()
        in_path = None
    else:
        in_path = Path(args.input)
        if not in_path.is_file():
            print(f"error: no such file: {in_path}", file=sys.stderr)
            return 2
        text = in_path.read_text(errors="replace")
    if not text.strip():
        print("error: input is empty; nothing to process", file=sys.stderr)
        return 2
    cleaned, counts = replace_all(text, kinds)
    total = sum(counts.values())
    if total == 0:
        # Nothing replaced means this run did nothing, and I say so
        # with the exit code instead of writing back an untouched
        # file and calling it cleaned.
        print("no PII patterns found; nothing replaced", file=sys.stderr)
        return 2
    summary = {"replaced": total, "by_type": counts}
    if args.output:
        out = Path(args.output)
        if in_path is not None and out.resolve() == in_path.resolve():
            print("error: --output resolves to the input file; "
                  "refusing to overwrite it", file=sys.stderr)
            return 2
        out.write_text(cleaned)
    else:
        sys.stdout.write(cleaned)
    if args.json:
        print(json.dumps(summary), file=sys.stderr)
    else:
        parts = ", ".join(f"{k}={counts[k]}" for k in sorted(counts))
        print(f"replaced {total} item(s): {parts}", file=sys.stderr)
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog="ds-pii-pattern-replacer",
        description="Replace PII patterns (email, phone, SSN, payment "
                    "card) in a text file with plain tokens.")
    parser.add_argument("input", help="text file to clean, or - for stdin")
    parser.add_argument("--output",
                        help="write the cleaned text here instead of stdout")
    parser.add_argument("--types", default="email,phone,ssn,card",
                        help="comma list of kinds to replace "
                             "(default: email,phone,ssn,card)")
    parser.add_argument("--json", action="store_true",
                        help="print the replacement summary as JSON "
                             "to stderr")
    return parser


def main(argv=None):
    return run(build_parser().parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
