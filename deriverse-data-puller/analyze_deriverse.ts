// engine.ts - FINAL READ-ONLY VERSION
import { createSolanaRpc } from "@solana/kit";
import { address } from "@solana/kit";
import dotenv from "dotenv";

dotenv.config();

export function initEngine() {
  // Use environment variable or default to devnet
  const rpcUrl = process.env.SOLANA_RPC_URL || "https://api.devnet.solana.com";
  
  console.log(`🌐 Connecting to: ${rpcUrl}`);
  
  const connection = createSolanaRpc(rpcUrl);

  // Get program ID from environment
  const programIdEnv = process.env.DERIVERSE_PROGRAM_ID;
  if (!programIdEnv) {
    console.warn("⚠️  DERIVERSE_PROGRAM_ID not set in .env, using devnet default");
  }
  
  const programId = address(programIdEnv || "Drvrseg8AQLP8B96DBGmHRjFGviFNYTkHueY9g3k27Gu");
  
  console.log(`🎯 Deriverse Program: ${programId.toString()}`);
  
  return {
    connection,
    programId,
  };
}

// Helper for quick access
export async function getAllDeriverseAccounts() {
  const { connection, programId } = initEngine();
  
  console.log(`🔍 Fetching all Deriverse accounts...`);
  
  const startTime = Date.now();
  const accounts = await connection.getProgramAccounts(
    programId,
    {
      encoding: "base64",
      commitment: "confirmed"
    }
  ).send();
  
  const elapsed = Date.now() - startTime;
  console.log(`✅ Found ${accounts.length} accounts in ${elapsed}ms`);
  
  return accounts;
}