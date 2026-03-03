#!/usr/bin/env python3
"""
gwpgen.py – entropy-driven, cryptographically sound password generator

Part of the gwtools project:
https://github.com/georgwallisch/gwtools

Copyright (c) 2026 Georg Wallisch
License: MIT
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
    "weak": 50,
    "good": 70,
    "strong": 100,
    "stronger": 125,
    "tough": 150,    
    "paranoid": 200,
    "insane": 256    
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
        b = int.from_bytes(os.urandom(1), "big") & mask
        if b < k:
            return b

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
                   target_length: int,
                   target_entropy: int,
                   group: int,
                   separator: str,
                   pad_group: bool) -> str:

    k = len(alphabet)
    min_length = len(classes)
    bits = math.ceil(math.log2(k))
    mask = (1 << bits) - 1
    entropy_per_char = math.log2(k)

    if target_length:
        length = target_length
    elif target_entropy:
        length = math.ceil(target_entropy / entropy_per_char)
    else:
        raise ValueError("Neither length nor target entropy given")     
        
    remainder = 0
    if group > 0 and pad_group:
        remainder = length % group
        if remainder != 0:
            length += group - remainder
            
    if length < min_length:
        raise ValueError("Length too short for selected character classes")
        
    entropy = length * math.log2(k) 

    logging.debug("Alphabetgröße: %d", k)
    logging.debug("Bits pro Zeichen: %d", bits)
    logging.debug("Entropie/Z.: %.2f", entropy_per_char)
    if target_length:
        logging.debug("Ziellänge: %d", target_length)
    if target_entropy:
        logging.debug("Zielentropie: %d Bit", target_entropy)
    logging.debug("Berechnete Länge: %d", length)
    if remainder != 0:
        logging.debug("Länge wurde um %d Zeichen erweitert zum Auffüllen", (group-remainder))
    logging.debug("Berechnete Entropie: %.2f Bit", entropy)
        
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
        logging.debug("Gesamtlänge mit Gruppierungszeichen: %d", len(pw))       
    

    return pw


# ----------------------------
# CLI
# ----------------------------

def main() -> None:
    try:
        parser = argparse.ArgumentParser(
            description="Kryptographisch saubere Passworterzeugung"
        )
        
        length_group = parser.add_mutually_exclusive_group(required=True)
        length_group.add_argument("-b", "--entropy-bits", type=int)
        length_group.add_argument("-L", "--length", type=int)
        
        for preset, bits in ENTROPY_PRESETS.items():
            length_group.add_argument(f"--{preset}", action="store_const",
                            const=preset, dest="preset", help=f"Entropy preset: {bits} bits")
        
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
        parser.add_argument("-p","--pad-group", action="store_true",
                            help="Bei Gruppierung die letzte Gruppe auf gleiche Länge auffüllen")
        
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
            
        length = None
        entropy = None
            
        if args.length:
            length = args.length
        else:   
            if args.entropy_bits:
                entropy = args.entropy_bits
            elif args.preset:
                entropy = ENTROPY_PRESETS[args.preset]
            else:
                parser.error("Entropy-Preset, --entropy-bits oder Länge angeben!")

        password = build_password(
            alphabet=alphabet,
            classes=classes,
            target_length=length,
            target_entropy=entropy,
            group=args.group,
            separator=args.separator,
            pad_group=args.pad_group
        )

        end = "\n"

        if args.no_newline:
            end = ""

        print(password, end=end)

    except ValueError as e:
        parser.error(str(e))
    
    except Exception:
        logging.exception("Unhandled exception in main")
        raise

if __name__ == "__main__":
    main()
