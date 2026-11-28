import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';

// Передавайте только доверенный JS-файл: vm не является песочницей безопасности.
const source = process.argv[2];
let catalog;
if (!source) {
  catalog = JSON.parse(fs.readFileSync(new URL('../support/catalog.json', import.meta.url), 'utf8'));
} else if (path.extname(source).toLowerCase() === '.json') {
  catalog = JSON.parse(fs.readFileSync(path.resolve(source), 'utf8'));
} else {
  const context = {window: {}};
  vm.createContext(context);
  vm.runInContext(fs.readFileSync(path.resolve(source), 'utf8'), context, {timeout: 1000});
  catalog = context.window.MIMIROOM_CATALOG;
}
if (!Array.isArray(catalog) || !catalog.length || catalog.some(card => !card || typeof card !== 'object')) {
  throw new Error('Ожидается непустой массив карточек прайса.');
}
if (source) fs.writeFileSync(new URL('../support/catalog.json', import.meta.url), JSON.stringify(catalog, null, 2));
fs.writeFileSync(new URL('../dist/support-catalog.js', import.meta.url), 'export const supportCatalog = ' + JSON.stringify(catalog) + ';\n');
console.log('Обновлены ' + catalog.length + ' карточек. Проверьте дату и факты в dist/support-core.js.');
