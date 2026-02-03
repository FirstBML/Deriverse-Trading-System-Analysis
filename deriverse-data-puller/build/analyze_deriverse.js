// analyze_deriverse.ts
import { initEngine } from "./engine.js";
// ACCOUNT_TYPE_MAP in analyze_deriverse.ts
const ACCOUNT_TYPE_MAP = {
    // Trader Accounts (Confirmed: 824 accounts, 248 bytes each)
    '1f00000001000000': 'Trader Account',
    // Position Accounts (Confirmed: 909 accounts, 376-408 bytes each)
    '1f0000000c000000': 'Position Account',
    // Order Accounts (909 accounts, 344-360 bytes each)
    '230000000c000000': 'Order Account',
    // Trade History (824 accounts, 64-104 bytes each)
    '2300000001000000': 'Trade History Account',
    // Market State (909 accounts, varies)
    '200000000c000000': 'Market State',
    // Trader Info/Metadata
    '2000000001000000': 'Trader Info Account',
    // Market Configuration (15 accounts, 64 bytes each)
    '0c0000000c000000': 'Market Configuration',
    // Fee Accounts (15 accounts, 24 bytes each)
    '0f0000000c000000': 'Fee Account',
    // Oracle Accounts (33 accounts, 80+ bytes each)
    '1400000006000000': 'Oracle Account',
    // Token Vaults (18 accounts, 88+ bytes each)
    '1100000005000000': 'Token Vault',
    // Large storage accounts
    '130000000a000000': 'Market Data Storage',
    '0f00000009000000': 'Historical Data Storage',
    '3200000009000000': 'Large Order Book',
    '2f0000000b000000': 'Trade History Storage',
    // Various metadata accounts
    '1f00000003000000': 'Position Metadata',
    '2000000003000000': 'Market Metadata',
    '2300000003000000': 'Order Metadata',
    '0400000003000000': 'Token Configuration',
    '0800000003000000': 'Fee Schedule',
};
// Add auto-detection for sizes
const ACCOUNT_SIZE_MAP = {
    '1f00000001000000': 248, // Trader accounts
    '1f0000000c000000': 376, // Position accounts (most common size)
    '230000000c000000': 344, // Order accounts
    '2300000001000000': 64, // Trade history (smallest)
    '0c0000000c000000': 64, // Market config
    '0f0000000c000000': 24, // Fee accounts
    '1400000006000000': 80, // Oracle accounts
};
async function analyzeDeriverseAccounts() {
    const { connection, programId } = initEngine();
    console.log(`Analyzing Deriverse program: ${programId.toString()}`);
    console.log("=".repeat(60));
    try {
        const allAccounts = await connection.getProgramAccounts(programId, {
            encoding: "base64",
            commitment: "confirmed"
        }).send();
        console.log(`Total Accounts: ${allAccounts.length}`);
        console.log("=".repeat(60));
        // Categorize accounts
        const categories = new Map();
        const traderAccounts = [];
        const positionAccounts = [];
        const orderAccounts = [];
        allAccounts.forEach((acc, index) => {
            const dataBuffer = Buffer.from(acc.account.data[0], 'base64');
            const discriminator = dataBuffer.length >= 8
                ? dataBuffer.slice(0, 8).toString('hex')
                : 'unknown';
            const accountType = ACCOUNT_TYPE_MAP[discriminator] || `Unknown (0x${discriminator})`;
            if (!categories.has(accountType)) {
                categories.set(accountType, { count: 0, examples: [] });
            }
            const category = categories.get(accountType);
            category.count++;
            if (category.examples.length < 3) {
                category.examples.push({
                    pubkey: acc.pubkey.toString(),
                    space: acc.account.space,
                    lamports: acc.account.lamports,
                });
            }
            // Collect specific types for detailed analysis
            if (discriminator === '1f00000001000000') {
                traderAccounts.push(acc);
            }
            else if (discriminator === '1f0000000c000000') {
                positionAccounts.push(acc);
            }
            else if (discriminator === '230000000c000000') {
                orderAccounts.push(acc);
            }
        });
        // Display categories
        console.log("\n📊 ACCOUNT CATEGORIES:");
        console.log("=".repeat(60));
        categories.forEach((stats, type) => {
            console.log(`\n${type}:`);
            console.log(`  Count: ${stats.count}`);
            console.log(`  Examples:`);
            stats.examples.forEach(ex => {
                const pubkeyShort = ex.pubkey.length > 20 ? ex.pubkey.slice(0, 20) + '...' : ex.pubkey;
                const solAmount = Number(ex.lamports) / 1e9;
                console.log(`    • ${pubkeyShort} (${ex.space} bytes, ${solAmount.toFixed(6)} SOL)`);
            });
        });
        // Detailed analysis of trader accounts
        console.log("\n👤 TRADER ACCOUNTS ANALYSIS:");
        console.log("=".repeat(60));
        console.log(`Found ${traderAccounts.length} trader accounts`);
        if (traderAccounts.length > 0) {
            const sampleTrader = traderAccounts[0];
            const data = Buffer.from(sampleTrader.account.data[0], 'base64');
            console.log("\nSample Trader Account Structure:");
            console.log(`Pubkey: ${sampleTrader.pubkey.toString()}`);
            console.log(`Data Size: ${data.length} bytes`);
            // Try to parse common trader account fields (these are guesses based on typical DEX structures)
            console.log("\nParsed Data (interpreted):");
            // Bytes 0-7: Discriminator (already known)
            console.log(`  Bytes 0-7: Discriminator = 0x${data.slice(0, 8).toString('hex')}`);
            // Bytes 8-15: Version/nonce?
            const version = data.readUInt32LE(8);
            console.log(`  Bytes 8-11: Version/Nonce = ${version}`);
            // Bytes 12-19: Flags?
            const flags = data.readUInt32LE(12);
            console.log(`  Bytes 12-15: Flags = ${flags.toString(2)} (binary)`);
            // Bytes 16-47: Owner pubkey (32 bytes)
            const ownerPubkey = data.slice(16, 48);
            console.log(`  Bytes 16-47: Owner Pubkey = ${Buffer.from(ownerPubkey).toString('hex').slice(0, 32)}...`);
            // Bytes 48-79: Authority pubkey (32 bytes)
            const authorityPubkey = data.slice(48, 80);
            console.log(`  Bytes 48-79: Authority Pubkey = ${Buffer.from(authorityPubkey).toString('hex').slice(0, 32)}...`);
            // Try to read balances (these would be u64 values, 8 bytes each)
            console.log("\n  Potential Balance Fields (interpreted as u64):");
            for (let i = 80; i < Math.min(160, data.length); i += 8) {
                if (i + 8 <= data.length) {
                    const balance = data.readBigUInt64LE(i);
                    if (balance > 0n) {
                        console.log(`    Bytes ${i}-${i + 7}: ${balance} (${Number(balance) / 1e6} if USDC)`);
                    }
                }
            }
        }
        // Position accounts analysis
        console.log("\n📈 POSITION ACCOUNTS ANALYSIS:");
        console.log("=".repeat(60));
        console.log(`Found ${positionAccounts.length} position accounts`);
        if (positionAccounts.length > 0) {
            const samplePosition = positionAccounts[0];
            const data = Buffer.from(samplePosition.account.data[0], 'base64');
            console.log("\nSample Position Account:");
            console.log(`Pubkey: ${samplePosition.pubkey.toString()}`);
            console.log(`Size: ${data.length} bytes`);
            console.log(`First 64 bytes: 0x${data.slice(0, 64).toString('hex')}`);
            // Common position fields
            console.log("\nCommon position fields (interpreted):");
            console.log(`  Bytes 8-11:  Trader Index? = ${data.readUInt32LE(8)}`);
            console.log(`  Bytes 12-15: Market ID? = ${data.readUInt32LE(12)}`);
            console.log(`  Bytes 16-23: Size? = ${data.readBigUInt64LE(16)}`);
            console.log(`  Bytes 24-31: Entry Price? = ${data.readBigUInt64LE(24)}`);
            console.log(`  Bytes 32-39: Collateral? = ${data.readBigUInt64LE(32)}`);
        }
        // Generate statistics
        console.log("\n📈 STATISTICS:");
        console.log("=".repeat(60));
        const totalLamports = allAccounts.reduce((sum, acc) => sum + acc.account.lamports, 0n);
        const totalSOL = Number(totalLamports) / 1e9;
        // Fix for the sum calculation
        const totalSpace = allAccounts.reduce((sum, acc) => sum + Number(acc.account.space), 0);
        const avgSize = totalSpace / allAccounts.length;
        console.log(`Total Value Locked: ${totalSOL.toFixed(2)} SOL`);
        console.log(`Average account size: ${avgSize.toFixed(0)} bytes`);
        // Find largest accounts
        const sortedBySize = [...allAccounts].sort((a, b) => Number(b.account.space) - Number(a.account.space));
        console.log("\nLargest Accounts by Size:");
        sortedBySize.slice(0, 5).forEach((acc, i) => {
            const pubkeyShort = acc.pubkey.toString().length > 20
                ? acc.pubkey.toString().slice(0, 20) + '...'
                : acc.pubkey.toString();
            console.log(`  ${i + 1}. ${pubkeyShort}: ${acc.account.space} bytes`);
        });
        // Find richest accounts
        const sortedByValue = [...allAccounts].sort((a, b) => Number(b.account.lamports - a.account.lamports));
        console.log("\nRichest Accounts by Lamports:");
        sortedByValue.slice(0, 5).forEach((acc, i) => {
            const pubkeyShort = acc.pubkey.toString().length > 20
                ? acc.pubkey.toString().slice(0, 20) + '...'
                : acc.pubkey.toString();
            const solAmount = Number(acc.account.lamports) / 1e9;
            console.log(`  ${i + 1}. ${pubkeyShort}: ${solAmount.toFixed(6)} SOL`);
        });
        return {
            totalAccounts: allAccounts.length,
            categories: Object.fromEntries(categories),
            traderAccounts: traderAccounts.length,
            positionAccounts: positionAccounts.length,
            orderAccounts: orderAccounts.length,
            totalValueSOL: totalSOL,
        };
    }
    catch (error) {
        console.error("Error analyzing accounts:", error);
        throw error;
    }
}
analyzeDeriverseAccounts().catch(console.error);
