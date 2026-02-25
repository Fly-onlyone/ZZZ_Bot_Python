import { copyFileSync, existsSync, mkdirSync } from "node:fs";
import { execSync, spawnSync } from "node:child_process";
import { join } from "node:path";

const rootDir = join(import.meta.dir, "..", "..");
const distDir = join(rootDir, "product", "dist");
const binariesDir = join(rootDir, "src-tauri", "binaries");

const extension = process.platform === "win32" ? ".exe" : "";
const baseName = `zzz-backend${extension}`;
const hostTarget = execSync("rustc --print host-tuple", {
  cwd: rootDir,
  encoding: "utf8",
}).trim();
const targetName = `zzz-backend-${hostTarget}${extension}`;

mkdirSync(distDir, { recursive: true });
mkdirSync(binariesDir, { recursive: true });

const buildResult = spawnSync(
  "uv",
  [
    "run",
    "pyinstaller",
    "product/BotSidecar.spec",
    "--distpath",
    "product/dist",
    "--workpath",
    "product/build-sidecar",
    "--noconfirm",
  ],
  {
    cwd: rootDir,
    stdio: "inherit",
    shell: process.platform === "win32",
  }
);

if (buildResult.status !== 0) {
  process.exit(buildResult.status ?? 1);
}

const builtPath = join(distDir, baseName);
if (!existsSync(builtPath)) {
  throw new Error(`Missing built sidecar at ${builtPath}`);
}

const targetPath = join(binariesDir, targetName);
copyFileSync(builtPath, targetPath);

console.log(`Sidecar copied to ${targetPath}`);
