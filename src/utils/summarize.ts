/** Extract a short label from text: first sentence, max maxLen chars. */
export function extractSummary(text: string, maxLen = 24): string {
  const first = text.split(/[。！？.!?\n]/)[0].trim()
  const s = first.length >= 8 ? first : text.trim()
  return s.length <= maxLen ? s : s.slice(0, maxLen) + '…'
}
