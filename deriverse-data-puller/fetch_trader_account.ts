// ffetch_trader_account.ts
import { initEngine } from "./engine.js";

async function fetchAllAccountsWithPagination() {
  const { connection, programId } = initEngine();
  const allAccounts = [];
  let lastAccountPubkey = null;
  
  while (true) {
    const accounts = await connection.getProgramAccounts(
      programId,
      {
        filters: [],
        ...(lastAccountPubkey ? {
          before: lastAccountPubkey,
          limit: 100, // Fetch 100 at a time
        } : {})
      }
    ).send();
    
    if (accounts.length === 0) break;
    
    allAccounts.push(...accounts);
    lastAccountPubkey = accounts[accounts.length - 1].pubkey;
    
    console.log(`Fetched ${accounts.length} accounts, total: ${allAccounts.length}`);
  }
  
  return allAccounts;
}