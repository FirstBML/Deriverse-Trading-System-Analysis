const positions = await engine.getPositions({
  client: client.address,
});

const positionRows = positions.map(p => ({
  trader: client.address.toBase58(),
  market: p.market.toBase58(),
  size: p.size,
  entry_price: p.entryPrice,
  realized_pnl: p.realizedPnl,
  unrealized_pnl: p.unrealizedPnl,
  timestamp: Date.now()
}));

console.log(positionRows);
