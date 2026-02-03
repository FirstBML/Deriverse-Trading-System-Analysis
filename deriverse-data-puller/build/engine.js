// engine.ts
import { createSolanaRpc } from "@solana/kit";
import { address } from "@solana/kit";
import dotenv from "dotenv";
dotenv.config();
export function initEngine() {
    const rpcUrl = process.env.SOLANA_RPC_URL ?? "https://api.mainnet-beta.solana.com";
    const connection = createSolanaRpc(rpcUrl);
    const programId = address("Drvrseg8AQLP8B96DBGmHRjFGviFNYTkHueY9g3k27Gu");
    return {
        connection,
        programId,
    };
}
