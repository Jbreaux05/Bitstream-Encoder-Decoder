#!/usr/bin/env python3
"""
Bitstream Encoding/Decoding using a 4B/5B translation table.
Default 4B/5B table is used if no custom table file is provided.
Asks whether to encode or decode, then prompts for the bitstream and performs the operation.
Outputs the table used and both the input and output bitstreams along with their lengths for verification.
"""

import sys
import os

# Standard 4B/5B encoding table (4-bit data -> 5-bit code)
DEFAULT_4B5B_TABLE = {
    "0000": "11110",
    "0001": "01001",
    "0010": "10100",
    "0011": "10101",
    "0100": "01010",
    "0101": "01011",
    "0110": "01110",
    "0111": "01111",
    "1000": "10010",
    "1001": "10011",
    "1010": "10110",
    "1011": "10111",
    "1100": "11010",
    "1101": "11011",
    "1110": "11100",
    "1111": "11101",
}


def load_table(filepath: str) -> dict[str, str]:
    """
    Load a translation table from a file.

    Expected format — one mapping per line:
        0000 11110
        0001 01001
        ...
    Lines starting with '#' are treated as comments and ignored.
    """
    table: dict[str, str] = {}
    with open(filepath, "r") as f:
        for lineno, raw in enumerate(f, start=1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) != 2:
                raise ValueError(
                    f"Line {lineno}: expected '<data> <code>', got: {raw!r}"
                )
            data, code = parts
            if not all(c in "01" for c in data):
                raise ValueError(
                    f"Line {lineno}: data symbol '{data}' contains non-binary characters."
                )
            if not all(c in "01" for c in code):
                raise ValueError(
                    f"Line {lineno}: code word '{code}' contains non-binary characters."
                )
            table[data] = code
    if not table:
        raise ValueError("Translation table is empty.")
    return table


def validate_table(table: dict[str, str]) -> None:
    """Verify that the table is a valid bijection (no duplicate codes) and,
    when the data symbol size is 4 bits, that all 16 possible 4-bit entries
    (0000–1111) are present."""
    codes = list(table.values())
    if len(codes) != len(set(codes)):
        seen: set[str] = set()
        for data, code in table.items():
            if code in seen:
                raise ValueError(
                    f"Duplicate code word '{code}' detected — table is not uniquely decodable."
                )
            seen.add(code)

    data_len = len(next(iter(table)))
    code_len = len(next(iter(table.values())))
    for data, code in table.items():
        if len(data) != data_len:
            raise ValueError(
                f"Inconsistent data symbol length: '{data}' has {len(data)} bits, expected {data_len}."
            )
        if len(code) != code_len:
            raise ValueError(
                f"Inconsistent code word length: '{code}' has {len(code)} bits, expected {code_len}."
            )

    # Every one of the 2^data_len possible symbols must have a mapping.
    all_symbols = {format(i, f"0{data_len}b") for i in range(2 ** data_len)}
    missing = sorted(all_symbols - table.keys())
    if missing:
        raise ValueError(
            f"Custom table is missing {len(missing)} of the {2 ** data_len} required "
            f"{data_len}-bit symbol(s): " + ", ".join(missing)
        )


def print_table(table: dict[str, str]) -> None:
    data_len = len(next(iter(table)))
    code_len = len(next(iter(table.values())))
    header = f"  {'Data':<{data_len + 2}}  {'Code':<{code_len + 2}}"
    print(header)
    print("  " + "-" * (data_len + code_len + 6))
    for data in sorted(table):
        print(f"  {data}  ->  {table[data]}")


def encode(bitstream: str, table: dict[str, str]) -> str:
    #Encode a bitstream using the translation table.
    data_len = len(next(iter(table)))
    if len(bitstream) % data_len != 0:
        raise ValueError(
            f"Bitstream length ({len(bitstream)}) is not a multiple of the "
            f"data symbol size ({data_len} bits)."
        )
    chunks = [bitstream[i : i + data_len] for i in range(0, len(bitstream), data_len)]
    encoded_parts: list[str] = []
    for chunk in chunks:
        if chunk not in table:
            raise ValueError(
                f"Symbol '{chunk}' not found in the translation table."
            )
        encoded_parts.append(table[chunk])
    return "".join(encoded_parts)


