// fetch_deriverse_transactionsts
import 'dotenv/config';
import { Connection, PublicKey } from '@solana/web3.js';
const connection = new Connection(process.env.SOLANA_RPC_URL || 'https://api.devnet.solana.com', 'confirmed');
const DERIVERSE_PROGRAM_ID = new PublicKey('Drvrseg8AQLP8B96DBGmHRjFGviFNYTkHueY9g3k27Gu');
async function run() {
    try {
        console.log('🔍 Fetching Deriverse transactions...');
        console.log(`Program: ${DERIVERSE_PROGRAM_ID.toString()}`);
        // Get signatures for the program
        const sigs = await connection.getSignaturesForAddress(DERIVERSE_PROGRAM_ID, { limit: 10 });
        console.log(`📊 Found ${sigs.length} recent transactions`);
        for (const s of sigs) {
            console.log(`\n📄 Transaction: ${s.signature}`);
            try {
                const tx = await connection.getTransaction(s.signature, {
                    maxSupportedTransactionVersion: 0,
                });
                if (!tx?.meta) {
                    console.log('   No transaction metadata');
                    continue;
                }
                console.log(`   Slot: ${tx.slot}`);
                console.log(`   Fee: ${tx.meta.fee} lamports`);
                console.log(`   Success: ${!tx.meta.err}`);
                console.log(`   Log count: ${tx.meta.logMessages?.length ?? 0}`);
                // Extract trade info if available
                if (tx.meta.logMessages) {
                    const tradeLogs = tx.meta.logMessages.filter(log => log.toLowerCase().includes('fill') ||
                        log.toLowerCase().includes('trade') ||
                        log.toLowerCase().includes('position'));
                    if (tradeLogs.length > 0) {
                        console.log('   ⭐ Trade-related logs found:');
                        tradeLogs.forEach(log => console.log(`     - ${log.slice(0, 100)}...`));
                    }
                }
            }
            catch (txError) {
                console.log(`   Failed to fetch transaction: ${txError.message}`);
            }
        }
    }
    catch (error) {
        console.error('❌ Error:', error.message);
    }
}
run().catch(console.error);
