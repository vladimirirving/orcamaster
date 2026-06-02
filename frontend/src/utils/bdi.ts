export function calcBdiComposto(
  ac: number, sg: number, r: number, df: number, lucro: number,
  iss: number, pis: number, cofins: number
): number {
  const denominador = 1 - iss - pis - cofins
  if (denominador <= 0) throw new Error('ISS + PIS + COFINS deve ser menor que 100%')
  return ((1 + ac + sg + r + df + lucro) / denominador) - 1
}
