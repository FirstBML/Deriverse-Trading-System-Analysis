// enhanced_analysis.ts
import { initEngine } from "./engine.js";
async function enhancedDeriverseAnalysis() {
    const { connection, programId } = initEngine();
    console.log("🔍 Enhanced Deriverse Protocol Analysis");
    console.log("=".repeat(70));
    try {
        const allAccounts = await connection.getProgramAccounts(programId, { encoding: "base64", commitment: "confirmed" }).send();
        // Analyze each account
        const analyzed = allAccounts.map(acc => {
            const data = Buffer.from(acc.account.data[0], 'base64');
            const discriminator = data.length >= 8
                ? data.slice(0, 8).toString('hex')
                : 'unknown';
            // Determine account type based on discriminator and size
            let accountType = 'Unknown';
            if (discriminator === '1f00000001000000')
                accountType = 'Trader Account';
            else if (discriminator === '1f0000000c000000')
                accountType = 'Position Account';
            else if (discriminator === '230000000c000000')
                accountType = 'Order Account';
            else if (discriminator === '2300000001000000')
                accountType = 'Trade History';
            else if (discriminator === '2000000001000000')
                accountType = 'Admin Account';
            else if (data.length === 248)
                accountType = 'Trader Account (size match)';
            else if (data.length === 376 || data.length === 408)
                accountType = 'Position Account (size match)';
            else if (data.length === 344 || data.length === 360)
                accountType = 'Order Account (size match)';
            else if (data.length === 64)
                accountType = 'Small Config Account';
            else if (data.length === 24)
                accountType = 'Fee/Utility Account';
            return {
                pubkey: acc.pubkey.toString(),
                discriminator,
                accountType,
                size: data.length,
                lamports: acc.account.lamports,
                data
            };
        });
        // Generate comprehensive report
        console.log(`📊 Total Accounts Analyzed: ${analyzed.length}`);
        console.log("=".repeat(70));
        // Group by account type
        const byType = new Map();
        analyzed.forEach(acc => {
            if (!byType.has(acc.accountType)) {
                byType.set(acc.accountType, []);
            }
            byType.get(acc.accountType).push(acc);
        });
        console.log("\n🏷️  ACCOUNT TYPE DISTRIBUTION:");
        console.log("=".repeat(70));
        const sortedTypes = Array.from(byType.entries())
            .sort((a, b) => b[1].length - a[1].length);
        sortedTypes.forEach(([type, accounts]) => {
            const avgSize = accounts.reduce((sum, acc) => sum + acc.size, 0) / accounts.length;
            const totalValue = accounts.reduce((sum, acc) => sum + acc.lamports, 0n);
            console.log(`\n${type}:`);
            console.log(`  Count: ${accounts.length} (${(accounts.length / analyzed.length * 100).toFixed(1)}%)`);
            console.log(`  Avg Size: ${avgSize.toFixed(0)} bytes`);
            console.log(`  Total Value: ${Number(totalValue) / 1e9} SOL`);
            // Show discriminators for this type
            const discriminators = new Set(accounts.map(a => a.discriminator));
            if (discriminators.size <= 5) {
                console.log(`  Discriminators: ${Array.from(discriminators).map(d => `0x${d}`).join(', ')}`);
            }
        });
        // Deep analysis of trader accounts
        const traderAccounts = analyzed.filter(a => a.accountType.includes('Trader'));
        if (traderAccounts.length > 0) {
            console.log("\n👤 DEEP TRADER ACCOUNT ANALYSIS:");
            console.log("=".repeat(70));
            console.log(`Found ${traderAccounts.length} trader accounts`);
            const sample = traderAccounts[0];
            console.log(`\nSample Account: ${sample.pubkey}`);
            console.log(`Size: ${sample.size} bytes, Value: ${Number(sample.lamports) / 1e9} SOL`);
            // Parse trader account structure
            console.log("\nAccount Structure:");
            console.log("Offset | Bytes (hex)                     | Interpretation");
            console.log("-".repeat(80));
            const offsets = [
                { offset: 0, length: 8, desc: "Discriminator" },
                { offset: 8, length: 4, desc: "Version/Nonce" },
                { offset: 12, length: 4, desc: "Flags" },
                { offset: 16, length: 32, desc: "Owner Pubkey" },
                { offset: 48, length: 32, desc: "Authority Pubkey" },
                { offset: 80, length: 8, desc: "Balance 1 (likely USDC)" },
                { offset: 88, length: 8, desc: "Balance 2" },
                { offset: 96, length: 8, desc: "Balance 3" },
                { offset: 104, length: 8, desc: "Balance 4" },
                { offset: 112, length: 8, desc: "Balance 5" },
            ];
            offsets.forEach(({ offset, length, desc }) => {
                if (offset + length <= sample.data.length) {
                    const bytes = sample.data.slice(offset, offset + length);
                    const hex = bytes.toString('hex');
                    let interpretation = '';
                    if (length === 8 && offset >= 80) {
                        // Interpret as u64 balance
                        const balance = bytes.readBigUInt64LE(0);
                        interpretation = `= ${balance} (${Number(balance) / 1e6} USDC)`;
                    }
                    else if (length === 32) {
                        // Pubkey
                        interpretation = `= ${hex.slice(0, 16)}...`;
                    }
                    else if (length === 4) {
                        // u32
                        const value = bytes.readUInt32LE(0);
                        interpretation = `= ${value}`;
                    }
                    console.log(`${offset.toString().padStart(6)} | ${hex.padEnd(30)} | ${desc} ${interpretation}`);
                }
            });
            // Calculate total balances for all traders
            let totalTraderValue = 0n;
            let totalUsdcBalance = 0n;
            traderAccounts.forEach(trader => {
                totalTraderValue += trader.lamports;
                // Sum USDC balances (assuming bytes 80-87 is USDC)
                if (trader.data.length >= 88) {
                    const usdcBalance = trader.data.readBigUInt64LE(80);
                    totalUsdcBalance += usdcBalance;
                }
            });
            console.log(`\n📈 Trader Statistics:`);
            console.log(`  Total Trader SOL: ${Number(totalTraderValue) / 1e9} SOL`);
            console.log(`  Total USDC (estimated): ${Number(totalUsdcBalance) / 1e6} USDC`);
            console.log(`  Avg SOL per trader: ${Number(totalTraderValue) / traderAccounts.length / 1e9} SOL`);
        }
        // Position account analysis
        const positionAccounts = analyzed.filter(a => a.accountType.includes('Position'));
        if (positionAccounts.length > 0) {
            console.log("\n📈 POSITION ACCOUNT ANALYSIS:");
            console.log("=".repeat(70));
            console.log(`Found ${positionAccounts.length} position accounts`);
            // Analyze position sizes
            const sizes = positionAccounts.map(p => p.size);
            const uniqueSizes = [...new Set(sizes)].sort((a, b) => a - b);
            console.log(`\nPosition Sizes: ${uniqueSizes.join(', ')} bytes`);
            // Sample position parsing
            const samplePos = positionAccounts.find(p => p.size === 408);
            if (samplePos) {
                console.log(`\nSample 408-byte Position:`);
                console.log(`Address: ${samplePos.pubkey}`);
                // Common position field interpretations
                const posData = samplePos.data;
                console.log("\nInterpreted Fields:");
                // Market ID (likely bytes 12-15)
                const marketId = posData.readUInt32LE(12);
                console.log(`  Market ID: ${marketId}`);
                // Position size (bytes 16-23 as u64)
                const positionSize = posData.readBigUInt64LE(16);
                console.log(`  Position Size: ${positionSize}`);
                // Entry price (bytes 24-31 as u64)
                const entryPrice = posData.readBigUInt64LE(24);
                console.log(`  Entry Price: ${entryPrice} (${Number(entryPrice) / 1e6} if price in USDC)`);
                // Collateral (bytes 32-39 as u64)
                const collateral = posData.readBigUInt64LE(32);
                console.log(`  Collateral: ${collateral} (${Number(collateral) / 1e6} if USDC)`);
                // Leverage calculation
                if (positionSize > 0n && collateral > 0n) {
                    const leverage = Number(positionSize * 10000n / collateral) / 100;
                    console.log(`  Estimated Leverage: ${leverage.toFixed(2)}x`);
                }
            }
        }
        // TVL and Protocol Statistics
        console.log("\n💰 PROTOCOL STATISTICS:");
        console.log("=".repeat(70));
        const totalLamports = analyzed.reduce((sum, acc) => sum + acc.lamports, 0n);
        const totalSOL = Number(totalLamports) / 1e9;
        console.log(`Total Value Locked (TVL): ${totalSOL.toFixed(2)} SOL`);
        // Categorize by value
        const highValue = analyzed.filter(a => Number(a.lamports) > 1e9); // > 1 SOL
        const mediumValue = analyzed.filter(a => Number(a.lamports) > 1e8 && Number(a.lamports) <= 1e9); // 0.1 - 1 SOL
        const lowValue = analyzed.filter(a => Number(a.lamports) <= 1e8); // < 0.1 SOL
        console.log(`\nValue Distribution:`);
        console.log(`  High Value (>1 SOL): ${highValue.length} accounts`);
        console.log(`  Medium Value (0.1-1 SOL): ${mediumValue.length} accounts`);
        console.log(`  Low Value (<0.1 SOL): ${lowValue.length} accounts`);
        // Top accounts by value
        const topByValue = [...analyzed]
            .sort((a, b) => Number(b.lamports - a.lamports))
            .slice(0, 10);
        console.log(`\n🏆 Top 10 Accounts by Value:`);
        topByValue.forEach((acc, i) => {
            const valueSOL = Number(acc.lamports) / 1e9;
            console.log(`  ${i + 1}. ${acc.pubkey.slice(0, 16)}...: ${valueSOL.toFixed(6)} SOL (${acc.accountType})`);
        });
        return {
            totalAccounts: analyzed.length,
            traderCount: traderAccounts.length,
            positionCount: positionAccounts.length,
            totalTVL: totalSOL,
            accountTypes: sortedTypes.map(([type, accounts]) => ({
                type,
                count: accounts.length,
                avgSize: accounts.reduce((sum, a) => sum + a.size, 0) / accounts.length
            }))
        };
    }
    catch (error) {
        console.error("Analysis error:", error);
        throw error;
    }
}
enhancedDeriverseAnalysis().catch(console.error);
