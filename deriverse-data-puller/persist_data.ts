import { writeFileSync, existsSync, appendFileSync } from "fs";

function writeCSV(path: string, rows: any[]) {
  if (rows.length === 0) return;

  const headers = Object.keys(rows[0]).join(",");
  const values = rows.map(r => Object.values(r).join(",")).join("\n");

  if (!existsSync(path)) {
    writeFileSync(path, headers + "\n" + values + "\n");
  } else {
    appendFileSync(path, values + "\n");
  }
}

writeCSV("trades.csv", tradeRows);
writeCSV("positions.csv", positionRows);
