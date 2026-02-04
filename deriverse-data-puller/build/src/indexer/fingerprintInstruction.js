export function fingerprintInstruction(ix) {
    return ix.data.slice(0, 16); // first 8 bytes → hex fingerprint
}
