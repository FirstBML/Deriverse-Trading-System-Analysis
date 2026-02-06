export function decodeLogs(logs: string[] | null) {
  if (!logs) return [];

  return logs.filter(l =>
    l.toLowerCase().includes('order') ||
    l.toLowerCase().includes('trade') ||
    l.toLowerCase().includes('position') ||
    l.toLowerCase().includes('fill')
  );
}
