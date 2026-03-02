#!/usr/bin/env python3
"""
pwgen.py – kryptographisch saubere Passworterzeugung
"""

import argparse
import logging
import math
import os
import string
from typing import List


# ----------------------------
# Konfiguration
# ----------------------------

ENTROPY_PRESETS = {
    "good": 70,
    "strong": 100,
    "stronger": 125,
    "paranoid": 256,
}

UPPER = string.ascii_uppercase
LOWER = string.ascii_lowercase
DIGITS = string.digits
HEXLOW = DIGITS + LOWER[0:6]
HEXUP = DIGITS + UPPER[0:6]
SYMBOLS = "!$%&(),.-;:#+"


# ----------------------------
# Zufallsfunktionen
# ----------------------------

def rand_index(k: int, bits: int, mask: int) -> int:
    """Ziehe einen gleichverteilten Index < k mittels Rejection Sampling."""
    while True:
        b = os.urandom(1)[0] & mask
        if b < k:
            return b


#def secure_shuffle(items: List[str]) -> None:
#    """Fisher-Yates-Shuffle mit os.urandom()."""
#    for i in range(len(items) - 1, 0, -1):
#        j = os.urandom(1)[0] % (i + 1)
#        items[i], items[j] = items[j], items[i]

def secure_shuffle(items: List[str]) -> None:
    for i in range(len(items) - 1, 0, -1):
        bits = math.ceil(math.log2(i + 1))
        mask = (1 << bits) - 1
        j = rand_index(i + 1, bits, mask)
        items[i], items[j] = items[j], items[i]


def random_char_from(alphabet: str, bits: int, mask: int) -> str:
    idx = rand_index(len(alphabet), bits, mask)
    return alphabet[idx]


# ----------------------------
# Hauptlogik
# ----------------------------

def build_password(alphabet: str,
                   classes: List[str],
                   target_entropy: int,
                   group: int,
                   separator: str) -> str:

    k = len(alphabet)
    bits = math.ceil(math.log2(k))
    mask = (1 << bits) - 1
    entropy_per_char = math.log2(k)

    length = math.ceil(target_entropy / entropy_per_char)

    logging.debug("Alphabetgröße: %d", k)
    logging.debug("Bits pro Zeichen: %d", bits)
    logging.debug("Entropie/Z.: %.2f", entropy_per_char)
    logging.debug("Zielentropie: %d Bit", target_entropy)
    logging.debug("Berechnete Länge: %d", length)

    password_chars: List[str] = []

    # enforce classes
    for cls in classes:
        password_chars.append(random_char_from(cls, bits, mask))

    while len(password_chars) < length:
        password_chars.append(random_char_from(alphabet, bits, mask))

    secure_shuffle(password_chars)

    pw = "".join(password_chars)

    if group > 0:
        pw = separator.join(
            pw[i:i + group] for i in range(0, len(pw), group)
        )

    return pw


# ----------------------------
# CLI
# ----------------------------

def main() -> None:
    try:
        parser = argparse.ArgumentParser(
            description="Kryptographisch saubere Passworterzeugung"
        )

        preset = parser.add_mutually_exclusive_group(required=False)
        preset.add_argument("--good", action="store_const",
                            const="good", dest="preset")
        preset.add_argument("--strong", action="store_const",
                            const="strong", dest="preset")
        preset.add_argument("--stronger", action="store_const",
                            const="stronger", dest="preset")
        preset.add_argument("--paranoid", action="store_const",
                            const="paranoid", dest="preset")

        parser.add_argument("-b", "--entropy-bits", type=int)

        parser.add_argument("-a","--alphanum", action="store_true",
                            help="Alphanumerische Zeichen A–Z, a-z, 0-9")
        parser.add_argument("-u","--upper", action="store_true",
                            help="Großbuchstaben A–Z")
        parser.add_argument("-l","--lower", action="store_true",
                            help="Kleinbuchstaben a–z")
        parser.add_argument("-d","--digits", action="store_true",
                            help="Ziffern 0–9")
        parser.add_argument("-m","--symbols", action="store_true",
                            help="Sonderzeichen")
        parser.add_argument("-x","--hex-lower", action="store_true",
                            help="Hexadezimale Ziffern mit Kleinbuchstaben (0-9a-f)")
        parser.add_argument("-X","--hex-upper", action="store_true",
                            help="Hexadezimale Ziffern mit Großbuchstaben (0-9A-F)")

        parser.add_argument("-g", "--group", type=int, default=0,
                            help="Gruppierung (z.B. immer 4 Zeichen zu einem Block xxxx-xxxx-xxxx)")
        parser.add_argument("-s","--separator", default="-",
                            help="Trennzeichen für Gruppierung")
        parser.add_argument("-n","--no-newline", action="store_true",
                            help="Kein Zeilenumbruch bei der Ausgabe (für Piping)")

        parser.add_argument("-v", "--verbose", action="store_true",
                            help="Debug-Ausgaben")

        args = parser.parse_args()

        logging.basicConfig(
            level=logging.DEBUG if args.verbose else logging.WARNING,
            format="%(message)s"
        )

        classes: List[str] = []
        alphabet = ""

        if args.hex_lower:
            classes.append(HEXLOW)
            alphabet += HEXLOW
        elif args.hex_upper:
            classes.append(HEXUP)
            alphabet += HEXUP
        else:
            if args.upper or args.alphanum:
                classes.append(UPPER)
                alphabet += UPPER
            if args.lower or args.alphanum:
                classes.append(LOWER)
                alphabet += LOWER
            if args.digits or args.alphanum:
                classes.append(DIGITS)
                alphabet += DIGITS
        if args.symbols:
            classes.append(SYMBOLS)
            alphabet += SYMBOLS

        if not alphabet:
            parser.error("Mindestens eine Zeichenklasse auswählen")

        if args.entropy_bits:
            target_entropy = args.entropy_bits
        elif args.preset:
            target_entropy = ENTROPY_PRESETS[args.preset]
        else:
            parser.error("Preset oder --entropy-bits angeben")

        password = build_password(
            alphabet=alphabet,
            classes=classes,
            target_entropy=target_entropy,
            group=args.group,
            separator=args.separator,
        )

        end = "\n"

        if args.no_newline:
            end = ""

        print(password, end=end)

    except Exception:
        logging.exception("Unhandled exception in main")
        raise

if __name__ == "__main__":
    main()
