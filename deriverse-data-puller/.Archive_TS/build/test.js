import { initEngine } from "./engine.js";
async function test() {
    console.log("🧪 Testing connection...");
    try {
        const { connection, programId } = initEngine();
        // Get slot
        console.log("📡 Getting slot...");
        const slot = await connection.getSlot().send();
        console.log(`✅ Slot: ${slot}`);
        // Get program info
        console.log("📡 Getting program info...");
        const info = await connection.getAccountInfo(programId).send();
        console.log(`✅ Program exists: ${!!info.value}`);
        if (info.value) {
            console.log(`   Owner: ${info.value.owner.toString()}`);
            console.log(`   Lamports: ${info.value.lamports}`);
        }
        // Get a few accounts
        console.log("📡 Getting program accounts...");
        const accounts = await connection.getProgramAccounts(programId, {
            encoding: "base64",
            dataSlice: { offset: 0, length: 10 },
            withContext: false
        }).send();
        console.log(`✅ Found ${accounts.length} accounts`);
        if (accounts.length > 0) {
            console.log(`   First account: ${accounts[0].pubkey.toString()}`);
        }
        console.log("\n🎉 All tests passed!");
    }
    catch (error) {
        console.error("❌ Error:", error.message);
        if (error.stack) {
            console.error("Stack:", error.stack);
        }
    }
}
test();
