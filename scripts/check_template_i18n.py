#!/usr/bin/env python3
"""Gate for the seeded-record dual-write: a .po msgid must equal the XML source value.

WHY THIS EXISTS
---------------
Seeded records live in `<data noupdate="1">`, so an upgrade never overwrites the live
prod row. That means a change has to land in BOTH places -- the codebase XML/.po (fresh
installs, devbox) and a direct prod DB write. The failure mode is silent: edit only one
side and the commit looks complete, the diff is real, tests pass, and nothing complains.

The .po half has its own silent failure on top: Odoo's translation importer matches on
the msgid EXACTLY. A msgid that drifts from the XML by so much as trailing whitespace
means the translation is simply never applied on a fresh install -- no error, no warning,
just an English email where German was intended. That happened here: template 40's msgid
differed from its XML by trailing spaces on blank lines, because the English body had
been hand-written in a conversion script instead of extracted from the XML.

Reading the source back settles it every time, which is what makes this checkable rather
than a matter of care. This script is that check, wired so it runs without being
remembered.

WHAT IT CHECKS
--------------
1. every `model:mail.template,<field>:<module>.<xmlid>` reference in a .po resolves to a
   real record+field in that module's XML                        -- all field forms
2. msgstr is non-empty (an empty one imports as "no translation") -- all field forms
3. msgid == the XML source value, byte-exact                      -- CDATA / plain only

WHAT IT DOES NOT CHECK, AND WHY
-------------------------------
`<field ... type="html">` fields hold raw child XML, and Odoo's loader serialises them
itself. Reproducing that serialisation byte-exact outside Odoo would be guesswork, and a
gate that guesses is worse than one that abstains. Those fields are reported as UNCHECKED
with a count -- never silently passed. Closing that gap needs a fresh-DB export compared
against the po, which is a CI job, not a pre-commit hook.

USAGE
-----
    python3 scripts/check_template_i18n.py            # whole repo
    python3 scripts/check_template_i18n.py --staged   # only modules with staged changes
Exit 0 = clean, 1 = at least one strict check failed.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
# `#: model:mail.template,body_html:crearis.mail_template_consulting_alert`
REF = re.compile(r'^#:\s*model:mail\.template,(\w+):([\w.]+?)\.(\w+)\s*$', re.M)
QUOTED = re.compile(r'"((?:[^"\\]|\\.)*)"', re.S)


def unquote(chunk: str) -> str:
    """Parse a po value, inline ("x") or multi-line ("" / "a\\n" ...)."""
    s = ''.join(QUOTED.findall(chunk))
    return s.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')


def po_entries(path: Path):
    """Yield (field, module, xmlid, msgid, msgstr) for mail.template refs."""
    for block in path.read_text(encoding='utf-8').split('\n\n'):
        m = REF.search(block)
        if not m or 'msgid' not in block:
            continue
        body = block[block.index('msgid'):]
        try:
            split = body.index('msgstr')
        except ValueError:
            continue
        yield (m.group(1), m.group(2), m.group(3),
               unquote(body[len('msgid'):split]), unquote(body[split + len('msgstr'):]))


def xml_field(module_dir: Path, xmlid: str, field: str):
    """Return (value, form). form is 'text' (comparable), 'html' (not comparable),
    'missing', or ('badxml', path) when a data file will not parse.

    ElementTree is deliberate: it resolves entity escapes outside CDATA and leaves CDATA
    content literal, which is exactly what Odoo's own XML loader does for a plain field.

    ⚠ A ParseError is a HARD FAILURE, never a skip. The first version of this script
    swallowed it, which turned a malformed data file -- `--` inside an XML comment, which
    XML forbids and which would break every fresh install -- into a misleading
    "record not found". A gate that hides the very class of silent failure it exists to
    catch is worse than no gate. Learned by shipping that bug, 2026-08-05.
    """
    for xml_path in sorted(module_dir.rglob('*.xml')):
        try:
            root = ET.parse(xml_path).getroot()
        except ET.ParseError as exc:
            return f'{xml_path.name}: {exc}', 'badxml'
        for rec in root.iter('record'):
            if rec.get('id') != xmlid or rec.get('model') != 'mail.template':
                continue
            for fld in rec.findall('field'):
                if fld.get('name') != field:
                    continue
                if fld.get('type') == 'html':
                    return None, 'html'
                return fld.text or '', 'text'
    return None, 'missing'


def staged_modules() -> set[str] | None:
    out = subprocess.run(['git', 'diff', '--cached', '--name-only'],
                         cwd=REPO, capture_output=True, text=True)
    if out.returncode != 0:
        return None
    mods = set()
    for line in out.stdout.splitlines():
        parts = Path(line).parts
        if parts:
            mods.add(parts[0])
    return mods


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--staged', action='store_true',
                    help='only check modules with staged changes (pre-commit use)')
    args = ap.parse_args()

    only = staged_modules() if args.staged else None
    if args.staged and only is not None:
        print(f'--staged: modules touched = {", ".join(sorted(only)) or "(none)"}')

    failures: list[str] = []
    unchecked: list[str] = []
    checked = 0

    for po in sorted(REPO.glob('*/i18n/*.po')):
        module = po.parts[-3]
        if only is not None and module not in only:
            continue
        for field, ref_module, xmlid, msgid, msgstr in po_entries(po):
            where = f'{po.relative_to(REPO)} :: {ref_module}.{xmlid}/{field}'
            module_dir = REPO / ref_module
            if not module_dir.is_dir():
                failures.append(f'{where}\n    module directory not found: {ref_module}')
                continue
            value, form = xml_field(module_dir, xmlid, field)

            if form == 'badxml':
                failures.append(f'{where}\n    MALFORMED XML -- {value}\n'
                                f'    => this module cannot load. Every fresh install and'
                                f' every `-u {ref_module}` fails.\n'
                                f'    (prod may look fine: noupdate="1" means the data file'
                                f' is never re-read there.)')
                continue
            if form == 'missing':
                failures.append(f'{where}\n    no such record+field in {ref_module}/**.xml'
                                f' -- renamed or removed?')
                continue
            if not msgstr.strip():
                failures.append(f'{where}\n    msgstr is empty -- imports as "no translation"')
                continue
            if form == 'html':
                unchecked.append(f'{where}  (type="html": Odoo serialises it, not comparable here)')
                continue

            checked += 1
            if msgid != value:
                n = min(len(msgid), len(value))
                at = next((i for i in range(n) if msgid[i] != value[i]), n)
                failures.append(
                    f'{where}\n'
                    f'    msgid != XML source (first difference at offset {at})\n'
                    f'    po :  {msgid[max(0, at - 40):at + 40]!r}\n'
                    f'    xml:  {value[max(0, at - 40):at + 40]!r}\n'
                    f'    => on a fresh install this translation would SILENTLY not apply.\n'
                    f'    Fix: regenerate the msgid from the XML, never by hand.')

    print(f'strict-checked: {checked}   unchecked: {len(unchecked)}   failed: {len(failures)}')
    for u in unchecked:
        print(f'  UNCHECKED  {u}')
    for f in failures:
        print(f'  FAIL       {f}')

    if failures:
        print('\nGate FAILED.')
        return 1
    print('\nGate passed.' + (' Note the UNCHECKED entries above -- they are not covered,'
                              ' not proven correct.' if unchecked else ''))
    return 0


if __name__ == '__main__':
    sys.exit(main())
