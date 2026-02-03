// engine.ts - Try this version
import { createSolanaRpc, address } from "@solana/kit";
import { config } from "dotenv";
import * as fs from 'fs';
config(); // Instead of dotenv.config()
export function initEngine() {
    const rpcUrl = process.env.SOLANA_RPC_URL || "https://api.devnet.solana.com";
    console.log(`🌐 Connecting to: ${rpcUrl}`);
    console.log(`   Using program: Drvrseg8AQLP8B96DBGmHRjFGviFNYTkHueY9g3k27Gu`);
    try {
        const connection = createSolanaRpc(rpcUrl);
        const programIdEnv = process.env.DERIVERSE_PROGRAM_ID;
        if (!programIdEnv) {
            console.warn("⚠️  DERIVERSE_PROGRAM_ID not set in .env, using devnet default");
        }
        const programId = address(programIdEnv || "Drvrseg8AQLP8B96DBGmHRjFGviFNYTkHueY9g3k27Gu");
        console.log(`🎯 Deriverse Program ID: ${programId.toString()}`);
        return {
            connection,
            programId,
        };
    }
    catch (error) {
        console.error("❌ Failed to initialize engine:", error.message);
        throw error;
    }
}
// Helper function
export function ensureDir(dirPath) {
    if (!fs.existsSync(dirPath)) {
        fs.mkdirSync(dirPath, { recursive: true });
    }
}
