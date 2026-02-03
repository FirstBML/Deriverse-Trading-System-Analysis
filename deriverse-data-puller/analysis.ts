// analysis.ts - MAIN ANALYSIS FILE
import { initEngine, ensureDir } from "./engine.js";
import fs from 'fs';

async function fetchAllAccounts() {
  const { connection, programId } = initEngine();
  
  console.log(`🔍 Fetching all Deriverse accounts...`);
  
  const accounts = await connection.getProgramAccounts(
    programId,
    {
      encoding: "base64",
      commitment: "confirmed"
    }
  ).send();
  
  console.log(`✅ Found ${accounts.length} accounts`);
  return accounts;
}

async function analyzeDeriverse() {
  try {
    const accounts = await fetchAllAccounts();
    
    console.log("\n" + "=".repeat(60));
    console.log("📊 DERIVERSE PROTOCOL ANALYSIS");
    console.log("=".repeat(60));
    
    // Basic statistics
    const totalLamports = accounts.reduce((sum, acc) => sum + acc.account.lamports, 0n);
    const totalSOL = Number(totalLamports) / 1e9;
    
    console.log(`💰 Total Value Locked (TVL): ${totalSOL.toFixed(2)} SOL`);
    console.log(`📊 Total Accounts: ${accounts.length}`);
    
    // Categorize accounts
    const traderAccounts: any[] = [];
    const positionAccounts: any[] = [];
    const orderAccounts: any[] = [];
    const tradeHistoryAccounts: any[] = [];
    
    accounts.forEach(acc => {
      const data = Buffer.from(acc.account.data[0], 'base64');
      if (data.length >= 8) {
        const discriminator = data.slice(0, 8).toString('hex');
        
        if (discriminator === '1f00000001000000') {
          traderAccounts.push(acc);
        } else if (discriminator === '1f0000000c000000') {
          positionAccounts.push(acc);
        } else if (discriminator === '230000000c000000') {
          orderAccounts.push(acc);
        } else if (discriminator === '2300000001000000') {
          tradeHistoryAccounts.push(acc);
        }
      }
    });
    
    console.log("\n🏷️  ACCOUNT CATEGORIES:");
    console.log("-".repeat(40));
    console.log(`👤 Trader Accounts: ${traderAccounts.length}`);
    console.log(`📈 Position Accounts: ${positionAccounts.length}`);
    console.log(`🛒 Order Accounts: ${orderAccounts.length}`);
    console.log(`🔄 Trade History: ${tradeHistoryAccounts.length}`);
    
    // Analyze sample trader account
    if (traderAccounts.length > 0) {
      console.log("\n💼 SAMPLE TRADER ACCOUNT:");
      console.log("-".repeat(40));
      const sample = traderAccounts[0];
      const data = Buffer.from(sample.account.data[0], 'base64');
      console.log(`Address: ${sample.pubkey.toString().slice(0, 16)}...`);
      console.log(`Balance: ${Number(sample.account.lamports) / 1e9} SOL`);
      console.log(`Data Size: ${data.length} bytes`);
      
      // Show balances (first few)
      if (data.length >= 88) {
        console.log("\nBalances (estimated as 6-decimal tokens):");
        for (let i = 80; i < Math.min(120, data.length); i += 8) {
          if (i + 8 <= data.length) {
            const balance = data.readBigUInt64LE(i);
            if (balance > 0n) {
              const tokenValue = Number(balance) / 1e6;
              console.log(`  ${tokenValue.toLocaleString()} tokens`);
            }
          }
        }
      }
    }
    
    // Analyze sample position
    if (positionAccounts.length > 0) {
      console.log("\n📈 SAMPLE POSITION ACCOUNT:");
      console.log("-".repeat(40));
      const sample = positionAccounts[0];
      const data = Buffer.from(sample.account.data[0], 'base64');
      
      if (data.length >= 40) {
        const marketId = data.readUInt32LE(12);
        const positionSize = data.readBigUInt64LE(16);
        const entryPrice = data.readBigUInt64LE(24);
        const collateral = data.readBigUInt64LE(32);
        
        console.log(`Market ID: ${marketId}`);
        console.log(`Position Size: ${positionSize} units`);
        console.log(`Entry Price: ${Number(entryPrice) / 1e6} (estimated)`);
        console.log(`Collateral: ${Number(collateral) / 1e6} (estimated)`);
        
        if (collateral > 0n) {
          const leverage = Number(positionSize * 10000n / collateral) / 100;
          console.log(`Estimated Leverage: ${leverage.toFixed(2)}x`);
        }
      }
    }
    
    // Save analysis to file
    ensureDir('./analysis_output');
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const outputFile = `./analysis_output/analysis_${timestamp}.json`;
    
    const summary = {
      timestamp: new Date().toISOString(),
      totalAccounts: accounts.length,
      totalSOL,
      traderCount: traderAccounts.length,
      positionCount: positionAccounts.length,
      orderCount: orderAccounts.length,
      tradeHistoryCount: tradeHistoryAccounts.length,
      topAccounts: accounts
        .sort((a, b) => Number(b.account.lamports - a.account.lamports))
        .slice(0, 5)
        .map(acc => ({
          address: acc.pubkey.toString(),
          sol: Number(acc.account.lamports) / 1e9
        }))
    };
    
    fs.writeFileSync(outputFile, JSON.stringify(summary, null, 2));
    console.log(`\n💾 Analysis saved to: ${outputFile}`);
    
    return summary;
    
  } catch (error) {
    console.error("❌ Analysis error:", error);
    throw error;
  }
}

