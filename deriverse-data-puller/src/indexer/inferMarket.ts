export function inferMarketType(logs: string[]) {
  const joined = logs.join(' ').toLowerCase();

  if (joined.includes('leverage') || joined.includes('liquidation')) {
    return 'PERP';
  }

  if (joined.includes('position')) {
    return 'DERIVATIVE';
  }

  if (joined.includes('swap') || joined.includes('spot')) {
    return 'SPOT';
  }

  return 'UNKNOWN';
}
