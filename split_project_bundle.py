#!/usr/bin/env python3
"""
Split a project bundle (created by collect_project_code.ps1) into parts
that are under a token limit, keeping entire file blocks intact.

Usage:
    python split_project_bundle.py --input project_code_bundle.txt --out-prefix project_code_bundle_part --token-limit 30000 --dry-run

Dependencies:
    - tiktoken (optional, recommended): pip install tiktoken

Behavior:
    - Detects blocks starting with a header line: === File: ... ===
    - Uses tiktoken for accurate token counts when available; otherwise falls back to chars/4.
    - Keeps blocks intact; starts a new part only between blocks. If a single block exceeds the limit
      and --allow-split-files is not set, that part may exceed the token limit (soft limit).
    - If --allow-split-files is set, large single blocks will be split by lines into multiple parts.
    - Writes UTF-8 without BOM and logs actions to a log file.
"""

import argparse
import math
import os
import re
import sys
from datetime import datetime


def now():
    return datetime.now().isoformat(sep=' ', timespec='seconds')


def log(msg, path):
    line = f"[{now()}] {msg}"
    with open(path, 'a', encoding='utf-8') as f:
        f.write(line + '\n')


# Tokenizer wrapper
class Tokenizer:
    def __init__(self, model='cl100k_base'):
        self.model = model
        self.backend = 'fallback'
        try:
            import tiktoken
            try:
                # prefer encoding_for_model when available
                enc = tiktoken.encoding_for_model(model)
            except Exception:
                try:
                    enc = tiktoken.get_encoding(model)
                except Exception:
                    enc = tiktoken.get_encoding('cl100k_base')
            self.encoder = enc
            self.backend = 'tiktoken'
        except Exception:
            self.encoder = None
            self.backend = 'fallback'

    def count(self, text: str) -> int:
        if self.backend == 'tiktoken' and self.encoder is not None:
            try:
                toks = self.encoder.encode(text)
                return len(toks)
            except Exception:
                # fallback
                return math.ceil(len(text) / 4)
        else:
            return math.ceil(len(text) / 4)


def split_blocks(content: str):
    # Normalize newlines
    content = content.replace('\r\n', '\n')
    # Find header positions using regex
    header_re = re.compile(r'(?m)^=== File: .* ===\s*$')
    matches = list(header_re.finditer(content))
    blocks = []
    if not matches:
        blocks.append(content)
        return blocks
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        block = content[start:end].rstrip('\n')
        blocks.append(block)
    return blocks


def write_part(out_path, blocks):
    # Join blocks with double newline and write CRLF
    text = '\n\n'.join(blocks)
    text = text.replace('\n', '\r\n')
    with open(out_path, 'w', encoding='utf-8', newline='') as f:
        f.write(text)


def split_large_block_by_lines(block, tokenizer, token_limit):
    # Splits a single block into smaller parts by accumulating lines until token limit reached
    lines = block.splitlines()
    parts = []
    cur = []
    cur_tokens = 0
    for line in lines:
        # preserve newline when joining later
        line_with_n = line + '\n'
        t = tokenizer.count(line_with_n)
        if cur and (cur_tokens + t) > token_limit:
            parts.append('\n'.join(cur).rstrip('\n'))
            cur = [line]
            cur_tokens = tokenizer.count(line_with_n)
        else:
            cur.append(line)
            cur_tokens += t
    if cur:
        parts.append('\n'.join(cur).rstrip('\n'))
    return parts


def main(argv):
    p = argparse.ArgumentParser()
    p.add_argument('--input', '-i', default='project_code_bundle.txt')
    p.add_argument('--out-prefix', '-o', default='project_code_bundle_part')
    p.add_argument('--token-limit', '-t', type=int, default=30000)
    p.add_argument('--model', '-m', default='cl100k_base')
    p.add_argument('--log-file', default='split_project_bundle.log')
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--allow-split-files', action='store_true')
    args = p.parse_args(argv)

    if not os.path.isfile(args.input):
        print(f"Input file not found: {args.input}")
        sys.exit(1)

    # prepare log
    if not args.dry_run:
        with open(args.log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{now()}] Starting split for {args.input}\n")

    with open(args.input, 'r', encoding='utf-8') as f:
        content = f.read()

    blocks = split_blocks(content)
    tokenizer = Tokenizer(args.model)
    if args.dry_run:
        print(f"Tokenizer backend: {tokenizer.backend}")
    total_blocks = len(blocks)
    if args.dry_run:
        print(f"Found {total_blocks} block(s) in {args.input}")

    current_part = 1
    current_blocks = []
    current_tokens = 0
    created = 0

    for idx, block in enumerate(blocks):
        tokens = tokenizer.count(block)
        lines = block.count('\n') + 1
        if args.dry_run:
            print(f"Block {idx+1}: tokens={tokens}, lines={lines}")

        # If adding block would exceed limit and current part has content, flush
        if current_blocks and (current_tokens + tokens) > args.token_limit:
            out_name = f"{args.out_prefix}{current_part}.txt"
            if args.dry_run:
                print(f"Would write part {current_part} with {len(current_blocks)} blocks, tokens~{current_tokens} -> {out_name}")
            else:
                write_part(out_name, current_blocks)
                log(f"Wrote {out_name} (blocks={len(current_blocks)}, tokens~{current_tokens})", args.log_file)
                created += 1
            current_part += 1
            current_blocks = []
            current_tokens = 0

        # If single block exceeds limit
        if tokens > args.token_limit:
            if args.allow_split_files:
                # split the block by lines into sub-blocks
                subparts = split_large_block_by_lines(block, tokenizer, args.token_limit)
                for sp in subparts:
                    stoks = tokenizer.count(sp)
                    if current_blocks and (current_tokens + stoks) > args.token_limit:
                        out_name = f"{args.out_prefix}{current_part}.txt"
                        if args.dry_run:
                            print(f"Would write part {current_part} with {len(current_blocks)} blocks, tokens~{current_tokens} -> {out_name}")
                        else:
                            write_part(out_name, current_blocks)
                            log(f"Wrote {out_name} (blocks={len(current_blocks)}, tokens~{current_tokens})", args.log_file)
                            created += 1
                        current_part += 1
                        current_blocks = []
                        current_tokens = 0
                    # add subpart as its own block
                    current_blocks.append(sp)
                    current_tokens += stoks
            else:
                # add the oversized block to current part (soft limit)
                current_blocks.append(block)
                current_tokens += tokens
        else:
            # normal add
            current_blocks.append(block)
            current_tokens += tokens

    # flush remaining
    if current_blocks:
        out_name = f"{args.out_prefix}{current_part}.txt"
        if args.dry_run:
            print(f"Would write part {current_part} with {len(current_blocks)} blocks, tokens~{current_tokens} -> {out_name}")
        else:
            write_part(out_name, current_blocks)
            log(f"Wrote {out_name} (blocks={len(current_blocks)}, tokens~{current_tokens})", args.log_file)
            created += 1

    if args.dry_run:
        print("Dry run complete. No files written.")
    else:
        print(f"Done. Created {created} files. See {args.log_file} for details.")


if __name__ == '__main__':
    main(sys.argv[1:])
