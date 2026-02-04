import { Connection } from '@solana/web3.js';

export async function fetchTransaction(
  connection: Connection,
  signature: string
) {
  return connection.getTransaction(signature, {
    commitment: 'confirmed',
    maxSupportedTransactionVersion: 0,
  });
}

