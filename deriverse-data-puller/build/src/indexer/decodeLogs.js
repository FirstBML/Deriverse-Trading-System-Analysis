export function decodeLogs(logs) {
    if (!logs)
        return [];
    return logs.filter(l => l.toLowerCase().includes('order') ||
        l.toLowerCase().includes('trade') ||
        l.toLowerCase().includes('position') ||
        l.toLowerCase().includes('fill'));
}