def decode(encoded_stream: str, table: dict[str, str]) -> str:
    #Decode an encoded bitstream using the reverse of the translation table.
    reverse: dict[str, str] = {code: data for data, code in table.items()}
    code_len = len(next(iter(table.values())))
    if len(encoded_stream) % code_len != 0:
        raise ValueError(
            f"Encoded stream length ({len(encoded_stream)}) is not a multiple of the "
            f"code word size ({code_len} bits)."
        )
    chunks = [encoded_stream[i : i + code_len] for i in range(0, len(encoded_stream), code_len)]
    decoded_parts: list[str] = []
    for chunk in chunks:
        if chunk not in reverse:
            raise ValueError(
                f"Code word '{chunk}' not found in the translation table."
            )
        decoded_parts.append(reverse[chunk])
    return "".join(decoded_parts)


def prompt_bitstream(prompt: str) -> str:
    """Prompt until the user enters a non-empty binary string."""
    while True:
        raw = input(prompt).strip()
        if not raw:
            print("  Error: bitstream cannot be empty. Please try again.")
            continue
        if not all(c in "01" for c in raw):
            print("  Error: bitstream must contain only '0' and '1'. Please try again.")
            continue
        return raw


def prompt_table() -> dict[str, str]:
    """Prompt for a table file path (or accept a CLI argument) and keep
    re-asking until a valid table is loaded, or the user presses Enter to
    use the default 4B/5B table."""
    # On the first call, honour a CLI argument if one was provided.
    first_path: str | None = sys.argv[1] if len(sys.argv) > 1 else None

    while True:
        if first_path is not None:
            path = first_path
            first_path = None  # only use it once
        else:
            path = input(
                "Enter path to translation table file "
                "(or press Enter to use default 4B/5B table): "
            ).strip()

        if not path:
            print("Using default 4B/5B translation table.")
            return DEFAULT_4B5B_TABLE

        if not os.path.isfile(path):
            print(f"  Error: file '{path}' not found. Please try again.")
            continue

        try:
            table = load_table(path)
            validate_table(table)
            print(f"Loaded translation table from '{path}' ({len(table)} entries).")
            return table
        except (ValueError, OSError) as exc:
            print(f"  Error loading table: {exc}")
            print("  Please provide a different file.")


def run_encoding(table: dict[str, str]) -> None:
    data_len = len(next(iter(table)))
    print(f"\n[Encoding Mode]  (data symbol size: {data_len} bits)")
    while True:
        bitstream = prompt_bitstream("  Enter bitstream to encode: ")
        try:
            encoded = encode(bitstream, table)
            break
        except ValueError as exc:
            print(f"  Encoding error: {exc}")
            print("  Please try again.")

    print("\n--- Translation Table ---")
    print_table(table)
    print("\n--- Results ---")
    print(f"  Original bitstream : {bitstream}")
    print(f"  Encoded bitstream  : {encoded}")
    print(f"  (length: {len(bitstream)} bits -> {len(encoded)} bits)")


def run_decoding(table: dict[str, str]) -> None:
    code_len = len(next(iter(table.values())))
    print(f"\n[Decoding Mode]  (code word size: {code_len} bits)")
    while True:
        encoded_stream = prompt_bitstream("  Enter encoded bitstream to decode: ")
        try:
            decoded = decode(encoded_stream, table)
            break
        except ValueError as exc:
            print(f"  Decoding error: {exc}")
            print("  Please try again.")

    print("\n--- Translation Table ---")
    print_table(table)
    print("\n--- Results ---")
    print(f"  Encoded bitstream  : {encoded_stream}")
    print(f"  Decoded bitstream  : {decoded}")
    print(f"  (length: {len(encoded_stream)} bits -> {len(decoded)} bits)")


def main() -> None:
    print("=== Bitstream Encoder/Decoder (Default 4B/5B) ===\n")

    table = prompt_table()

    print("\nSelect operation:")
    print("  1) Encode a bitstream")
    print("  2) Decode an encoded bitstream")
    while True:
        choice = input("Enter choice (1 or 2): ").strip()
        if choice == "1":
            run_encoding(table)
            break
        elif choice == "2":
            run_decoding(table)
            break
        else:
            print("  Invalid choice. Please enter 1 or 2.")


if __name__ == "__main__":
    main()
