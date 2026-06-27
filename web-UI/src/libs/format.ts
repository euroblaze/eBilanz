// Wiederverwendbare de-DE Formatierungshelfer (Locale + EUR per globaler Konvention).
const LOCALE = 'de-DE'

const eurFormatter = new Intl.NumberFormat(LOCALE, {
  style: 'currency',
  currency: 'EUR',
  minimumFractionDigits: 2,
})

const dateTimeFormatter = new Intl.DateTimeFormat(LOCALE, {
  dateStyle: 'medium',
  timeStyle: 'short',
})

const dateFormatter = new Intl.DateTimeFormat(LOCALE, { dateStyle: 'medium' })

/** Betrag als Euro (z. B. 1.234,56 €). */
export function formatEur(value: number): string {
  return eurFormatter.format(value)
}

/** Prozent mit einer Nachkommastelle (z. B. 92,0 %). */
export function formatPercent(value: number): string {
  return new Intl.NumberFormat(LOCALE, {
    style: 'percent',
    minimumFractionDigits: 0,
    maximumFractionDigits: 1,
  }).format(value)
}

/** Datum + Uhrzeit (de-DE). Akzeptiert Date-Objekt (globale Konvention: Date-Objekte). */
export function formatDateTime(value: Date): string {
  return dateTimeFormatter.format(value)
}

/** Datum (de-DE). */
export function formatDate(value: Date): string {
  return dateFormatter.format(value)
}
