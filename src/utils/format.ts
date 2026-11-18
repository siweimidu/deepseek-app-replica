const pad = (value: number, length = 2): string => String(value).padStart(length, '0')

const toDate = (value: string | number | Date): Date | null => {
  const date = value instanceof Date ? value : new Date(value)
  return Number.isNaN(date.getTime()) ? null : date
}

export const formatDate = (
  value: string | number | Date,
  separator: '/' | '-' = '-'
): string | null => {
  const date = toDate(value)
  if (!date) {
    return null
  }
  return [pad(date.getFullYear(), 4), pad(date.getMonth() + 1), pad(date.getDate())].join(separator)
}

export const monthKey = (value: string | number | Date): string | null => {
  const date = toDate(value)
  return date ? `${date.getFullYear()}-${pad(date.getMonth() + 1)}` : null
}

/** 会话详情用的完整时间：与官方一致显示到分钟，如 2026-11-18 12:52 */
export const formatDateTime = (value: string | number | Date): string => {
  const date = toDate(value)
  if (!date) {
    return '—'
  }
  return `${formatDate(date)} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}
