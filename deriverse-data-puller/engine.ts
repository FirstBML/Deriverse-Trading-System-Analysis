// engine.ts - WITH CACHING
import { createSolanaRpc } from "@solana/kit";
import { address } from "@solana/kit";
import dotenv from "dotenv";
import fs from 'fs';

dotenv.config();

// Cache interface
interface CacheEntry {
  timestamp: number;
  slot: number;
  data: any;
}

class DeriverseCache {
  private cacheDir = './cache';
  private cacheFile = './cache/deriverse_cache.json';
  
  constructor() {
    if (!fs.existsSync(this.cacheDir)) {
      fs.mkdirSync(this.cacheDir, { recursive: true });
    }
  }
  
  save(key: string, slot: number, data: any) {
    const cache: CacheEntry = {
      timestamp: Date.now(),
      slot,
      data
    };
    
    const cachePath = path.join(this.cacheDir, `${key}.json`);
    fs.writeFileSync(cachePath, JSON.stringify(cache, null, 2));
  }
  
  load(key: string): CacheEntry | null {
    const cachePath = path.join(this.cacheDir, `${key}.json`);
    if (fs.existsSync(cachePath)) {
      try {
        return JSON.parse(fs.readFileSync(cachePath, 'utf8'));
      } catch (error) {
        return null;
      }
    }
    return null;
  }
  
  shouldRefresh(key: string, maxAgeMinutes: number = 5): boolean {
    const cached = this.load(key);
    if (!cached) return true;
    
    const ageMinutes = (Date.now() - cached.timestamp) / 1000 / 60;
    return ageMinutes > maxAgeMinutes;
  }
}

export const cache = new DeriverseCache();

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
    cache
  };
}

// Helper with caching
export async function getCachedProgramAccounts(maxAgeMinutes: number = 5) {
  const { connection, programId } = initEngine();
  const cacheKey = `program_accounts_${programId.toString()}`;
  
  // Check cache
  if (!cache.shouldRefresh(cacheKey, maxAgeMinutes)) {
    const cached = cache.load(cacheKey);
    if (cached) {
      console.log(`📂 Using cached data from ${new Date(cached.timestamp).toLocaleTimeString()}`);
      return cached.data;
    }
  }
  
  // Fetch fresh data
  console.log('🔄 Fetching fresh data...');
  const accounts = await connection.getProgramAccounts(
    programId,
    {
      encoding: "base64",
      commitment: "confirmed"
    }
  ).send();
  
  // Get current slot for caching
  const slot = await connection.getSlot().send();
  
  // Cache the result
  cache.save(cacheKey, slot, accounts);
  console.log(`💾 Data cached for next ${maxAgeMinutes} minutes`);
  
  return accounts;
}