import { PartiallyDecodedInstruction } from '@solana/web3.js';

export function fingerprintInstruction(ix: PartiallyDecodedInstruction) {
  return ix.data.slice(0, 16); // first 8 bytes → hex fingerprint
}

