"""Kanonische Demo-Domaenendaten (Taxonomie-Baum, GAAP-Bestandteile).

Einzige Backend-Quelle fuer Mapping/GAAP/Kontennachweise/Validierung — solange kein
echter esteuer.de-Taxonomie-Import existiert. Spiegelt die bisherigen Frontend-Mocks.
"""
from __future__ import annotations

# --- Taxonomie-Baum (Mapping-Positionen) ------------------------------------
# feldtyp: Mussfeld | Summenmussfeld | rechnerisch notwendig | Auffangposition |
#          Kontennachweis erwünscht
MAPPING_TAXONOMY = [
    {
        "id": "bilanz", "label": "Bilanz",
        "children": [
            {
                "id": "aktiva", "label": "Aktiva", "feldtyp": "Summenmussfeld",
                "children": [
                    {
                        "id": "av", "label": "Anlagevermögen", "feldtyp": "Summenmussfeld",
                        "children": [
                            {"id": "sachanlagen", "label": "Sachanlagen", "feldtyp": "Mussfeld"},
                            {"id": "immat", "label": "Immaterielle Vermögensgegenstände", "feldtyp": "Mussfeld"},
                        ],
                    },
                    {
                        "id": "uv", "label": "Umlaufvermögen", "feldtyp": "Summenmussfeld",
                        "children": [
                            {"id": "vorraete", "label": "Vorräte", "feldtyp": "Mussfeld"},
                            {"id": "ford-alul", "label": "Forderungen aus Lieferungen und Leistungen", "feldtyp": "Mussfeld"},
                            {"id": "kasse", "label": "Kassenbestand / Bank", "feldtyp": "Mussfeld"},
                        ],
                    },
                ],
            },
            {
                "id": "passiva", "label": "Passiva", "feldtyp": "Summenmussfeld",
                "children": [
                    {
                        "id": "ek", "label": "Eigenkapital", "feldtyp": "Summenmussfeld",
                        "children": [
                            {"id": "gez-kapital", "label": "Gezeichnetes Kapital", "feldtyp": "Mussfeld"},
                            {"id": "ruecklagen", "label": "Gewinnrücklagen", "feldtyp": "rechnerisch notwendig"},
                        ],
                    },
                    {
                        "id": "verb", "label": "Verbindlichkeiten", "feldtyp": "Summenmussfeld",
                        "children": [
                            {"id": "verb-alul", "label": "Verbindlichkeiten aus Lieferungen und Leistungen", "feldtyp": "Mussfeld"},
                            {"id": "sonst-verb", "label": "Sonstige Verbindlichkeiten", "feldtyp": "Auffangposition"},
                        ],
                    },
                ],
            },
        ],
    },
    {
        "id": "guv", "label": "Gewinn- und Verlustrechnung",
        "children": [
            {"id": "umsatz", "label": "Umsatzerlöse", "feldtyp": "Mussfeld"},
            {"id": "material", "label": "Materialaufwand", "feldtyp": "Mussfeld"},
            {"id": "personal", "label": "Personalaufwand", "feldtyp": "Mussfeld"},
            {"id": "sonst-aufwand", "label": "Sonstige betriebliche Aufwendungen", "feldtyp": "Auffangposition"},
            {"id": "kn-erloese", "label": "Erlöse (Kontennachweis)", "feldtyp": "Kontennachweis erwünscht"},
        ],
    },
]


def flatten_leaves(nodes: list[dict]) -> list[dict]:
    out: list[dict] = []

    def walk(ns: list[dict]) -> None:
        for n in ns:
            if n.get("children"):
                walk(n["children"])
            else:
                out.append({"id": n["id"], "label": n["label"], "feldtyp": n.get("feldtyp")})

    walk(nodes)
    return out


MAPPING_LEAVES = flatten_leaves(MAPPING_TAXONOMY)
MUSSFELD_LEAF_IDS = [leaf["id"] for leaf in MAPPING_LEAVES if leaf["feldtyp"] == "Mussfeld"]


