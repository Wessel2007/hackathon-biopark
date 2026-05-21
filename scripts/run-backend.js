const { spawn } = require("child_process");
const fs = require("fs");
const path = require("path");

const backendDir = path.resolve(__dirname, "..", "backend");
const venvDir = path.join(backendDir, ".venv");
const win = process.platform === "win32";

const python = win
  ? path.join(venvDir, "Scripts", "python.exe")
  : path.join(venvDir, "bin", "python");

const executable = fs.existsSync(python) ? python : win ? "python" : "python3";

const child = spawn(
  executable,
  ["-m", "uvicorn", "app.main:app", "--reload", "--host", "127.0.0.1", "--port", "8000"],
  { cwd: backendDir, stdio: "inherit", env: process.env, shell: win }
);

child.on("exit", (code) => process.exit(code ?? 1));
