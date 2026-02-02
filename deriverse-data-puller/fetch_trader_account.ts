const client = await engine.getOrCreateClient();

console.log("Client address:", client.address.toBase58());
