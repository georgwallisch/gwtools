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
import sys
import string
from typing import List


# ----------------------------
# Konfiguration
# ----------------------------

ENTROPY_PRESETS = {
    "weak": 50,
    "good": 70,
    "strong": 100,
    "stronger": 128,
    "tough": 192,    
    "paranoid": 256,
    "insane": 512    
}

PROGNAME = "gwpgen"
VERSION = "1.2"

UPPER = string.ascii_uppercase
LOWER = string.ascii_lowercase
DIGITS = string.digits
HEXLOW = DIGITS + LOWER[0:6]
HEXUP = DIGITS + UPPER[0:6]
SYMBOLS = "!$%&(),.-;:#+"
MAX_ENTROPY = 1000
MAX_LENGTH = 250
MAX_NUMBER = 500
urandom_bytes_used = 0


# ----------------------------
# Zufallsfunktionen
# ----------------------------

def rand_index(k: int, mask: int) -> int:
    """Ziehe einen gleichverteilten Index < k mittels Rejection Sampling."""
    while True:
        b = int.from_bytes(random_bytes(1), "big") & mask
        if b < k:
            return b

def secure_shuffle(items: List[str]) -> None:
    for i in range(len(items) - 1, 0, -1):
        bits = math.ceil(math.log2(i + 1))
        mask = (1 << bits) - 1
        j = rand_index(i + 1, mask)
        items[i], items[j] = items[j], items[i]

def random_char_from(alphabet: str, mask: int) -> str:
    idx = rand_index(len(alphabet), mask)
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

    if not alphabet:
        raise ValueError("Alphabet became empty after removing separator")

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
        
    entropy = length * entropy_per_char
        
    logging.debug("Alphabet size: %d", k)
    logging.debug("Alphabet: %s", alphabet)
    logging.debug("RNG bits per character: %d", bits)
    logging.debug("Entropy per char: %.2f", entropy_per_char)
    if target_length:
        logging.debug("Target length: %d", target_length)
    if target_entropy:
        logging.debug("Target entropy: %d bits", target_entropy)
    logging.debug("Calculated length: %d", length)
    if remainder != 0:
        logging.debug("Added %d characters to pad the final group", (group-remainder))
    logging.debug("Theoretical entropy: %.2f bits", entropy)
       
    passwords: List[str] = []
    
    for _ in range(number):
        passwords.append(build_password(alphabet=alphabet,
                                        classes=classes,
                                        bits=bits,
                                        length=length,
                                        enforce_classes=enforce_classes,
                                        group=group,
                                        separator=separator))
    
    logging.debug("Output length: %d", len(passwords[0]))
    logging.debug("Random bytes read from OS RNG: %d", urandom_bytes_used)  
    
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
            password_chars.append(random_char_from(cls, mask))

    while len(password_chars) < length:
        password_chars.append(random_char_from(alphabet, mask))

    secure_shuffle(password_chars)

    pw = "".join(password_chars)

    if group > 0:
        pw = separator.join(
            pw[i:i + group] for i in range(0, len(pw), group)
        )
    
    return pw
    
def format_wifi(ssid:str, pw:str, hidden:bool):
    
    ssid_escaped = escape_wifi_string(ssid)
    pw_escaped = escape_wifi_string(pw)

    wifi = f"WIFI:T:WPA;S:{ssid_escaped};P:{pw_escaped};"
    if hidden:
        wifi += "HIDDEN:true;"
    wifi += ";"

    return wifi
    
def escape_wifi_string(s: str) -> str:
    """Escape special characters for WiFi QR code format."""
    return (
        s.replace("\\", "\\\\")
         .replace(";", "\\;")
         .replace(",", "\\,")
         .replace(":", "\\:")
         .replace('"', '\\"')
    )
    
def write_passwords(passwords, args):

    end = "" if args.no_newline else "\n"

    f = None

    if args.output:
        if os.path.exists(args.output) and not args.force:
            raise ValueError(f"File '{args.output}' already exists (use --force to overwrite)")
        try:
            f = open(args.output, "w", encoding="utf-8")
        except OSError as e:
            raise ValueError(f"Cannot write to '{args.output}': {e.strerror}")

    try:
        for pw in passwords:
            if args.wifi:
                pw = format_wifi(ssid=args.wifi, pw=pw, hidden=False)
            elif args.wifi_hidden:
                pw = format_wifi(ssid=args.wifi, pw=pw, hidden=True)

            if f:
                f.write(pw + end)

            if not f or args.tee:
                print(pw, end=end)

    finally:
        if f:
            f.close()

