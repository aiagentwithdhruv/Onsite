# Onsite Material Library Upload Format

> Quick reference for converting any material list to Onsite Material Library CSV

## Header (exact, case-sensitive)

```csv
material name,Unit,category,description,hsn code,gst
```

## Column Specs

| Col | Field | Required | Type | Rules |
|-----|-------|----------|------|-------|
| A | material name | Yes | Text | Must be **unique** — no duplicates allowed |
| B | Unit | Yes | Text | Must be from Onsite valid units list (case-sensitive) |
| C | category | No | Text | Material category (e.g., "Electrical", "Carpentry Material", "Paint Material") |
| D | description | No | Text | Detailed description / specs |
| E | hsn code | No | Text | HSN code for the material |
| F | gst | Yes | Number | GST percentage: 18, 12, 5, or 0 (no % symbol) |

## Common Categories (observed from Onsite data)

- Carpentry Material
- Glass works
- Lighting Material
- Electrical
- Paint Material
- Plumbing Material
- Civil Material
- Hardware
- HVAC Material
- Safety Equipment

## Unit Mapping (source → Onsite valid)

| Source (invalid) | Target (valid) |
|-----------------|----------------|
| Nos, Nos., No, No. | nos |
| Mtr, Mtr., M, Mtrs | meter |
| Sqft, SQFT, Sq ft | sqft |
| Kg, KG, Kgs | kg |
| LS, L.S. | lumpsum |
| Rft, RFT | RFT |
| Rmt, rmt | RMT |
| Pkt, Packet, Box, Boxes | nos |
| L, Ltr, Liters | Litre |
| Ton, MT, Tonn | tonne |
| Pcs, Pieces | pcs |
| Set | set |
| Roll | roll |
| Pair | pair |
| Bundle | Bundle |
| Bag, Bags | bags |

## Validation Rules

1. **No duplicate material names** — Onsite rejects duplicates
2. **Valid units only** — case-sensitive
3. **GST must be a number** — 18, 12, 5, or 0
4. **No commas in numbers**
5. **No special characters** that break CSV (escape quotes if needed)

## Example Output

```csv
material name,Unit,category,description,hsn code,gst
1.5sq.mm FRLS Copper Wire,meter,Electrical,1.5sq.mm FRLS PVC insulated copper wire,,18
25mm Dia. G.I Conduit,meter,Electrical,25mm Dia. G.I Conduit 1.40mm wall thickness,,18
3 pin Ceiling rose,nos,Electrical,3 pin Ceiling rose,,18
6A 1 Way Switch,nos,Electrical,6A 1 Way Switch,,18
PVC sleeves,nos,Electrical,PVC sleeves / Gutkha (40 pcs/pkt),,18
```
