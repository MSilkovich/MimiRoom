import fs from 'node:fs';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';

const root = fileURLToPath(new URL('../', import.meta.url));
function checkDirectory(directory) {
  for (const entry of fs.readdirSync(directory, {withFileTypes: true})) {
    const file = path.join(directory, entry.name);
    if (entry.isDirectory()) checkDirectory(file);
    else if (/\.(?:m?js)$/.test(entry.name)) {
      const result = spawnSync(process.execPath, ['--check', file], {stdio: 'inherit'});
      if (result.status !== 0) process.exit(result.status || 1);
    }
  }
}
for (const directory of ['dist', 'server', 'scripts', 'tests']) {
  checkDirectory(path.join(root, directory));
}
JSON.parse(fs.readFileSync(path.join(root, 'docs/openapi.json'), 'utf8'));
console.log('Синтаксис JavaScript и JSON контракта проверен.');
