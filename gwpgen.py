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
urandom_bytes_used = 0


# ----------------------------
# Zufallsfunktionen
# ----------------------------

def rand_index(k: int, bits: int, mask: int) -> int:
    """Ziehe einen gleichverteilten Index < k mittels Rejection Sampling."""
    while True:
        b = int.from_bytes(random_bytes(1), "big") & mask
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
    
def random_bytes(n):
    global urandom_bytes_used
    urandom_bytes_used += n
    return os.urandom(n)

# ----------------------------
# Hauptlogik
# ----------------------------

def build_passwords(alphabet: str,
                   classes: List[str],
                   target_length: int,
                   target_entropy: int,
                   enforce_classes: bool,
                   group: int,
                   separator: str,
                   pad_group: bool,
                   number: int) -> List[str]:

    if group > 0 and separator in alphabet:
        alphabet = alphabet.replace(separator, "")

    alphabet = "".join(sorted(set(alphabet)))

    k = len(alphabet)
    min_length = len(classes)
    bits = math.ceil(math.log2(k))

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

    logging.debug("Alphabet size: %d", k)
    logging.debug("Bits per character: %d", bits)
    logging.debug("Entropy per char: %.2f", entropy_per_char)
    if target_length:
        logging.debug("Target length: %d", target_length)
    if target_entropy:
        logging.debug("Target entropy: %d bits", target_entropy)
    logging.debug("Calculated length: %d", length)
    if remainder != 0:
        logging.debug("Added %d more characters to pad group", (group-remainder))
    logging.debug("Calculated entropy: %.2f bits", entropy)
       
    passwords: List[str] = []
    
    for _ in range(number):
        passwords.append(build_password(alphabet=alphabet,
                                        classes=classes,
                                        bits=bits,
                                        length=length,
                                        enforce_classes=enforce_classes,
                                        group=group,
                                        separator=separator))
    
    logging.debug("Total grouped length: %d", len(passwords[0]))
    logging.debug("Total entropy consumed: %d bytes", urandom_bytes_used)
    
    return passwords
    
    
def build_password(alphabet: str,
                   classes: List[str],
                   bits: int,
                   length: int,
                   enforce_classes: bool,
                   group: int,
                   separator: str) -> str:
        
    mask = (1 << bits) - 1
    password_chars: List[str] = []

    # enforce classes
    if enforce_classes:
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
    
def write_passwords(passwords, args):
    
    end = "\n"

    if args.no_newline:
        end = ""

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            for pw in passwords:
                f.write(pw + end)

                if args.tee:
                    print(pw, end=end)

    else:
        for pw in passwords:
            print(pw, end=end)


# ----------------------------
# CLI
# ----------------------------

def main() -> None:
    try:
        parser = argparse.ArgumentParser(
            description="Cryptographically sound password generator"
        )
        
        length_group = parser.add_mutually_exclusive_group(required=True)
        length_group.add_argument("-b", "--entropy-bits", type=int)
        length_group.add_argument("-L", "--length", type=int)
        
        for preset, bits in ENTROPY_PRESETS.items():
            length_group.add_argument(f"--{preset}", action="store_const",
                            const=preset, dest="preset", help=f"Entropy preset: {bits} bits")
        
        parser.add_argument("-a","--alphanum", action="store_true",
                            help="Alphanumeric characters A–Z, a-z, 0-9")
        parser.add_argument("-u","--upper", action="store_true",
                            help="Upppercase letters (A–Z)")
        parser.add_argument("-l","--lower", action="store_true",
                            help="Lowercase letters (a–z)")
        parser.add_argument("-d","--digits", action="store_true",
                            help="Digits (0–9)")
        parser.add_argument("-m", "--symbols", nargs="?", const=SYMBOLS,
                            help="Use symbols (optional custom alphabet)")
        parser.add_argument("-x","--hex-lower", action="store_true",
                            help="Lowercase hexadecimal characters (0-9a-f)")
        parser.add_argument("-X","--hex-upper", action="store_true",
                            help="Uppercase hexadecimal characters (0-9A-F)")
        
        parser.add_argument("-E", "--enforce-classes", action="store_true", default=True,
                            help="Enforce at least one character per character class (default)")
        parser.add_argument("--no-enforce-classes", action="store_false", dest="enforce_classes",
                            help="Do not enforce at least one character per character class")

        parser.add_argument("-g", "--group", type=int, default=0,
                            help="Group characters to blocks")
        parser.add_argument("-s","--separator", default="-",
                            help="Group separator")
        parser.add_argument("-p","--pad-group", action="store_true",
                            help="Pad last group to group length")
        parser.add_argument("-o", "--output",
                            help="Write generated password to file")
        parser.add_argument("--tee", action="store_true",
                            help="Write password both to stdout and output file")

        parser.add_argument("-N", "--number", type=int, default=1,
                            help="How many passwords to generate")

        parser.add_argument("-n","--no-newline", action="store_true",
                            help="No newline at output")

        parser.add_argument("-v", "--verbose", action="store_true",
                            help="Verbose output")
        
        parser.add_argument("-V", "--version", action="version", version="gwpgen 1.0")

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
            classes.append(args.symbols)
            alphabet += args.symbols

        if not alphabet:
            parser.error("Select at least one character class")
            
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
                parser.error("Use entropy preset or set --entropy-bits or --length!")
                
        passwords = build_passwords(
            alphabet=alphabet,
            classes=classes,
            target_length=length,
            target_entropy=entropy,
            enforce_classes=args.enforce_classes,
            group=args.group,
            separator=args.separator,
            pad_group=args.pad_group,
            number=args.number
        )

        write_passwords(passwords, args)
        
    except ValueError as e:
        parser.error(str(e))
    
    except Exception:
        logging.exception("Unhandled exception in main")
        raise

if __name__ == "__main__":
    main()
