#!/usr/bin/env python3
"""
Script untuk memindahkan file .md ke folder docs/
Kecuali README.md yang tetap di root.
"""

import os
import shutil
from pathlib import Path

# Project root - gunakan absolute path
ROOT = Path(__file__).resolve().parents[1]

print(f"📁 Project root: {ROOT}")
print(f"📁 Script location: {Path(__file__).resolve()}")

# Folder tujuan
DOCS_DIR = ROOT / "docs"
DOCS_DIR.mkdir(exist_ok=True)
print(f"📁 Docs folder: {DOCS_DIR}")

# File yang harus tetap di root
KEEP_IN_ROOT = {"README.md"}

# Cari semua file .md di root
print("\n🔍 Mencari file .md di root...")
md_files = list(ROOT.glob("*.md"))
print(f"   Ditemukan {len(md_files)} file .md")

for f in md_files:
    print(f"   - {f.name}")

# Pindahkan file .md
moved_count = 0
skipped_count = 0

for md_file in md_files:
    if md_file.name in KEEP_IN_ROOT:
        print(f"\n✓ Skip: {md_file.name} (tetap di root)")
        skipped_count += 1
        continue
    
    # Cek apakah file ada
    if not md_file.exists():
        print(f"✗ Error: {md_file.name} tidak ditemukan")
        continue
    
    # Pindahkan ke docs/
    dest = DOCS_DIR / md_file.name
    try:
        shutil.move(str(md_file), str(dest))
        print(f"✓ Move: {md_file.name} → docs/")
        moved_count += 1
    except Exception as e:
        print(f"✗ Error memindahkan {md_file.name}: {e}")

print(f"\n{'='*50}")
print(f"✅ Selesai! {moved_count} file dipindahkan ke docs/")
print(f"ℹ️  {skipped_count} file tetap di root")
print(f"{'='*50}")

# Verifikasi
print("\n📋 Verifikasi file di docs/:")
docs_files = list(DOCS_DIR.glob("*.md"))
print(f"   Total file di docs/: {len(docs_files)}")
