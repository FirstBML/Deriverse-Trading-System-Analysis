import 'dotenv/config';
import fs from 'fs';
import { Connection, PublicKey } from '@solana/web3.js';
import { fetchProgramSignatures } from './fetchSignatures.js';
import { fetchTransaction } from './fetchTransaction.js';
import { decodeLogs } from './decodeLogs.js';
import { fingerprintInstruction } from './fingerprintInstruction.js';
import { inferMarketType } from './inferMarket.js';
const connection = new Connection(process.env.SOLANA_RPC_URL || 'https://api.devnet.solana.com', 'confirmed');
const PROGRAM_ID = new PublicKey('Drvrseg8AQLP8B96DBGmHRjFGviFNYTkHueY9g3k27Gu');
export async function runIndexer() {
    console.log('🚀 Starting Deriverse Event Indexer');
    const sigs = await fetchProgramSignatures(connection, PROGRAM_ID, 50);
    const events = [];
    for (const s of sigs) {
        const tx = await fetchTransaction(connection, s.signature);
        if (!tx || !tx.meta)
            continue;
        const logs = decodeLogs(tx.meta.logMessages || null);
        const marketType = inferMarketType(logs);
        const instructions = tx.transaction.message.instructions ? tx.transaction.message.instructions.filter((ix) => 'data' in ix) : [];
        for (const ix of instructions) {
            const event = {
                signature: s.signature,
                slot: tx.slot,
                blockTime: tx.blockTime,
                eventType: logs.length > 0 ? 'TRADE' : 'UNKNOWN',
                instructionFingerprint: fingerprintInstruction(ix),
                involvedAccounts: ix.accounts.map((a) => a.toBase58()),
                rawLogs: logs,
                inferredMarketType: marketType,
                success: !tx.meta.err,
            };
            events.push(event);
        }
    }
    fs.mkdirSync('./data/events', { recursive: true });
    const file = `./data/events/deriverse_events_${Date.now()}.json`;
    fs.writeFileSync(file, JSON.stringify(events, null, 2));
    console.log(`💾 Indexed ${events.length} events → ${file}`);
}
runIndexer().catch(console.error);
