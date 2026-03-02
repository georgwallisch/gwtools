# gwtools

Small security-focused command-line utilities.

Currently included:

- `gwpgen.py` – entropy-driven, cryptographically sound password generator

---

## gwpgen – Entropy-Driven Password Generator

`gwpgen` is a cryptographically clean password generator designed with
a strict focus on:

- measurable entropy instead of arbitrary complexity rules
- unbiased random selection (rejection sampling)
- bias-free Fisher–Yates shuffle
- explicit character class enforcement
- reproducible entropy targets (e.g. 100-bit, 256-bit)

The design goal is not “memorable passwords” but mathematically
well-defined randomness suitable for:

- WPA/WPA3 PSKs
- API keys
- device provisioning
- offline secrets
- infrastructure credentials

---

## Design Principles

### 1. Entropy-Based Length Calculation

Password length is derived from the requested entropy:


length = ceil(target_entropy / log2(alphabet_size))


No arbitrary length defaults.

---

### 2. Uniform Randomness

Character selection uses rejection sampling to avoid modulo bias.

---

### 3. Bias-Free Shuffle

Class-enforced characters are shuffled using a cryptographically correct
Fisher–Yates algorithm without modulo bias.

---

### 4. No Policy Theater

No artificial "must contain symbol" rules unless explicitly requested.
Character classes are enforced only if selected.

---

## Examples

Generate 100-bit alphanumeric password:


python3 gwpgen.py --strong --alphanum

MIT License – see LICENSE file.
