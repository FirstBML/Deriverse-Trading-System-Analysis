// export_to_csv.ts - COMPLETE VERSION
import { initEngine } from "./engine.js";
import fs from 'fs';
import path from 'path';
import { stringify } from 'csv-stringify/sync';

// ==================== CSV EXPORT ====================
export async function exportDeriverseDataToCSV() {
  const { connection, programId } = initEngine();
  const outputDir = './analysis_output';
  
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }
  
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const csvFile = path.join(outputDir, `deriverse_data_${timestamp}.csv`);
  
  console.log(`📤 Exporting Deriverse data to CSV...`);
  
  try {
    const accounts = await connection.getProgramAccounts(
      programId,
      {
        encoding: "base64",
        commitment: "confirmed"
      }
    ).send();
    
    console.log(`📊 Processing ${accounts.length} accounts...`);
    
    // Prepare CSV data
    const csvData = accounts.map(acc => {
      const data = Buffer.from(acc.account.data[0], 'base64');
      const discriminator = data.length >= 8 
        ? data.slice(0, 8).toString('hex')
        : '';
      
      // Try to identify account type
      let accountType = 'Unknown';
      if (discriminator === '1f00000001000000') accountType = 'Trader Account';
      else if (discriminator === '1f0000000c000000') accountType = 'Position Account';
      else if (discriminator === '230000000c000000') accountType = 'Order Account';
      else if (discriminator === '2300000001000000') accountType = 'Trade History';
      
      return {
        timestamp: new Date().toISOString(),
        pubkey: acc.pubkey.toString(),
        owner: acc.account.owner.toString(),
        lamports: acc.account.lamports.toString(),
        sol_value: (Number(acc.account.lamports) / 1e9).toFixed(9),
        space: acc.account.space.toString(),
        data_size: data.length,
        executable: acc.account.executable.toString(),
        rent_epoch: acc.account.rentEpoch.toString(),
        discriminator: `0x${discriminator}`,
        account_type: accountType,
        data_preview: data.length > 0 ? data.slice(0, 16).toString('hex') : ''
      };
    });
    
    // Write to CSV
    const csvContent = stringify(csvData, { header: true });
    fs.writeFileSync(csvFile, csvContent);
    
    console.log(`✅ CSV exported to: ${csvFile}`);
    
    // Create summary
    const summaryFile = path.join(outputDir, `deriverse_summary_${timestamp}.csv`);
    createSummaryCSV(csvData, summaryFile);
    
    return {
      csvFile,
      summaryFile,
      totalAccounts: csvData.length
    };
    
  } catch (error) {
    console.error('❌ Export error:', error);
    throw error;
  }
}

// ==================== SUMMARY CREATION ====================
function createSummaryCSV(csvData: any[], outputFile: string) {
  const summary = csvData.reduce((acc, row) => {
    const type = row.account_type;
    if (!acc[type]) {
      acc[type] = {
        account_type: type,
        count: 0,
        total_sol: 0,
        total_size: 0,
        discriminators: new Set<string>()
      };
    }
    acc[type].count++;
    acc[type].total_sol += parseFloat(row.sol_value);
    acc[type].total_size += parseInt(row.data_size);
    acc[type].discriminators.add(row.discriminator);
    return acc;
  }, {} as Record<string, any>);
  
  const summaryArray = Object.values(summary).map((item: any) => ({
    account_type: item.account_type,
    account_count: item.count,
    total_sol: item.total_sol.toFixed(6),
    avg_sol: (item.total_sol / item.count).toFixed(6),
    total_data_size: item.total_size,
    avg_data_size: Math.round(item.total_size / item.count),
    discriminators: Array.from(item.discriminators).join('; ')
  }));
  
  const summaryContent = stringify(summaryArray, { header: true });
  fs.writeFileSync(outputFile, summaryContent);
  
  console.log(`📊 Summary exported to: ${outputFile}`);
}

// ==================== INCREMENTAL FETCHING ====================
interface CacheState {
  lastFetched: string;
  lastSlot: number;
  processedAccounts: Set<string>;
}

