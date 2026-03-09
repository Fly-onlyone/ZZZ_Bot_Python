import { copyFileSync, existsSync, mkdirSync, statSync } from "node:fs";
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

function ensureDirectory(path: string) {
  if (existsSync(path)) {
    if (!statSync(path).isDirectory()) {
      throw new Error(
        `Expected directory at ${path}, but found a file instead`
      );
    }
    return;
  }

  mkdirSync(path, { recursive: true });
}

ensureDirectory(distDir);
ensureDirectory(binariesDir);

const buildResult = spawnSync(
  "uv",
  [
    "run",
    "--group",
    "dev",
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
