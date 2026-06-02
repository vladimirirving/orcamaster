import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function fmtBRL(val: string | null | undefined): string {
  if (!val) return '—'
  return parseFloat(val).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

export function fmtPct(val: string | null | undefined): string {
  if (!val) return '—'
  return (parseFloat(val) * 100).toFixed(2) + '%'
}
