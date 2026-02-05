import { Connection, PublicKey } from '@solana/web3.js';

export async function fetchProgramSignatures(
  connection: Connection,
  programId: PublicKey,
  limit = 100
) {
  return connection.getSignaturesForAddress(programId, { limit });
}