def read_passwords(path):
    if path == "-":
        return [line.strip() for line in sys.stdin if line.strip()]
    else:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return [line.strip() for line in f if line.strip()]
        except OSError as e:
            raise ValueError(f"Cannot read from '{path}': {e.strerror}")


# ----------------------------
# CLI
# ----------------------------

def main() -> None:
    try:
        parser = argparse.ArgumentParser(
            description="Cryptographically sound password generator"
        )
        
        length_group = parser.add_mutually_exclusive_group()
        length_group.add_argument("-b", "--entropy-bits", type=int)
        length_group.add_argument("-L", "--length", type=int)
        
        for preset, bits in ENTROPY_PRESETS.items():
            length_group.add_argument(f"--{preset}", action="store_const",
                            const=preset, dest="preset", help=f"Entropy preset: {bits} bits")
        
        parser.add_argument("-a","--alphanum", action="store_true",
                            help="Alphanumeric characters (A–Z, a-z, 0-9)")
        parser.add_argument("-u","--upper", action="store_true",
                            help="Uppercase letters (A–Z)")
        parser.add_argument("-l","--lower", action="store_true",
                            help="Lowercase letters (a–z)")
        parser.add_argument("-d","--digits", action="store_true",
                            help="Digits (0–9)")
        parser.add_argument("-m", "--symbols", nargs="?", const=SYMBOLS,
                            help="Use symbols (optionally specify custom alphabet)")
        parser.add_argument("-x","--hex-lower", action="store_true",
                            help="Lowercase hexadecimal characters (0-9a-f)")
        parser.add_argument("-X","--hex-upper", action="store_true",
                            help="Uppercase hexadecimal characters (0-9A-F)")

        parser.add_argument("--no-enforce-classes", action="store_false", dest="enforce_classes",
                            help="Do not enforce at least one character per class")
        parser.set_defaults(enforce_classes=True)

        parser.add_argument("-g", "--group", type=int, default=0,
                            help="Group characters into blocks")
        parser.add_argument("-s","--separator", default="-",
                            help="Group separator")
        parser.add_argument("-p","--pad-group", action="store_true",
                            help="Pad the last group to full group length")
        parser.add_argument("-o", "--output",
                            help="Write generated password(s) to a file")
        parser.add_argument("--force", action="store_true",
                            help="Force overwrite existing file")
        parser.add_argument("-i", "--input", metavar="FILE",
                            help="Read existing password(s) from file or '-' for stdin")
        
        parser.add_argument("--tee", action="store_true",
                            help="Write password(s) both to stdout and output file")

        wifi_group = parser.add_mutually_exclusive_group()

        wifi_group.add_argument("-W", "--wifi", metavar="SSID",
                            help="Output password as WiFi QR string for given SSID")
        
        wifi_group.add_argument("--wifi-hidden", metavar="SSID",
                            help="Output password as WiFi QR string for given SSID and set hidden")        

        parser.add_argument("-N", "--number", type=int, default=1,
                            help="Generate N passwords (default: 1)")

        parser.add_argument("-n","--no-newline", action="store_true",
                            help="Do not append a trailing newline")
        
        parser.add_argument("--no-limits", action="store_true",
                            help="Disable safety limits for entropy and password length")

        parser.add_argument("-v", "--verbose", action="store_true",
                            help="Verbose output")
        
        parser.add_argument("-V", "--version", action="version", version=f"{PROGNAME} {VERSION}")

        args = parser.parse_args()

        logging.basicConfig(
            level=logging.DEBUG if args.verbose else logging.WARNING,
            format="%(message)s"
        )
        
        if args.input:
           passwords = read_passwords(args.input)
                   
        else:
            
            if not (args.length or args.entropy_bits or args.preset):
                parser.error("Must specify --length, --entropy-bits, or a preset")
           
            if args.number < 1:
                parser.error("--number must be >= 1")
                
            if args.number > 1 and (args.wifi or args.wifi_hidden):
                parser.error("--wifi options cannot be used with --number > 1")
    
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
            if args.symbols is not None:
                if args.symbols == "":
                    parser.error("Symbol alphabet must not be empty")
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
                    parser.error("Use an entropy preset, or specify --entropy-bits or --length")
     
            if not args.no_limits:
                
                if entropy and entropy > MAX_ENTROPY:
                    parser.error(f"Entropy limit exceeded (max {MAX_ENTROPY} bits). Use --no-limits to override.")
            
                if length and length > MAX_LENGTH:
                    parser.error(f"Length limit exceeded (max {MAX_LENGTH}). Use --no-limits to override.")
                    
                if args.number > MAX_NUMBER:
                    parser.error(f"Number limit exceeded (max {MAX_NUMBER}). Use --no-limits to override.")

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