export async function fetchIncrementalData() {
  const cacheFile = './cache/deriverse_cache.json';
  const outputDir = './incremental_data';
  
  // Ensure directories exist
  if (!fs.existsSync('./cache')) fs.mkdirSync('./cache', { recursive: true });
  if (!fs.existsSync(outputDir)) fs.mkdirSync(outputDir, { recursive: true });
  
  // Load cache
  let cache: CacheState = {
    lastFetched: new Date(0).toISOString(),
    lastSlot: 0,
    processedAccounts: new Set()
  };
  
  if (fs.existsSync(cacheFile)) {
    try {
      const cached = JSON.parse(fs.readFileSync(cacheFile, 'utf8'));
      cache = {
        lastFetched: cached.lastFetched,
        lastSlot: cached.lastSlot,
        processedAccounts: new Set(cached.processedAccounts || [])
      };
    } catch (error) {
      console.warn('⚠️ Cache corrupted, starting fresh');
    }
  }
  
  const { connection, programId } = initEngine();
  
  // Get current slot
  const slot = await connection.getSlot().send();
  console.log(`📅 Current slot: ${slot}, Last fetched slot: ${cache.lastSlot}`);
  
  if (slot <= cache.lastSlot) {
    console.log('✅ No new data since last fetch');
    return { newAccounts: 0, totalAccounts: cache.processedAccounts.size };
  }
  
  // Fetch accounts
  const accounts = await connection.getProgramAccounts(
    programId,
    {
      encoding: "base64",
      commitment: "confirmed"
    }
  ).send();
  
  // Filter new accounts
  const newAccounts = accounts.filter(acc => 
    !cache.processedAccounts.has(acc.pubkey.toString())
  );
  
  console.log(`📊 New accounts since last fetch: ${newAccounts.length}`);
  
  if (newAccounts.length > 0) {
    // Save new data
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const newDataFile = path.join(outputDir, `new_accounts_${timestamp}.json`);
    
    const newData = newAccounts.map(acc => ({
      timestamp: new Date().toISOString(),
      slot,
      pubkey: acc.pubkey.toString(),
      owner: acc.account.owner.toString(),
      lamports: acc.account.lamports.toString(),
      space: acc.account.space.toString(),
      data: acc.account.data[0]
    }));
    
    fs.writeFileSync(newDataFile, JSON.stringify(newData, null, 2));
    console.log(`💾 New data saved to: ${newDataFile}`);
    
    // Update cache
    newAccounts.forEach(acc => {
      cache.processedAccounts.add(acc.pubkey.toString());
    });
  }
  
  // Update cache
  cache.lastFetched = new Date().toISOString();
  cache.lastSlot = slot;
  
  fs.writeFileSync(cacheFile, JSON.stringify({
    lastFetched: cache.lastFetched,
    lastSlot: cache.lastSlot,
    processedAccounts: Array.from(cache.processedAccounts)
  }, null, 2));
  
  return {
    newAccounts: newAccounts.length,
    totalAccounts: cache.processedAccounts.size,
    lastSlot: slot
  };
}

// ==================== SPOT & PERPETUAL DATA ====================
export async function fetchTradingData() {
  const { connection, programId } = initEngine();
  
  console.log('📈 Fetching trading data...');
  
  const accounts = await connection.getProgramAccounts(
    programId,
    {
      encoding: "base64",
      commitment: "confirmed"
    }
  ).send();
  
  // Categorize trading data
  const spotData: any[] = [];
  const perpetualData: any[] = [];
  const tradeHistory: any[] = [];
  
  accounts.forEach(acc => {
    const data = Buffer.from(acc.account.data[0], 'base64');
    const discriminator = data.length >= 8 
      ? data.slice(0, 8).toString('hex')
      : '';
    
    const accountInfo = {
      pubkey: acc.pubkey.toString(),
      discriminator,
      data_size: data.length,
      lamports: Number(acc.account.lamports) / 1e9
    };
    
    // Categorize based on discriminator patterns
    if (discriminator === '1f0000000c000000') {
      // Position accounts (could be spot or perpetual)
      const positionData = parsePositionData(data);
      if (positionData) {
        perpetualData.push({
          ...accountInfo,
          ...positionData,
          type: 'position'
        });
      }
    } else if (discriminator === '230000000c000000') {
      // Order accounts
      const orderData = parseOrderData(data);
      if (orderData) {
        spotData.push({
          ...accountInfo,
          ...orderData,
          type: 'order'
        });
      }
    } else if (discriminator === '2300000001000000') {
      // Trade history
      tradeHistory.push({
        ...accountInfo,
        raw_data: data.slice(0, 32).toString('hex'),
        type: 'trade_history'
      });
    }
  });
  
  // Save to files
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const outputDir = './trading_data';
  
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }
  
  if (spotData.length > 0) {
    const spotFile = path.join(outputDir, `spot_data_${timestamp}.json`);
    fs.writeFileSync(spotFile, JSON.stringify(spotData, null, 2));
    console.log(`💾 Spot data: ${spotData.length} accounts -> ${spotFile}`);
  }
  
  if (perpetualData.length > 0) {
    const perpetualFile = path.join(outputDir, `perpetual_data_${timestamp}.json`);
    fs.writeFileSync(perpetualFile, JSON.stringify(perpetualData, null, 2));
    console.log(`💾 Perpetual data: ${perpetualData.length} accounts -> ${perpetualFile}`);
  }
  
  if (tradeHistory.length > 0) {
    const historyFile = path.join(outputDir, `trade_history_${timestamp}.json`);
    fs.writeFileSync(historyFile, JSON.stringify(tradeHistory, null, 2));
    console.log(`💾 Trade history: ${tradeHistory.length} accounts -> ${historyFile}`);
  }
  
  return {
    spot: spotData.length,
    perpetual: perpetualData.length,
    tradeHistory: tradeHistory.length
  };
}

