# Bitstream Encoder/Decoder

A Python command-line tool for encoding and decoding binary bitstreams using a configurable translation table. The program defaults to the standard **4B/5B** encoding scheme but accepts any custom table file that follows the expected format.

---

## Table of Contents

- [Overview](#overview)
- [What is 4B/5B Encoding?](#what-is-4b5b-encoding)
- [Files](#files)
- [Requirements](#requirements)
- [Usage](#usage)
- [Translation Table File Format](#translation-table-file-format)
- [Encoding](#encoding)
- [Decoding](#decoding)
- [Validation Rules](#validation-rules)

---

## Overview

The program operates in one of two modes chosen at runtime:

| Mode     | Input                   | Output                                              |
|----------|-------------------------|-----------------------------------------------------|
| Encoding | Raw bitstream           | Translation table, original bitstream, encoded bitstream |
| Decoding | Encoded bitstream       | Translation table, encoded bitstream, decoded bitstream  |

---

## What is 4B/5B Encoding?

4B/5B is a line encoding scheme used in networking (e.g., Fast Ethernet / FDDI) to improve clock synchronisation and DC balance on a physical link. Every group of **4 data bits** is replaced by a **5-bit code word** chosen so that no code word contains more than one leading zero or more than two trailing zeros. This guarantees enough signal transitions for receivers to stay synchronised.

The standard mapping used as the default table:

| Data (4-bit) | Code (5-bit) |
|:---:|:---:|
| 0000 | 11110 |
| 0001 | 01001 |
| 0010 | 10100 |
| 0011 | 10101 |
| 0100 | 01010 |
| 0101 | 01011 |
| 0110 | 01110 |
| 0111 | 01111 |
| 1000 | 10010 |
| 1001 | 10011 |
| 1010 | 10110 |
| 1011 | 10111 |
| 1100 | 11010 |
| 1101 | 11011 |
| 1110 | 11100 |
| 1111 | 11101 |

---

## Files

```
CSC_4501_Project/
├── bitstream_encoder_decoder.py   # Main program
├── customtable.txt                # Example custom translation table
└── README.md                      # This file
```

---

## Requirements

- Python **3.10** or later
- No third-party packages — standard library only

---

## Usage

### Option 1 — Pass the table file as a command-line argument

```bash
python3 bitstream_encoder_decoder.py <table_file>
```

Example:
```bash
python3 bitstream_encoder_decoder.py customtable.txt
```

### Option 2 — Run interactively and enter the path when prompted

```bash
python3 bitstream_encoder_decoder.py
```

The program will prompt:
```
Enter path to translation table file (or press Enter to use default 4B/5B table):
```

Press **Enter** with no input to use the built-in 4B/5B table.

---

## Translation Table File Format

Ideally, just tweak the contents of the provided customtable.txt file, adhering to the following constraints:

Custom tables are plain `.txt` files. Each non-blank, non-comment line defines one mapping:

```
<data_symbol> <code_word>
```

- Fields are separated by whitespace (spaces or tabs).
- Lines beginning with `#` are treated as comments and ignored.
- Both symbols must contain **only** the characters `0` and `1`.

**Example (`customtable.txt`):**
```
# My custom 4B/4B inversion table
0000 1111
0001 1110
0010 1101
...
1111 0000
```

### Constraints enforced on every custom table

| Rule | Details |
|------|---------|
| Binary characters only | Every symbol must consist solely of `0` and `1` |
| Consistent lengths | All data symbols must be the same length; all code words must be the same length |
| Complete coverage | All **2ⁿ** possible n-bit data symbols must be present (e.g., all 16 for a 4-bit table) |
| Unique code words | No two data symbols may share the same code word (required for unambiguous decoding) |

---

## Encoding

1. The program splits the input bitstream into consecutive chunks, each the same width as the data symbols in the table.
2. Each chunk is looked up in the table and replaced with its corresponding code word.
3. The code words are concatenated to form the encoded bitstream.

**Requirement:** the input bitstream length must be an exact multiple of the data symbol width. If not, the program prints an error and re-prompts.

**Example** (default 4B/5B table):
```
Input  : 10100011          (8 bits → two 4-bit symbols: 1010, 0011)
Encoded: 1011010101        (10 bits → 10110, 10101)
```

---

## Decoding

1. The program splits the encoded bitstream into consecutive chunks, each the same width as the code words in the table.
2. Each chunk is looked up in the **reverse** of the table (code word → data symbol).
3. The data symbols are concatenated to form the decoded bitstream.

**Requirement:** the encoded bitstream length must be an exact multiple of the code word width. If not, the program prints an error and re-prompts.

**Example** (default 4B/5B table):
```
Encoded: 1011010101        (10 bits → two 5-bit codes: 10110, 10101)
Decoded: 10100011          (8 bits → 1010, 0011)
```

---

## Validation Rules

The program validates input at every stage and re-prompts on any error:

| Stage | What is checked |
|-------|----------------|
| Table file path | File must exist and be readable |
| Table contents | Binary characters only, consistent symbol lengths, full 2ⁿ coverage, no duplicate code words |
| Bitstream input | Non-empty, binary characters only (`0` and `1`) |
| Bitstream alignment | Length must be a multiple of the symbol/code width for the chosen mode |
| Menu choice | Must be `1` (encode) or `2` (decode) |

---

