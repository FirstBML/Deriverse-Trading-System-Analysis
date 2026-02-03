// compare_test.ts - Exactly like test.ts but with more logging
import { initEngine } from "./engine.js";
async function compareTest() {
    console.log("🔍 Compare test - using same code as successful test");
    try {
        const { connection, programId } = initEngine();
        // Get slot (this worked before)
        console.log("1. Getting slot...");
        const slot = await connection.getSlot().send();
        console.log(`✅ Slot: ${slot}`);
        // Get program info (this worked before)
        console.log("2. Getting program info...");
        const info = await connection.getAccountInfo(programId).send();
        console.log(`✅ Program exists: ${!!info.value}`);
        // Try the EXACT same call that worked in test.ts
        console.log("3. Getting program accounts (small slice)...");
        const accounts = await connection.getProgramAccounts(programId, {
            encoding: "base64",
            dataSlice: { offset: 0, length: 10 },
            withContext: false // Same as successful test
        }).send();
        console.log(`✅ Found ${accounts.length} accounts`);
        // Now try the full fetch (like analysis.ts does)
        console.log("4. Getting ALL program accounts...");
        const allAccounts = await connection.getProgramAccounts(programId, {
            encoding: "base64",
            commitment: "confirmed"
        }).send();
        console.log(`✅ Found ALL: ${allAccounts.length} accounts`);
    }
    catch (error) {
        console.error("❌ Compare test error:", error.message);
        console.error("Stack:", error.stack);
    }
}
compareTest();
