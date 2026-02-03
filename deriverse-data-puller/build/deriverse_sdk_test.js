// deriverse_sdk_test.ts
import { createEngine } from "@deriverse/kit";
import dotenv from "dotenv";
dotenv.config();
async function testDeriverseSDK() {
    try {
        // Initialize with official SDK
        const engine = createEngine({
            rpcUrl: process.env.SOLANA_RPC_URL || "https://api.devnet.solana.com",
            programId: process.env.DERIVERSE_PROGRAM_ID || "Drvrseg8AQLP8B96DBGmHRjFGviFNYTkHueY9g3k27Gu",
            version: 12,
        });
        console.log("✅ Deriverse SDK initialized");
        console.log(`Program: ${engine.programId.toString()}`);
        // Test connection
        const programInfo = await engine.connection.getAccountInfo(engine.programId).send();
        console.log(`Program executable: ${programInfo?.executable}`);
        // Get all accounts (same as before)
        const accounts = await engine.connection.getProgramAccounts(engine.programId, { encoding: "base64" }).send();
        console.log(`\n📊 Found ${accounts.length} accounts via @deriverse/kit`);
        // The SDK might have helper functions for specific account types
        // Check what methods are available
        console.log("\nAvailable engine methods:");
        Object.keys(engine).forEach(key => {
            if (typeof engine[key] === 'function') {
                console.log(`  - ${key}`);
            }
        });
    }
    catch (error) {
        console.error("❌ Error with @deriverse/kit:", error);
    }
}
testDeriverseSDK();
