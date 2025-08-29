#!/usr/bin/env python3
"""
Project Bundle Manager - Collect and Split Project Code

Collects all relevant project files and splits them into parts under a token limit.

Usage:
    python project_bundle_manager.py --token-limit 30000

Dependencies:
    - tiktoken (optional, recommended): pip install tiktoken
"""

import argparse
import math
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Tuple


def now():
    """Get current timestamp for logging."""
    return datetime.now().isoformat(sep=' ', timespec='seconds')


def log(msg: str, log_path: str):
    """Write a timestamped message to the log file."""
    line = f"[{now()}] {msg}"
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(line + '\n')


class Tokenizer:
    """Token counter with tiktoken support and fallback."""
    
    def __init__(self, model='cl100k_base'):
        self.backend = 'fallback'
        try:
            import tiktoken
            try:
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

    def count(self, text: str) -> int:
        """Count tokens in text."""
        if self.backend == 'tiktoken' and self.encoder is not None:
            try:
                tokens = self.encoder.encode(text)
                return len(tokens)
            except Exception:
                return math.ceil(len(text) / 4)
        else:
            return math.ceil(len(text) / 4)


class ProjectBundleManager:
    """Manages collection and splitting of project code bundles."""
    
    # File extensions to include
    TEXT_EXTENSIONS = {
        '.py', '.md', '.txt', '.json', '.yaml', '.yml', '.ini', '.cfg',
        '.js', '.ts', '.html', '.css', '.java', '.c', '.cpp', '.h',
        '.rb', '.go', '.rs', '.sh', '.ps1', '.sql'
    }
    
    # Directories to exclude
    EXCLUDE_DIRS = {
        '.git', '__pycache__', 'build', 'dist', 'node_modules', 'venv',
        '.venv', 'env', 'site-packages', '.egg-info', '.parcel-cache', 'vendor'
    }
    
    # Special files to always include
    SPECIAL_FILES = {'requirements.txt', 'README.md'}
    
    def __init__(self, log_file: str = 'project_bundle_manager.log'):
        self.log_file = log_file
        self.included = 0
        self.skipped = 0
        self.errors = 0
        self.skipped_large = 0
        self.skipped_binary = 0
        self.skipped_extension = 0
        self.excluded_dirs = {}  # dir_name -> file_count
        self.ignored_extensions = {}  # extension -> count
    
    def is_text_file(self, file_path: Path) -> bool:
        """Check if a file is a text file by looking for null bytes."""
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                return b'\x00' not in chunk
        except Exception:
            return False
    
    def should_exclude_path(self, path: Path) -> bool:
        """Check if a path should be excluded based on directory names."""
        for part in path.parts:
            if part in self.EXCLUDE_DIRS:
                return True
        return False
    
    def should_include_file(self, file_path: Path) -> Tuple[bool, str]:
        """
        Determine if a file should be included in the bundle.
        Returns (should_include, reason).
        """
        # Check size (max 5MB)
        try:
            size_mb = file_path.stat().st_size / (1024 * 1024)
            if size_mb > 5:
                self.skipped_large += 1
                return False, f"large ({size_mb:.1f}MB > 5MB)"
        except Exception:
            return False, "cannot read file stats"
        
        # Check if it's in an excluded directory
        if self.should_exclude_path(file_path):
            # Track which excluded directory this file is in
            for part in file_path.parts:
                if part in self.EXCLUDE_DIRS:
                    self.excluded_dirs[part] = self.excluded_dirs.get(part, 0) + 1
                    break
            return False, "in excluded directory"
        
        # Check if it's a special file
        if file_path.name in self.SPECIAL_FILES:
            if self.is_text_file(file_path):
                return True, "special file"
            else:
                self.skipped_binary += 1
                return False, "special file but binary"
        
        # Check extension
        if file_path.suffix.lower() in self.TEXT_EXTENSIONS:
            if self.is_text_file(file_path):
                return True, "text file"
            else:
                self.skipped_binary += 1
                return False, "has text extension but is binary"
        
        self.skipped_extension += 1
        # Track ignored file extensions
        ext = file_path.suffix.lower() if file_path.suffix else '(no extension)'
        self.ignored_extensions[ext] = self.ignored_extensions.get(ext, 0) + 1
        return False, "not a recognized text file"
    
    def collect_and_split(self, token_limit: int = 30000, output_prefix: str = 'project_code_bundle_part'):
        """Collect all files and split them into parts under token limit."""
        root_dir = Path.cwd()
        tokenizer = Tokenizer()
        
        # Create timestamped output folder
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder_name = f"bundle_{timestamp}_limit{token_limit}"
        output_folder = root_dir / folder_name
        output_folder.mkdir(exist_ok=True)
        
        # Update log file path to be inside the output folder
        self.log_file = output_folder / "bundle_creation.log"
        
        print(f"Tokenizer backend: {tokenizer.backend}")
        print(f"Collecting files from: {root_dir}")
        print(f"Output folder: {output_folder}")
        
        # Clear log file
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write("")
        log("Starting project bundle collection and split", self.log_file)
        
        # Find all files
        try:
            all_files = list(root_dir.rglob('*'))
            all_files = [f for f in all_files if f.is_file()]
        except Exception as e:
            print(f"Error scanning directory: {e}")
            return
        
        # Filter files
        included_files = []
        large_files = []
        
        for file_path in all_files:
            should_include, reason = self.should_include_file(file_path)
            
            if should_include:
                included_files.append(file_path)
            else:
                self.skipped += 1
                # Track large files specifically for detailed reporting
                if "large" in reason:
                    rel_path = file_path.relative_to(root_dir)
                    size_mb = file_path.stat().st_size / (1024 * 1024)
                    large_files.append((rel_path, size_mb))
        
        # Print detailed statistics
        print(f"\n=== SCAN RESULTS ===")
        print(f"✅ Files to include: {len(included_files)}")
        print(f"❌ Files skipped: {self.skipped}")
        
        if self.excluded_dirs:
            print(f"\n📁 Excluded directories and file counts:")
            for dir_name, count in sorted(self.excluded_dirs.items()):
                print(f"   {dir_name}: {count} files")
        
        if large_files:
            print(f"\n📏 Large files (>5MB) ignored:")
            for file_path, size_mb in large_files:
                print(f"   {file_path} ({size_mb:.1f}MB)")
        
        if self.skipped_binary > 0:
            print(f"\n🔒 Binary files ignored: {self.skipped_binary}")
        
        if self.skipped_extension > 0:
            print(f"\n📄 Files with unrecognized extensions ignored: {self.skipped_extension}")
            if self.ignored_extensions:
                print("   Extensions found:")
                for ext, count in sorted(self.ignored_extensions.items(), key=lambda x: x[1], reverse=True):
                    print(f"     {ext}: {count} files")
        
        print(f"\n" + "="*50)
        
        if not included_files:
            print("No files to process.")
            return
        
        # Process files and split into parts
        current_part = 1
        current_blocks = []
        current_tokens = 0
        created = 0
        
        for file_path in sorted(included_files):
            try:
                rel_path = file_path.relative_to(root_dir)
                
                # Read file content
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Create file block
                header = f"=== File: {rel_path} ==="
                block = f"{header}\n{content}"
                block_tokens = tokenizer.count(block)
                
                # Check if we need to start a new part
                if current_blocks and (current_tokens + block_tokens) > token_limit:
                    # Write current part
                    out_name = output_folder / f"{output_prefix}{current_part}.txt"
                    self._write_part(out_name, current_blocks)
                    log(f"Wrote {out_name} (blocks={len(current_blocks)}, tokens~{current_tokens})", self.log_file)
                    created += 1
                    
                    current_part += 1
                    current_blocks = []
                    current_tokens = 0
                
                # Add block to current part
                current_blocks.append(block)
                current_tokens += block_tokens
                self.included += 1
                
                log(f"Added {rel_path} to part {current_part} (tokens: {block_tokens})", self.log_file)
                
            except Exception as e:
                self.errors += 1
                log(f"ERROR processing {rel_path}: {e}", self.log_file)
        
        # Write remaining blocks
        if current_blocks:
            out_name = output_folder / f"{output_prefix}{current_part}.txt"
            self._write_part(out_name, current_blocks)
            log(f"Wrote {out_name} (blocks={len(current_blocks)}, tokens~{current_tokens})", self.log_file)
            created += 1
        
        print(f"\nDone! Created {created} part(s) in folder: {folder_name}")
        print(f"Included: {self.included}, Skipped: {self.skipped}, Errors: {self.errors}")
        print(f"See {self.log_file} for details.")
        
        # Create summary file
        self._create_summary_file(output_folder, created, token_limit, timestamp)
    
    def _write_part(self, output_path, blocks: List[str]):
        """Write blocks to a part file with proper line endings."""
        text = '\n\n'.join(blocks)
        text = text.replace('\n', '\r\n')
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            f.write(text)
    
    def _create_summary_file(self, output_folder, parts_created, token_limit, timestamp):
        """Create a summary file with bundle creation details."""
        summary_file = output_folder / "BUNDLE_SUMMARY.txt"
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("PROJECT BUNDLE SUMMARY\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Creation Time: {timestamp}\n")
            f.write(f"Token Limit: {token_limit:,}\n")
            f.write(f"Parts Created: {parts_created}\n")
            f.write(f"Files Included: {self.included}\n")
            f.write(f"Files Skipped: {self.skipped}\n")
            f.write(f"Errors: {self.errors}\n\n")
            
            if self.excluded_dirs:
                f.write("EXCLUDED DIRECTORIES:\n")
                f.write("-" * 30 + "\n")
                for dir_name, count in sorted(self.excluded_dirs.items()):
                    f.write(f"  {dir_name}: {count} files\n")
                f.write("\n")
            
            if self.skipped_large > 0:
                f.write(f"LARGE FILES IGNORED: {self.skipped_large}\n")
                f.write("(Files larger than 5MB)\n\n")
            
            if self.skipped_binary > 0:
                f.write(f"BINARY FILES IGNORED: {self.skipped_binary}\n\n")
            
            if self.ignored_extensions:
                f.write("IGNORED FILE EXTENSIONS:\n")
                f.write("-" * 30 + "\n")
                for ext, count in sorted(self.ignored_extensions.items(), key=lambda x: x[1], reverse=True):
                    f.write(f"  {ext}: {count} files\n")
                f.write("\n")
            
            f.write("FILES INCLUDED:\n")
            f.write("-" * 30 + "\n")
            for i in range(1, parts_created + 1):
                f.write(f"  project_code_bundle_part{i}.txt\n")
            
            f.write(f"\nLog file: bundle_creation.log\n")
        
        print(f"📄 Summary saved to: {summary_file}")
        print(f"📁 All files are in: {output_folder}")


def main():
    parser = argparse.ArgumentParser(description='Project Bundle Manager - Collect and Split Project Code')
    parser.add_argument('--token-limit', '-t', type=int, default=30000, 
                       help='Token limit per part (default: 30000)')
    parser.add_argument('--out-prefix', default='project_code_bundle_part', 
                       help='Output prefix for split parts (default: project_code_bundle_part)')
    parser.add_argument('--log-file', default='project_bundle_manager.log', 
                       help='Log file (default: project_bundle_manager.log)')
    
    args = parser.parse_args()
    
    manager = ProjectBundleManager(args.log_file)
    
    try:
        manager.collect_and_split(args.token_limit, args.out_prefix)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
