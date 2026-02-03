// open_positions.ts
import { initEngine } from "./engine.js";

async function fetchAllOpenPositions() {
  const { connection, programId } = initEngine();

  console.log(`Fetching all accounts for program: ${programId.toString()}`);

  try {
    // Use base64 encoding for large data responses
    const allAccounts = await connection.getProgramAccounts(
      programId,
      {
        encoding: "base64", // CRITICAL: Use base64 for large data
        commitment: "confirmed"
      }
    ).send();

    console.log(`Found ${allAccounts.length} total Deriverse accounts`);

    // Process and display account info
    allAccounts.slice(0, 10).forEach((acc, index) => {
      console.log(`\n=== Account ${index + 1}/${allAccounts.length} ===`);
      console.log(`Pubkey: ${acc.pubkey.toString()}`);
      console.log(`Owner: ${acc.account.owner.toString()}`);
      console.log(`Lamports: ${acc.account.lamports}`);
      console.log(`Space: ${acc.account.space} bytes`);
      console.log(`Executable: ${acc.account.executable}`);
      console.log(`Rent Epoch: ${acc.account.rentEpoch}`);
      
      // Data is now base64 encoded, convert to buffer
      const dataBuffer = Buffer.from(acc.account.data[0], 'base64');
      console.log(`Data length: ${dataBuffer.length} bytes`);
      
      // Show first bytes as hex
      if (dataBuffer.length > 0) {
        const firstBytes = dataBuffer.slice(0, Math.min(32, dataBuffer.length));
        console.log(`First bytes (hex): 0x${firstBytes.toString('hex')}`);
        
        // Try to interpret as text (might be readable)
        const asText = firstBytes.toString('utf8').replace(/[^\x20-\x7E]/g, '.');
        console.log(`As text: "${asText}"`);
      }
    });

    // Group by account type (discriminator)
    console.log("\n=== Analyzing Account Types ===");
    const accountTypes = new Map<string, number>();
    
    allAccounts.forEach(acc => {
      const dataBuffer = Buffer.from(acc.account.data[0], 'base64');
      if (dataBuffer.length >= 8) {
        const discriminator = dataBuffer.slice(0, 8).toString('hex');
        accountTypes.set(discriminator, (accountTypes.get(discriminator) || 0) + 1);
      }
    });
    
    console.log("\nAccount discriminators found:");
    accountTypes.forEach((count, discriminator) => {
      console.log(`  0x${discriminator}: ${count} accounts`);
    });

    return allAccounts;

  } catch (error) {
    console.error("Error fetching accounts:", error);
    
    // Fallback: Try with data slice to reduce size
    console.log("\nTrying alternative method with data slice...");
    try {
      const allAccounts = await connection.getProgramAccounts(
        programId,
        {
          encoding: "base64",
          dataSlice: { offset: 0, length: 100 }, // Only get first 100 bytes
          commitment: "confirmed"
        }
      ).send();
      
      console.log(`Found ${allAccounts.length} accounts (with data slice)`);
      return allAccounts;
    } catch (fallbackError) {
      console.error("Fallback also failed:", fallbackError);
      throw error;
    }
  }
}

// Fetch ALL positions
fetchAllOpenPositions().catch(console.error);