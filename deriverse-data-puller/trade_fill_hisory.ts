const trades = await engine.getTradeHistory({
  client: client.address,
  limit: 1000
});

const tradeRows = trades.map(t => ({
  trader: client.address.toBase58(),
  market: t.market.toBase58(),
  side: t.side,              // buy / sell or long / short
  price: t.price,
  size: t.size,
  fee: t.fee,
  tx: t.signature,
  timestamp: Number(t.timestamp) * 1000
}));

console.log(tradeRows);