// ==================== DATA PARSING HELPERS ====================
function parsePositionData(data: Buffer) {
  try {
    if (data.length < 40) return null;
    
    return {
      market_id: data.readUInt32LE(12),
      position_size: data.readBigUInt64LE(16).toString(),
      entry_price: data.readBigUInt64LE(24).toString(),
      collateral: data.readBigUInt64LE(32).toString(),
      // Additional fields based on position structure
      flags: data.readUInt32LE(8),
      raw_preview: data.slice(0, 48).toString('hex')
    };
  } catch (error) {
    console.warn('⚠️ Failed to parse position data');
    return null;
  }
}

function parseOrderData(data: Buffer) {
  try {
    if (data.length < 32) return null;
    
    return {
      // Assuming order structure based on typical DEX
      price: data.readBigUInt64LE(16).toString(),
      quantity: data.readBigUInt64LE(24).toString(),
      order_type: data.readUInt8(32), // 0 = bid, 1 = ask, etc.
      flags: data.readUInt32LE(12),
      raw_preview: data.slice(0, 40).toString('hex')
    };
  } catch (error) {
    console.warn('⚠️ Failed to parse order data');
    return null;
  }
}

// ==================== TRADE FILL HISTORY ====================
export async function fetchTradeFillHistory(startTime?: Date) {
  const { connection, programId } = initEngine();
  const outputDir = './trade_fills';
  
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }
  
  console.log('🔄 Fetching trade fill history...');
  
  // Get all accounts with trade history discriminator
  const accounts = await connection.getProgramAccounts(
    programId,
    {
      encoding: "base64",
      commitment: "confirmed",
      filters: [
        {
          memcmp: {
            offset: 0,
            bytes: "2300000001000000", // Trade history discriminator
            encoding: "base58"
          }
        }
      ]
    }
  ).send();
  
  console.log(`📊 Found ${accounts.length} trade history accounts`);
  
  // Parse trade fills
  const tradeFills: any[] = [];
  
  accounts.forEach(acc => {
    const data = Buffer.from(acc.account.data[0], 'base64');
    
    // Try to parse as trade fill (this is speculative based on typical structure)
    if (data.length >= 64) {
      const tradeFill = {
        pubkey: acc.pubkey.toString(),
        timestamp: new Date().toISOString(), // Would need actual timestamp from data
        // Parse hypothetical trade fill structure
        trader: data.slice(16, 48).toString('hex'),
        market_id: data.readUInt32LE(8),
        side: data.readUInt8(12), // 0 = buy, 1 = sell
        price: data.readBigUInt64LE(48).toString(),
        size: data.readBigUInt64LE(56).toString(),
        fee: data.readBigUInt64LE(64).toString(),
        raw_data: data.slice(0, 80).toString('hex')
      };
      
      tradeFills.push(tradeFill);
    }
  });
  
  // Save to file
  if (tradeFills.length > 0) {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const outputFile = path.join(outputDir, `trade_fills_${timestamp}.json`);
    fs.writeFileSync(outputFile, JSON.stringify(tradeFills, null, 2));
    console.log(`💾 Trade fills saved: ${outputFile} (${tradeFills.length} trades)`);
  }
  
  return {
    totalTradeFills: tradeFills.length,
    accountsProcessed: accounts.length
  };
}

// ==================== MAIN EXPORT ====================
if (import.meta.url === `file://${process.argv[1]}`) {
  // Command line interface
  const command = process.argv[2];
  
  switch (command) {
    case 'export-csv':
      exportDeriverseDataToCSV();
      break;
    
    case 'incremental':
      fetchIncrementalData();
      break;
    
    case 'trading-data':
      fetchTradingData();
      break;
    
    case 'trade-fills':
      fetchTradeFillHistory();
      break;
    
    case 'all':
      Promise.all([
        exportDeriverseDataToCSV(),
        fetchIncrementalData(),
        fetchTradingData(),
        fetchTradeFillHistory()
      ]).then(results => {
        console.log('✅ All tasks completed');
      });
      break;
    
    default:
      console.log(`
Usage: node export_to_csv.js <command>

Commands:
  export-csv     - Export all data to CSV
  incremental    - Fetch only new data since last run
  trading-data   - Extract spot/perpetual trading data
  trade-fills    - Fetch trade fill history
  all            - Run all tasks
  
Example: node export_to_csv.js incremental
      `);
      break;
  }
}

// Export all functions
export {
  exportDeriverseDataToCSV,
  fetchIncrementalData,
  fetchTradingData,
  fetchTradeFillHistory
};