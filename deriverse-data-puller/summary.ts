// summary.ts
import { initEngine } from "./engine.js";

async function getDeriverseSummary() {
  const { connection, programId } = initEngine();
  
  console.log("🚀 Deriverse Protocol Summary");
  console.log("=".repeat(50));
  
  const accounts = await connection.getProgramAccounts(
    programId,
    { encoding: "base64" }
  ).send();
  
  // Count by discriminator
  const counts: Record<string, number> = {};
  accounts.forEach(acc => {
    const data = Buffer.from(acc.account.data[0], 'base64');
    if (data.length >= 8) {
      const disc = data.slice(0, 8).toString('hex');
      counts[disc] = (counts[disc] || 0) + 1;
    }
  });
  
  // Top 10 account types
  const top10 = Object.entries(counts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10);
  
  console.log(`\n📊 Total Accounts: ${accounts.length}`);
  console.log("\n🏆 Top 10 Account Types:");
  top10.forEach(([disc, count]) => {
    const type = disc === '1f0000000c000000' ? 'Positions' :
                 disc === '230000000c000000' ? 'Orders' :
                 disc === '2300000001000000' ? 'Trade History' :
                 disc === '2000000001000000' ? 'Trader Info' :
                 disc === '1f00000001000000' ? 'Trader Accounts' : 'Other';
    console.log(`  ${type} (0x${disc}): ${count}`);
  });
  
  // TVL
  const tvl = accounts.reduce((sum, acc) => sum + acc.account.lamports, 0n);
  console.log(`\n💰 Total Value Locked: ${Number(tvl)/1e9} SOL`);
  
  // Active traders (assuming 1:1 with trader accounts)
  const traderCount = counts['1f00000001000000'] || 0;
  console.log(`\n👥 Active Traders: ${traderCount}`);
  
  // Open positions
  const positionCount = counts['1f0000000c000000'] || 0;
  console.log(`📈 Open Positions: ${positionCount}`);
  
  // Active orders
  const orderCount = counts['230000000c000000'] || 0;
  console.log(`🛒 Active Orders: ${orderCount}`);
}

getDeriverseSummary().catch(console.error);