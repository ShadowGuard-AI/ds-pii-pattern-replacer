![Banner](banner.png)

# ds-pii-pattern-replacer

I read a text file, find the personally identifiable information
hiding in it, and replace each match with a plain token, so the file
can be shared without sharing the people in it.

## What it replaces

- Email addresses become `[EMAIL]`.
- US phone numbers, in the common written forms, become `[PHONE]`.
- US Social Security numbers become `[SSN]`. I reject the ranges the
  Social Security Administration never issues (area 000, 666, and
  900 to 999, group 00, serial 0000), so look-alike order numbers
  survive.
- Payment card numbers become `[CARD]`, but only when the number
  passes the Luhn checksum. A long digit string that fails the
  checksum is arithmetic, not a card, and I leave it alone.

Two rules I do not bend:

- The matched values are never printed anywhere, not in the summary,
  not in an error message. You get counts, never the data.
- If nothing in the file matches, the run did nothing, and I say so:
  exit code 2, no output file written, no untouched copy passed off
  as cleaned.

## Install

```bash
git clone https://github.com/ShadowGuard-AI/ds-pii-pattern-replacer.git
cd ds-pii-pattern-replacer
```

Python 3, standard library only. There is nothing to install.

## Usage

```bash
python3 main.py customers.txt --output customers-clean.txt
```

Before:

```
Maria Garcia, maria.garcia@example.com, (262) 555-0147
Card on file: 4111-1111-1111-1111
SSN for payroll: 123-45-6789
Not a card (fails checksum): 4111 1111 1111 1112
```

After (and the summary on stderr reads
`replaced 6 item(s): card=1, email=2, phone=2, ssn=1` for the full
test file this example is drawn from):

```
Maria Garcia, [EMAIL], [PHONE]
Card on file: [CARD]
SSN for payroll: [SSN]
Not a card (fails checksum): 4111 1111 1111 1112
```

The example values are the usual published test numbers and
555-range fiction, taken from this tool's own test fixtures.

## Parameters

- `input`: the text file to clean, or `-` to read stdin.
- `--output`: write the cleaned text to this file instead of stdout.
  If it resolves to the input file, I refuse and exit 2 rather than
  overwrite the original.
- `--types`: comma list of kinds to replace, chosen from `email`,
  `phone`, `ssn`, `card`. Default is all four.
- `--json`: print the replacement summary as JSON (to stderr)
  instead of the plain line.

## Exit codes

- `0`: at least one replacement was made; cleaned text delivered.
- `2`: nothing was processed (missing or empty input, no PII found,
  unknown `--types` value, or the refused in-place output).

## Verified in this wave

No factual bug was found in the claims above. Runs in this wave, on the printed example, cleaned it to 4 items (card=1, email=1, phone=1, ssn=1); the 6 item summary quoted in the example refers to the fuller test file the example is drawn from, not to the printed snippet alone. A file with no PII exits 2 and writes no output file. An output path resolving to the input file is refused with exit 2. The JSON summary prints to stderr.

## License

MIT. See [LICENSE](LICENSE).
Copyright (c) Gavin K (@Epsilon0xCell).
