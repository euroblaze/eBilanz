// Offizielle E-Bilanz-Taxonomie-Optionen (esteuer.de / BMF).
// Einzige Quelle fuer die Stammdaten-Auswahl; identisch in backend/app/constants/taxonomie.py.
// Nur amtliche Bezeichnungen verwenden.

// Taxonomie-Versionen (amtliche Versionsnummern).
export const TAXONOMIE_VERSIONEN = ['6.9', '6.10'] as const

// Steuertaxonomie-Arten (amtliche Bezeichnungen).
// - Kerntaxonomie: alle Rechtsformen ohne Branchenspezifik (z. B. Simplify-ERP, Software-GmbH)
// - Ergänzungstaxonomie Verkehrsunternehmen (JAbschlVUV): Verkehrsunternehmen (z. B. Öffis)
// Weitere amtliche Ergänzungs-/Spezialtaxonomien folgen mit dem esteuer.de-Paket-Import.
export const TAXONOMIE_ARTEN = [
  'Kerntaxonomie',
  'Ergänzungstaxonomie Verkehrsunternehmen (JAbschlVUV)',
] as const

export type TaxonomieArt = (typeof TAXONOMIE_ARTEN)[number]