// Export data to JSON
async function exportData() {
  const accounts = await fetchAllAccounts();
  ensureDir('./data_exports');
  
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const exportFile = `./data_exports/deriverse_${timestamp}.json`;
  
  const exportData = accounts.map(acc => ({
    pubkey: acc.pubkey.toString(),
    owner: acc.account.owner.toString(),
    lamports: acc.account.lamports.toString(),
    sol_value: Number(acc.account.lamports) / 1e9,
    space: Number(acc.account.space),
    executable: acc.account.executable,
    rentEpoch: Number(acc.account.rentEpoch),
    data_size: Buffer.from(acc.account.data[0], 'base64').length,
    data_preview: Buffer.from(acc.account.data[0], 'base64').slice(0, 16).toString('hex')
  }));
  
  fs.writeFileSync(exportFile, JSON.stringify(exportData, null, 2));
  console.log(`💾 Exported ${exportData.length} accounts to: ${exportFile}`);
  
  return exportFile;
}

// Incremental data fetch
async function fetchIncrementalData() {
  const cacheFile = './cache/last_fetch.json';
  ensureDir('./cache');
  
  let processedAccounts = new Set<string>();
  if (fs.existsSync(cacheFile)) {
    try {
      const cache = JSON.parse(fs.readFileSync(cacheFile, 'utf8'));
      processedAccounts = new Set(cache.processedAccounts || []);
      console.log(`📋 Previously processed: ${processedAccounts.size} accounts`);
    } catch (error) {
      console.warn('⚠️ Cache corrupted, starting fresh');
    }
  }
  
  const accounts = await fetchAllAccounts();
  const newAccounts = accounts.filter(acc => 
    !processedAccounts.has(acc.pubkey.toString())
  );
  
  console.log(`🔄 New accounts since last fetch: ${newAccounts.length}`);
  
  if (newAccounts.length > 0) {
    ensureDir('./incremental_data');
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const newFile = `./incremental_data/new_${timestamp}.json`;
    
    const newData = newAccounts.map(acc => ({
      timestamp: new Date().toISOString(),
      pubkey: acc.pubkey.toString(),
      lamports: Number(acc.account.lamports) / 1e9,
      data_size: Buffer.from(acc.account.data[0], 'base64').length
    }));
    
    fs.writeFileSync(newFile, JSON.stringify(newData, null, 2));
    console.log(`💾 New data saved: ${newFile}`);
  }
  
  // Update cache
  accounts.forEach(acc => {
    processedAccounts.add(acc.pubkey.toString());
  });
  
  fs.writeFileSync(cacheFile, JSON.stringify({
    lastFetch: new Date().toISOString(),
    totalAccounts: accounts.length,
    processedAccounts: Array.from(processedAccounts)
  }, null, 2));
  
  console.log(`📋 Cache updated: ${processedAccounts.size} total accounts`);
  
  return {
    total: accounts.length,
    new: newAccounts.length
  };
}

// Command line interface
async function main() {
  const command = process.argv[2] || 'analyze';
  
  switch (command) {
    case 'analyze':
      await analyzeDeriverse();
      break;
    
    case 'export':
      await exportData();
      break;
    
    case 'incremental':
      await fetchIncrementalData();
      break;
    
    case 'all':
      console.log('Running complete analysis pipeline...\n');
      await analyzeDeriverse();
      console.log('\n' + '='.repeat(60));
      await exportData();
      console.log('\n' + '='.repeat(60));
      await fetchIncrementalData();
      console.log('\n✅ All tasks completed!');
      break;
    
    default:
      console.log(`
Deriverse Data Puller - Usage:

Commands:
  analyze      - Analyze protocol data (default)
  export       - Export all data to JSON
  incremental  - Fetch only new data
  all          - Run all tasks

Examples:
  npm start                    # Run analysis
  npm start export            # Export data
  npm start incremental       # Incremental fetch
  npm start all               # Run everything
      `);
      break;
  }
}

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(console.error);
}

// Export functions
export {
  analyzeDeriverse,
  exportData,
  fetchIncrementalData
};