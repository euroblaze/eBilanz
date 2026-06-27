"""Offizielle E-Bilanz-Taxonomie-Optionen (esteuer.de / BMF).

Kanonische Quelle fuer die API + spaeter XBRL/Validierung/Import. Identisch zu
web-UI/src/libs/taxonomie.ts. Nur amtliche Bezeichnungen.
"""

# Taxonomie-Versionen (amtliche Versionsnummern).
TAXONOMIE_VERSIONEN = ["6.9", "6.10"]

# Steuertaxonomie-Arten (amtliche Bezeichnungen).
# - Kerntaxonomie: alle Rechtsformen ohne Branchenspezifik (z. B. Simplify-ERP)
# - Ergänzungstaxonomie Verkehrsunternehmen (JAbschlVUV): Verkehrsunternehmen (z. B. Öffis)
TAXONOMIE_ARTEN = [
    "Kerntaxonomie",
    "Ergänzungstaxonomie Verkehrsunternehmen (JAbschlVUV)",
]
