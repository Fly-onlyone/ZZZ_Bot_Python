import { randomUUID } from "node:crypto";
import { join } from "node:path";

type ManagedProc = {
  name: string;
  proc: Bun.Subprocess;
};

const rootDir = join(import.meta.dir, "..", "..");
const frontendDir = join(rootDir, "frontend");
const managed: ManagedProc[] = [];

let shuttingDown = false;
let launchedTauri = false;

const devBackendPort = Number(process.env.ZZZ_DEV_BACKEND_PORT || "8001");
if (!Number.isInteger(devBackendPort) || devBackendPort <= 0) {
  throw new Error(
    `Invalid ZZZ_DEV_BACKEND_PORT value: ${process.env.ZZZ_DEV_BACKEND_PORT}`
  );
}
const devBackendUrl = `http://127.0.0.1:${devBackendPort}`;
const desktopToken = Bun.env.ZZZ_DESKTOP_TOKEN || randomUUID();

function spawnProcess(
  name: string,
  cmd: string[],
  cwd: string,
  extraEnv?: Record<string, string>
) {
  const proc = Bun.spawn(cmd, {
    cwd,
    env: {
      ...Bun.env,
      ...(extraEnv ?? {}),
    },
    stdin: "inherit",
    stdout: "inherit",
    stderr: "inherit",
  });

  managed.push({ name, proc });
  return proc;
}

async function stopAll(exitCode: number) {
  if (shuttingDown) return;
  shuttingDown = true;

  for (const { proc } of managed) {
    if (proc.exitCode === null && !proc.killed) {
      proc.kill("SIGTERM");
    }
  }

  await Promise.allSettled(managed.map(({ proc }) => proc.exited));
  process.exit(exitCode);
}

async function waitForHttp(url: string, timeoutMs: number) {
  const startedAt = Date.now();
  while (Date.now() - startedAt < timeoutMs) {
    try {
      await fetch(url);
      return;
    } catch {
      await Bun.sleep(500);
    }
  }
  throw new Error(`Timed out waiting for ${url}`);
}

process.on("SIGINT", () => {
  void stopAll(130);
});

process.on("SIGTERM", () => {
  void stopAll(143);
});

const backend = spawnProcess(
  "backend",
  [
    "uv",
    "run",
    "python",
    "backend/Bot.py",
    "--port",
    String(devBackendPort),
    "--no-frontend",
    "--hosted-by-tauri",
  ],
  rootDir,
  {
    ZZZ_DESKTOP_TOKEN: desktopToken,
  }
);

backend.exited.then((code) => {
  if (!shuttingDown && code !== 0) {
    console.error(`[run-tauri-app] backend exited with code ${code}`);
    void stopAll(code ?? 1);
  }
});

const frontend = spawnProcess("frontend", ["bun", "run", "dev"], frontendDir, {
  VITE_BACKEND_URL: devBackendUrl,
});
frontend.exited.then((code) => {
  if (!shuttingDown && code !== 0) {
    console.error(`[run-tauri-app] frontend exited with code ${code}`);
    void stopAll(code ?? 1);
  }
});

try {
  await Promise.all([
    waitForHttp("http://127.0.0.1:3000", 120_000),
    waitForHttp(devBackendUrl, 120_000),
  ]);

  const tauri = spawnProcess("tauri", ["cargo", "tauri", "dev"], rootDir, {
    ZZZ_DESKTOP_TOKEN: desktopToken,
    ZZZ_DEV_BACKEND_PORT: String(devBackendPort),
  });
  launchedTauri = true;

  const tauriCode = await tauri.exited;
  await stopAll(tauriCode ?? 0);
} catch (error) {
  const detail = error instanceof Error ? error.message : String(error);
  console.error(`[run-tauri-app] ${detail}`);
  await stopAll(1);
}

if (!launchedTauri) {
  await stopAll(1);
}
