import fs from "fs";

const output = {
  price: 24366.9,
  change: 178.5,
  percent: 0.74,
  updated: new Date().toLocaleTimeString("en-IN", {
    timeZone: "Asia/Kolkata",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit"
  }) + " IST"
};

fs.mkdirSync("data", { recursive: true });
fs.writeFileSync("data/nifty.json", JSON.stringify(output, null, 2));

console.log("✅ NIFTY data updated");
