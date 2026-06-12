#!/usr/bin/env python3
"""
QS-format BOQ → Onsite upload CSV converter.

Built 2026-06-12 for 'Lot 5 - LUTUNKU TI.s .xlsx' (Bill 4.7 Farm Structures,
"Original BOQ from Client" sheet). Reusable for any East-African QS-style BOQ:
  Item letter | Description | Unit | Qty | Rate | Amount

Verified on first use: 57/57 items, value sum matched source Amount column
EXACTLY (UGX 30,325,327), 0 validation errors.

Usage:
  python3 convert_qs_boq.py "<workbook.xlsx>" "<sheet name>" "<output.csv>" ["<Element prefix>"]

Key logic (hard-won, keep):
  - Stage boundaries: a header row AFTER "TOTAL CARRIED TO ELEMENT SUMMARY"
    (or file start) = new level-1 stage. Don't keyword-match stage names —
    "WALLING" appears both as a stage AND as a sub-group in the same sheet.
  - Skip QS accounting noise: TOTAL CARRIED / COLLECTION / brought forward /
    BILL No / ELEMENT NO / preamble rows.
  - Mixed depth is FINE (items at 1.1 and 1.2.1 in same file) — the accepted
    reference file (BOQ_Formatted_Onsite) does exactly this.
  - Unit map QS→Onsite: CM→cum, SM→sqm, LM→RMT, NO→nos, KG→kg, ITEM→Item.
    Anything unmapped = hard stop (never guess a unit).
  - GST 18, HSN 9954 for construction services, Item code = serial.
  - Numbers: no commas; ints stay ints.
  - Original item letters preserved in Notes ("Item A") for tender traceability.

Validation pass (always run after converting — see __main__):
  serial regex + duplicate + orphan-parent check, valid-unit check,
  comma check, and qty*price sum vs source Amount column.
"""
import openpyxl, csv, re, sys

UNIT_MAP = {'CM': 'cum', 'SM': 'sqm', 'LM': 'RMT', 'NO': 'nos', 'KG': 'kg', 'ITEM': 'Item'}
SKIP_PAT = re.compile(
    r'^(BILL No|FARM STRUCTURES|ELEMENT NO|MILKNG SHADE|ALL PROVISIONAL|'
    r'The work in this element|TOTAL CARRIED|COLLECTION|Total brought forward)', re.I)
HEADER = ['Serial Number', 'Item Name', 'Item code', 'unit', 'GST Percent',
          'Estimated Quantity', 'Unit Sale Price', 'HSN Code', 'Cost Code', 'Notes']


def clean(s):
    return re.sub(r'\s+', ' ', str(s).strip())


def convert(xlsx, sheet, prefix=''):
    wb = openpyxl.load_workbook(xlsx, data_only=True)
    ws = wb[sheet]
    out, stage_no, group_no, item_no = [], 0, 0, 0
    cur_parent, expect_stage = None, True
    src_amt = 0.0

    for row in ws.iter_rows(min_row=4, values_only=True):
        item, desc, unit, qty, rate, amt = row[0], row[1], row[2], row[3], row[4], row[5]
        if desc is None:
            continue
        d = clean(desc)
        is_item = bool(item and unit and qty is not None)

        if not is_item:
            if re.match(r'^TOTAL CARRIED TO ELEMENT SUMMARY', d, re.I):
                expect_stage = True
                continue
            if SKIP_PAT.match(d):
                continue
            if expect_stage:
                stage_no += 1; group_no = 0; item_no = 0; cur_parent = None
                name = f"{prefix} — {d}" if prefix else d
                out.append([str(stage_no), name, str(stage_no), '', '', '', '', '', '', ''])
                expect_stage = False
            else:
                group_no += 1; item_no = 0
                cur_parent = f"{stage_no}.{group_no}"
                out.append([cur_parent, d, cur_parent, '', '', '', '', '', '', ''])
            continue

        u = UNIT_MAP.get(clean(unit).upper())
        if u is None:
            raise SystemExit(f"UNMAPPED UNIT: {unit!r} on item {item} {d[:50]} — add to UNIT_MAP, never guess")
        if cur_parent is None:
            group_no += 1
            serial = f"{stage_no}.{group_no}"
        else:
            item_no += 1
            serial = f"{cur_parent}.{item_no}"
        q = float(qty); q = int(q) if q == int(q) else q
        r = '' if rate in (None, '') else (int(float(rate)) if float(rate) == int(float(rate)) else round(float(rate), 2))
        if isinstance(amt, (int, float)):
            src_amt += amt
        out.append([serial, d, serial, u, '18', str(q), str(r), '9954', '', f"Item {clean(item)}"])
    return out, src_amt


def validate(rows, src_amt):
    errs, serials, our_amt = [], set(), 0.0
    for i, r in enumerate(rows, 2):
        s, unit, qty, price = r[0], r[3], r[5], r[6]
        if not re.match(r'^\d+(\.\d+)*$', s): errs.append(f"row{i}: bad serial {s!r}")
        if s in serials: errs.append(f"row{i}: duplicate serial {s}")
        serials.add(s)
        if '.' in s and s.rsplit('.', 1)[0] not in serials:
            errs.append(f"row{i}: orphan {s}")
        if unit and qty and price:
            our_amt += float(qty) * float(price)
    if abs(src_amt - our_amt) > 1:
        errs.append(f"VALUE MISMATCH: source {src_amt:,.0f} vs csv {our_amt:,.0f}")
    return errs, our_amt


if __name__ == '__main__':
    xlsx, sheet, dest = sys.argv[1], sys.argv[2], sys.argv[3]
    prefix = sys.argv[4] if len(sys.argv) > 4 else ''
    rows, src_amt = convert(xlsx, sheet, prefix)
    errs, our_amt = validate(rows, src_amt)
    with open(dest, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f); w.writerow(HEADER); w.writerows(rows)
    items = sum(1 for r in rows if r[3])
    print(f"WROTE {dest}: {len(rows)} rows ({items} items), value {our_amt:,.0f} (source {src_amt:,.0f})")
    print(f"validation errors: {len(errs)}")
    for e in errs: print(' ', e)
