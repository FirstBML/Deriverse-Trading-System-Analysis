// timeout_test.ts
import { initEngine } from "./engine.js";
async function testWithTimeout() {
    console.log("⏱️ Testing with timeout...");
    try {
        const { connection, programId } = initEngine();
        // Set a timeout for the fetch
        const timeoutPromise = new Promise((_, reject) => {
            setTimeout(() => reject(new Error("Timeout after 30 seconds")), 30000);
        });
        console.log("Fetching accounts with 30s timeout...");
        const fetchPromise = connection.getProgramAccounts(programId, {
            encoding: "base64",
            commitment: "confirmed",
            dataSlice: { offset: 0, length: 10 } // Small data first
        }).send();
        // Race between fetch and timeout
        const accounts = await Promise.race([fetchPromise, timeoutPromise]);
        console.log(`✅ Found ${accounts.length} accounts`);
    }
    catch (error) {
        console.error("❌ Error:", error.message);
    }
}
testWithTimeout();
