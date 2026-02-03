// engine.ts - SIMPLIFIED & WORKING
import { createSolanaRpc } from "@solana/kit";
import { address } from "@solana/kit";
import dotenv from "dotenv";
import fs from 'fs';
import path from 'path';

dotenv.config();

export function initEngine() {
  const rpcUrl = process.env.SOLANA_RPC_URL || "https://api.devnet.solana.com";
  
  console.log(`🌐 Connecting to: ${rpcUrl}`);
  
  const connection = createSolanaRpc(rpcUrl);

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

// Simple cache helper
export function ensureDir(dirPath: string) {
  if (!fs.existsSync(dirPath)) {
    fs.mkdirSync(dirPath, { recursive: true });
  }
}

export function getCacheDir() {
  const cacheDir = './cache';
  ensureDir(cacheDir);
  return cacheDir;
}