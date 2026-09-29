#!/usr/bin/env python3
"""Check the files shipped in this source ZIP against its release manifest.

Detects accidental changes; not a cryptographic signature of the publisher.
Local runs, checkouts, caches and other newly created files are not checked.
"""
from pathlib import Path
import hashlib
import json

root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'RELEASE_FILES.json').read_text())
errors=[]
for name,expected in manifest['sha256'].items():
    p=(root/name).resolve()
    if not p.is_relative_to(root) or not p.is_file():errors.append(name+': missing/invalid');continue
    h=hashlib.sha256(p.read_bytes()).hexdigest()
    if h!=expected:errors.append(name+': modified')
if errors:raise SystemExit('\n'.join(errors))
print(f"Verified {len(manifest['sha256'])} shipped files. Local generated files ignored.")
