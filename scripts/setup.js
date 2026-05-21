const { execSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const backendDir = path.join(root, "backend");
const frontendDir = path.join(root, "frontend");
const venvDir = path.join(backendDir, ".venv");

function run(cmd, cwd = root) {
  console.log(`\n> ${cmd}`);
  execSync(cmd, { cwd, stdio: "inherit", env: process.env });
}

function pythonLauncher() {
  const win = process.platform === "win32";
  const venvPython = win
    ? path.join(venvDir, "Scripts", "python.exe")
    : path.join(venvDir, "bin", "python");
  if (fs.existsSync(venvPython)) return venvPython;
  return win ? "python" : "python3";
}

function ensureEnvFile(examplePath, targetPath, patch) {
  if (fs.existsSync(targetPath)) return;
  if (!fs.existsSync(examplePath)) return;
  let content = fs.readFileSync(examplePath, "utf8");
  if (patch) content = patch(content);
  fs.writeFileSync(targetPath, content, "utf8");
  console.log(`Criado ${path.relative(root, targetPath)} a partir do exemplo.`);
}

console.log("=== Instalando dependências ===\n");

// Raiz (concurrently)
run("npm install", root);

// Frontend
run("npm install", frontendDir);

ensureEnvFile(
  path.join(frontendDir, ".env.example"),
  path.join(frontendDir, ".env"),
  () => "VITE_API_URL=http://localhost:8000\n"
);

// Backend — venv + pip
const py = pythonLauncher();
if (!fs.existsSync(venvDir)) {
  run(`${py} -m venv .venv`, backendDir);
}

const venvPython = pythonLauncher();
const pip = `"${venvPython}" -m pip`;
run(`${pip} install --upgrade pip`, backendDir);
run(`${pip} install -r requirements.txt`, backendDir);

ensureEnvFile(
  path.join(backendDir, ".env.example"),
  path.join(backendDir, ".env")
);

console.log("\n=== Setup concluído ===\n");
