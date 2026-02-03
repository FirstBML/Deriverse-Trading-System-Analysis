// deriverse-data-puller/persist_data.ts
import fs from "fs";

export function persistData(
  tradeRows: any[],
  positionRows: any[]
) {
  fs.writeFileSync(
    "trades.json",
    JSON.stringify(tradeRows, null, 2)
  );

  fs.writeFileSync(
    "positions.json",
    JSON.stringify(positionRows, null, 2)
  );
}
