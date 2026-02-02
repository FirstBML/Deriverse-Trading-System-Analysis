import { readFileSync } from "fs";
import { createSignerFromKeypair } from "@solana/kit";
import { Engine } from "@deriverse/kit";
import dotenv from "dotenv";

dotenv.config();

const keypair = JSON.parse(
  readFileSync(process.env.KEYPAIR_FILENAME!, "utf-8")
);

const signer = createSignerFromKeypair(keypair);

export const engine = await Engine.connect({
  rpcEndpoint: process.env.RPC_HTTP!,
  programId: process.env.PROGRAM_ID!,
  signer,
  version: Number(process.env.VERSION),
});
