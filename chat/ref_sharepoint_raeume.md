# SharePoint plan_raeume Reference

*Created: 2026-01-28*  
*List GUID: `705952ee-bc5e-476f-88ea-31d21d5d3f7d`*

---

## Column Schema

| SP Column Name | Display Name | Type | Description |
|----------------|--------------|------|-------------|
| `Title` | Title | text (required) | Location short name |
| `Feld1` | Beschreibung | text | Description |
| `Feld10` | Ort | text | City/Location |
| `Feld11` | Adresse | text (multiline) | Street address |
| `PLZ` | PLZ | text (max 10) | Postal code |
| `Anfahrt` | Anfahrt | richtext | Directions (HTML) |
| `CloudinaryCode` | CloudinaryCode | text | Image reference |
| `Koordination` | Koordination | lookup → contacts | Responsible person (LookupId) |
| `oaddress_id` | oaddress_id | number (unique) | Odoo res.partner ID |

---

## Location Data (as of 2026-01-28)

| ID | Title | Ort | PLZ | Beschreibung | Adresse | Koordination |
|----|-------|-----|-----|--------------|---------|--------------|
| 1 | Nbg: KHG | Nürnberg | 90429 | Katholische Hochschulgemeinde | Königstraße 64 | 518 |
| 2 | Leer | | | *(empty placeholder)* | | |
| 3 | Mue: H-Lingg | München | 80336 | Hermann-Lingg-Straße | Lachdach Atelier, Hermann-Lingg-Str. 2 | 114 |
| 4 | Mue: Welt-Haus | München | 80336 | Eine-Welt-Haus | Schwanthalerstr. 80 | |
| 5 | Web: Standard | online | | Online / MS Teams | | |
| 6 | Nbg: freie Szene | Nürnberg | | Nürnberg | Gibitzenhofstr. 62, Hinterhaus, 2.OG | |
| 7 | Nbg: Büro | Nürnberg | 90429 | Büro Nürnberg | Fürtherstr. 174a | |
| 8 | Nbg: Tanzerei | Nürnberg/Fürth | 90763 | Tanzerei | Kaiserstr. 177 | 491 |
| 9 | Nbg: Sonstige | Nürnberg | | Raum: Auf Anfrage | | |
| 10 | DEU: Nachfrage | | | Veranstaltung in Deutschland | | |
| 11 | BAY: Nachfrage | | | Veranstaltung in Bayern | | |
| 12 | CZB: Nachfrage | | | Veranstaltung im Bayerisch-Tschechischen | | |
| 13 | Burgstallmühle | Burgstallmühle / Voggendorf | 91572 | Burgstallmühle | Burgstallmühle 1, Voggendorf | |
| 14 | - | | | freie Ortswahl *(placeholder)* | | |
| 15 | EU | | | Europa | | |
| 16 | Mue: Stachus | München | | Praxisgemeinschaft Dachauerstr | | |
| 17 | Mue: Kineo | München | 80336 | Kineo / Dojo SEIN | Schwanthalerstraße 91 | 516 |
| 18 | Mue: Viva la Danza | München | | Viva la Danza | Verdi-Str. 83 | 503 |
| 19 | Mue: Biodanza | München | 80331 | Biodanza | Altheimer Eck 12, 2. Stock | 504 |
| 20 | Mue: HochX | München | 80331 | HochX/Auenstr | Auenstraße | |

---

## Location Categories

### Physical Venues (Nürnberg Region)
- **1** Nbg: KHG - Main venue, Königstraße 64
- **6** Nbg: freie Szene - Gibitzenhofstr. 62
- **7** Nbg: Büro - Office, Fürtherstr. 174a
- **8** Nbg: Tanzerei - Kaiserstr. 177, Fürth
- **9** Nbg: Sonstige - On request

### Physical Venues (München)
- **3** Mue: H-Lingg - Lachdach Atelier
- **4** Mue: Welt-Haus - Eine-Welt-Haus
- **16** Mue: Stachus - Praxisgemeinschaft
- **17** Mue: Kineo - Dojo SEIN
- **18** Mue: Viva la Danza
- **19** Mue: Biodanza
- **20** Mue: HochX - Auenstraße

### Special Venues
- **13** Burgstallmühle - Retreat venue near Bechhofen

### Virtual / Placeholder
- **2** Leer - Empty/blank
- **5** Web: Standard - Online/MS Teams
- **14** - (dash) - Free location choice

### Regional Placeholders (on request)
- **10** DEU: Nachfrage - Germany-wide
- **11** BAY: Nachfrage - Bavaria-wide
- **12** CZB: Nachfrage - Bavarian-Czech region
- **15** EU - Europe-wide

---

## Usage in Events

Events reference locations via `raum1LookupId` (single-value lookup field).

**Read from SP:**
```python
raum_id = sp_fields.get('raum1LookupId')  # Returns integer ID (1-20)
```

**Event → Location mapping:**
```python
# In _map_event_from_sp():
vals['sp_raum_id'] = sp_fields.get('raum1LookupId')
```

---

## Sync Strategy

**Direction:** SharePoint → Odoo (READ-ONLY)

Locations are managed in SharePoint and synced to Odoo as `res.partner` records with `is_event_location=True`.

**Mapping to Odoo res.partner:**
| SP Field | Odoo Field |
|----------|------------|
| Title | name |
| Feld1 (Beschreibung) | comment |
| Feld10 (Ort) | city |
| Feld11 (Adresse) | street |
| PLZ | zip |
| id | sp_raum_id (custom field) |

**Write-back:** Only `oaddress_id` is written back to SP after Odoo partner creation.

---

## Query Commands

```python
# In Odoo Shell (Fast):
company = env['res.company'].browse(11)

# Export all locations
data = env['crearis.agenda.sync'].export_raeume_full(company)

# Print as table
for r in data:
    print(f"{r['id']:>3} | {r['Title']:<25} | {r['Ort']:<20} | {r['PLZ']}")
```

---

*Last updated: 2026-01-28*