# --- GAAP-Bestandteile (Erfassungsmasken) -----------------------------------
# Baeume mit Importwerten je Blatt; wert_final/nil kommen aus der DB-Persistenz.
#
# Beispieldaten am Profil eines OEPNV-/Busunternehmens orientiert (vgl. Lastenheft
# Oeffis Nahverkehr Hameln-Pyrmont GmbH): Busflotte, Werkstatt, Diesel, Fahrgeld-
# erloese, Ausgleichsleistungen, Investitionszuschuesse (Sonderposten).
# Summenfelder (Summenmussfeld) ergeben sich im Grid als Summe der Kinder.
# Konsistenz: Aktiva = Passiva = 11.963.000 | Anlagenspiegel-Buchwert = 10.338.000
#             GuV-Jahresueberschuss = 248.000 = Bilanz-EK-JUE = Ergebnisverwendung
#             Sonderposten 31.12. = 4.250.000 | Aufloesung 620.000 (GuV + Anlagenspiegel)
GAAP_TREES: dict[str, list[dict]] = {
    "bilanz": [
        {
            "id": "b-aktiva", "label": "Aktiva", "feldtyp": "Summenmussfeld",
            "children": [
                {
                    "id": "b-av", "label": "A. Anlagevermögen", "feldtyp": "Summenmussfeld",
                    "children": [
                        {"id": "b-immat", "label": "I. Immaterielle Vermögensgegenstände", "feldtyp": "Mussfeld", "importwert": 48000},
                        {
                            "id": "b-sach", "label": "II. Sachanlagen", "feldtyp": "Summenmussfeld",
                            "children": [
                                {"id": "b-sach-grund", "label": "Grundstücke und Bauten (Betriebshof, Werkstatthalle)", "feldtyp": "Mussfeld", "importwert": 2350000},
                                {"id": "b-sach-tech", "label": "Technische Anlagen und Werkstattausrüstung", "feldtyp": "Mussfeld", "importwert": 420000},
                                {"id": "b-sach-fahrz", "label": "Fahrzeuge / Omnibusse", "feldtyp": "Mussfeld", "importwert": 6800000},
                                {"id": "b-sach-bga", "label": "Andere Anlagen, Betriebs- und Geschäftsausstattung", "feldtyp": "Mussfeld", "importwert": 180000},
                                {"id": "b-sach-aib", "label": "Anlagen im Bau (E-Bus-Ladeinfrastruktur)", "feldtyp": "Mussfeld", "importwert": 540000},
                            ],
                        },
                        {"id": "b-finanz", "label": "III. Finanzanlagen", "feldtyp": "Mussfeld", "importwert": 25000},
                    ],
                },
                {
                    "id": "b-uv", "label": "B. Umlaufvermögen", "feldtyp": "Summenmussfeld",
                    "children": [
                        {"id": "b-vorr", "label": "Vorräte (Diesel, Ersatzteile, Betriebsstoffe)", "feldtyp": "Mussfeld", "importwert": 310000},
                        {"id": "b-ford", "label": "Forderungen aus Lieferungen und Leistungen", "feldtyp": "Mussfeld", "importwert": 295000},
                        {"id": "b-sonst-vg", "label": "Sonstige Vermögensgegenstände (SGB IX, Mineralölsteuer)", "feldtyp": "Mussfeld", "importwert": 140000},
                        {"id": "b-kasse", "label": "Kassenbestand, Guthaben bei Kreditinstituten", "feldtyp": "Mussfeld", "importwert": 820000},
                    ],
                },
                {"id": "b-rap", "label": "C. Rechnungsabgrenzungsposten", "feldtyp": "Mussfeld", "importwert": 35000},
            ],
        },
        {
            "id": "b-passiva", "label": "Passiva", "feldtyp": "Summenmussfeld",
            "children": [
                {
                    "id": "b-ek", "label": "A. Eigenkapital", "feldtyp": "Summenmussfeld",
                    "children": [
                        {"id": "b-ek-gez", "label": "Gezeichnetes Kapital", "feldtyp": "Mussfeld", "importwert": 1500000},
                        {"id": "b-ek-kr", "label": "Kapitalrücklage", "feldtyp": "Mussfeld", "importwert": 250000},
                        {"id": "b-ek-gr", "label": "Gewinnrücklagen", "feldtyp": "rechnerisch notwendig", "importwert": 900000},
                        {"id": "b-ek-jue", "label": "Jahresüberschuss", "feldtyp": "rechnerisch notwendig", "importwert": 248000},
                    ],
                },
                {"id": "b-sopo", "label": "B. Sonderposten für Investitionszuschüsse zum Anlagevermögen", "feldtyp": "Mussfeld", "importwert": 4250000},
                {
                    "id": "b-rueck", "label": "C. Rückstellungen", "feldtyp": "Summenmussfeld",
                    "children": [
                        {"id": "b-rueck-pens", "label": "Pensionsrückstellungen", "feldtyp": "Mussfeld", "importwert": 1350000},
                        {"id": "b-rueck-steu", "label": "Steuerrückstellungen", "feldtyp": "Mussfeld", "importwert": 120000},
                        {"id": "b-rueck-sonst", "label": "Sonstige Rückstellungen", "feldtyp": "Mussfeld", "importwert": 480000},
                    ],
                },
                {
                    "id": "b-verb", "label": "D. Verbindlichkeiten", "feldtyp": "Summenmussfeld",
                    "children": [
                        {"id": "b-verb-kred", "label": "Verbindlichkeiten gegenüber Kreditinstituten", "feldtyp": "Mussfeld", "importwert": 1950000},
                        {"id": "b-verb-alul", "label": "Verbindlichkeiten aus Lieferungen und Leistungen", "feldtyp": "Mussfeld", "importwert": 640000},
                        {"id": "b-verb-sonst", "label": "Sonstige Verbindlichkeiten", "feldtyp": "Auffangposition", "importwert": 255000},
                    ],
                },
                {"id": "b-rap-p", "label": "E. Rechnungsabgrenzungsposten", "feldtyp": "Mussfeld", "importwert": 20000},
            ],
        },
    ],
    "guv": [
        {
            "id": "g-jahresergebnis", "label": "Gewinn- und Verlustrechnung (Gesamtkostenverfahren)", "feldtyp": "Summenmussfeld",
            "children": [
                {
                    "id": "g-umsatz", "label": "1. Umsatzerlöse", "feldtyp": "Summenmussfeld",
                    "children": [
                        {"id": "g-umsatz-fahr", "label": "Fahrgelderlöse (Beförderungserlöse)", "feldtyp": "Mussfeld", "importwert": 7450000},
                        {"id": "g-umsatz-ausgl", "label": "Ausgleichsleistungen der öffentlichen Hand (§ 45a PBefG)", "feldtyp": "Mussfeld", "importwert": 4730000},
                        {"id": "g-umsatz-sgb", "label": "Erstattungen nach SGB IX", "feldtyp": "Mussfeld", "importwert": 380000},
                        {"id": "g-umsatz-weiter", "label": "Weiterberechnete Werkstatt- und Dienstleistungen", "feldtyp": "Auffangposition", "importwert": 220000},
                    ],
                },
                {
                    "id": "g-sbe", "label": "2. Sonstige betriebliche Erträge", "feldtyp": "Summenmussfeld",
                    "children": [
                        {"id": "g-sbe-sopo", "label": "Erträge aus der Auflösung von Sonderposten", "feldtyp": "Mussfeld", "importwert": 620000},
                        {"id": "g-sbe-uebrig", "label": "Übrige sonstige betriebliche Erträge (Mineralölsteuer-Erstattung u. a.)", "feldtyp": "Auffangposition", "importwert": 310000},
                    ],
                },
                {
                    "id": "g-material", "label": "3. Materialaufwand", "feldtyp": "Summenmussfeld",
                    "children": [
                        {"id": "g-material-kraft", "label": "Kraftstoffe und Betriebsstoffe (Diesel)", "feldtyp": "Mussfeld", "importwert": -2150000},
                        {"id": "g-material-ersatz", "label": "Ersatzteile und Fremdleistungen Werkstatt", "feldtyp": "Mussfeld", "importwert": -980000},
                        {"id": "g-material-sub", "label": "Aufwendungen für Subunternehmerverkehre", "feldtyp": "Auffangposition", "importwert": -1450000},
                    ],
                },
                {
                    "id": "g-personal", "label": "4. Personalaufwand", "feldtyp": "Summenmussfeld",
                    "children": [
                        {"id": "g-personal-loehne", "label": "Löhne und Gehälter", "feldtyp": "Mussfeld", "importwert": -5100000},
                        {"id": "g-personal-sozial", "label": "Soziale Abgaben und Altersversorgung", "feldtyp": "Mussfeld", "importwert": -1180000},
                    ],
                },
                {"id": "g-afa", "label": "5. Abschreibungen auf Sachanlagen und immaterielle Vermögensgegenstände", "feldtyp": "Mussfeld", "importwert": -1260000},
                {
                    "id": "g-sba", "label": "6. Sonstige betriebliche Aufwendungen", "feldtyp": "Summenmussfeld",
                    "children": [
                        {"id": "g-sba-vers", "label": "Versicherungen und Kfz-Steuer", "feldtyp": "Mussfeld", "importwert": -420000},
                        {"id": "g-sba-verw", "label": "Verwaltung, Miete und IT", "feldtyp": "Auffangposition", "importwert": -560000},
                    ],
                },
                {"id": "g-zins", "label": "7. Zinsen und ähnliche Aufwendungen", "feldtyp": "Mussfeld", "importwert": -210000},
                {"id": "g-steuer-ee", "label": "8. Steuern vom Einkommen und vom Ertrag", "feldtyp": "Mussfeld", "importwert": -110000},
                {"id": "g-steuer-sonst", "label": "9. Sonstige Steuern", "feldtyp": "Mussfeld", "importwert": -42000},
            ],
        },
    ],
    "ergebnisverwendung": [
        {
            "id": "ev-root", "label": "Ergebnisverwendung", "feldtyp": "Summenmussfeld",
            "children": [
                {"id": "e-jue", "label": "Jahresüberschuss", "feldtyp": "Mussfeld", "importwert": 248000},
                {"id": "e-vortrag", "label": "Gewinnvortrag aus dem Vorjahr", "feldtyp": "rechnerisch notwendig", "importwert": 60000},
                {"id": "e-einstell", "label": "Einstellung in Gewinnrücklagen", "feldtyp": "Mussfeld", "importwert": -150000},
            ],
        },
    ],
    "steuerlich": [
        {
            "id": "s-root", "label": "Steuerliche Gewinnermittlung", "feldtyp": "Summenmussfeld",
            "children": [
                {"id": "s-jue-hb", "label": "Jahresüberschuss lt. Handelsbilanz", "feldtyp": "Mussfeld", "importwert": 248000},
                {"id": "s-nabb", "label": "+ Nicht abziehbare Betriebsausgaben", "feldtyp": "Mussfeld", "importwert": 18000},
                {"id": "s-gewst", "label": "+ Nicht abziehbare Gewerbesteuer", "feldtyp": "Mussfeld", "importwert": 95000},
                {"id": "s-steuerfrei", "label": "− Steuerfreie Erträge", "feldtyp": "Mussfeld", "importwert": -12000},
                {"id": "s-afa-diff", "label": "± Abschreibungsdifferenz HB/StB", "feldtyp": "rechnerisch notwendig", "importwert": 64000},
            ],
        },
    ],
    "ueberleitung": [
        {
            "id": "u-root", "label": "Überleitungsrechnung (Handelsbilanz → Steuerbilanz, § 60 EStDV)", "feldtyp": "Summenmussfeld",
            "children": [
                {"id": "u-droh", "label": "Drohverlustrückstellungen (steuerlich nicht zulässig)", "feldtyp": "Mussfeld", "importwert": 90000},
                {"id": "u-pens", "label": "Pensionsrückstellungen (Bewertungsdifferenz § 6a EStG)", "feldtyp": "Mussfeld", "importwert": 140000},
                {"id": "u-afa", "label": "Abschreibungsdifferenz Sachanlagen", "feldtyp": "Mussfeld", "importwert": 64000},
                {"id": "u-sopo", "label": "Sonderposten / steuerliche Sonderabschreibung", "feldtyp": "Mussfeld", "importwert": -45000},
                {"id": "u-sonst", "label": "Sonstige Korrekturen", "feldtyp": "Auffangposition", "importwert": 8000},
            ],
        },
    ],
    "anlagenspiegel": [
        {
            "id": "a-av", "label": "Anlagevermögen – Entwicklung (AHK / kum. Abschreibung = Buchwert)", "feldtyp": "Summenmussfeld",
            "children": [
                {
                    "id": "a-immat", "label": "Immaterielle Vermögensgegenstände", "feldtyp": "Summenmussfeld",
                    "children": [
                        {"id": "a-immat-ahk", "label": "Anschaffungs-/Herstellungskosten", "feldtyp": "Mussfeld", "importwert": 95000},
                        {"id": "a-immat-abschr", "label": "Kumulierte Abschreibungen", "feldtyp": "Mussfeld", "importwert": -47000},
                    ],
                },
                {
                    "id": "a-grund", "label": "Grundstücke und Bauten", "feldtyp": "Summenmussfeld",
                    "children": [
                        {"id": "a-grund-ahk", "label": "Anschaffungs-/Herstellungskosten", "feldtyp": "Mussfeld", "importwert": 3800000},
                        {"id": "a-grund-abschr", "label": "Kumulierte Abschreibungen", "feldtyp": "Mussfeld", "importwert": -1450000},
                    ],
                },
                {
                    "id": "a-tech", "label": "Technische Anlagen und Werkstattausrüstung", "feldtyp": "Summenmussfeld",
                    "children": [
                        {"id": "a-tech-ahk", "label": "Anschaffungs-/Herstellungskosten", "feldtyp": "Mussfeld", "importwert": 980000},
                        {"id": "a-tech-abschr", "label": "Kumulierte Abschreibungen", "feldtyp": "Mussfeld", "importwert": -560000},
                    ],
                },
                {
                    "id": "a-fahrz", "label": "Fahrzeuge / Omnibusse", "feldtyp": "Summenmussfeld",
                    "children": [
                        {"id": "a-fahrz-ahk", "label": "Anschaffungs-/Herstellungskosten", "feldtyp": "Mussfeld", "importwert": 12500000},
                        {"id": "a-fahrz-abschr", "label": "Kumulierte Abschreibungen", "feldtyp": "Mussfeld", "importwert": -5700000},
                    ],
                },
                {
                    "id": "a-bga", "label": "Andere Anlagen, Betriebs- und Geschäftsausstattung", "feldtyp": "Summenmussfeld",
                    "children": [
                        {"id": "a-bga-ahk", "label": "Anschaffungs-/Herstellungskosten", "feldtyp": "Mussfeld", "importwert": 510000},
                        {"id": "a-bga-abschr", "label": "Kumulierte Abschreibungen", "feldtyp": "Mussfeld", "importwert": -330000},
                    ],
                },
                {
                    "id": "a-aib", "label": "Anlagen im Bau (E-Bus-Ladeinfrastruktur)", "feldtyp": "Summenmussfeld",
                    "children": [
                        {"id": "a-aib-ahk", "label": "Anschaffungs-/Herstellungskosten", "feldtyp": "Mussfeld", "importwert": 540000},
                        {"id": "a-aib-abschr", "label": "Kumulierte Abschreibungen", "feldtyp": "Mussfeld", "importwert": 0},
                    ],
                },
            ],
        },
        {
            "id": "a-sopo", "label": "Sonderposten für Investitionszuschüsse – Entwicklung", "feldtyp": "Summenmussfeld",
            "children": [
                {"id": "a-sopo-anfang", "label": "Stand 01.01.", "feldtyp": "Mussfeld", "importwert": 4870000},
                {"id": "a-sopo-zugang", "label": "Zugänge (neue Zuschüsse / Fördermittel)", "feldtyp": "Mussfeld", "importwert": 0},
                {"id": "a-sopo-aufl", "label": "Auflösung (ertragswirksam)", "feldtyp": "Mussfeld", "importwert": -620000},
            ],
        },
    ],
}

GAAP_BESTANDTEILE = list(GAAP_TREES.keys())


def gaap_leaf_ids(bestandteil: str) -> list[dict]:
    return flatten_leaves(GAAP_TREES.get(bestandteil, []))


def gaap_value_leaves(bestandteil: str) -> list[dict]:
    """Blaetter mit Importwert (fuer Seeding der erfassten Werte)."""
    out: list[dict] = []

    def walk(ns: list[dict]) -> None:
        for n in ns:
            if n.get("children"):
                walk(n["children"])
            elif "importwert" in n:
                out.append(n)

    walk(GAAP_TREES.get(bestandteil, []))
    return out
