// trade_fill_history.ts
import { initEngine } from "./engine.js";

async function fetchAllTradeFills() {
  const { connection, programId } = initEngine();

  // Fetch ALL trade fill accounts
  const allAccounts = await connection.getProgramAccounts(
    programId
    // No filters
  ).send();

  console.log(`Total trade fill accounts: ${allAccounts.length}`);
  
  // Process ALL accounts here
  return allAccounts;
}

fetchAllTradeFills().catch(console.error);