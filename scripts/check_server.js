// Verifies the live server and the complete module graph without a browser.
import { readdir, readFile } from 'node:fs/promises';
import { join } from 'node:path';
const origin = process.env.PREVIEW_URL || 'http://127.0.0.1:5173';
const paths = ['/', '/assets/favicon.svg', '/assets/pizza.jpg'];
async function collect(directory) {
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) await collect(path);
    else if (/\.(css|js)$/.test(path)) paths.push('/' + path.replaceAll('\\', '/'));
  }
}
await collect('js');
await collect('css');
for (const path of paths) {
  const response = await fetch(origin + path);
  if (response.status !== 200) throw new Error(`${path}: HTTP ${response.status}`);
  const body = await response.arrayBuffer();
  if (!body.byteLength) throw new Error(`${path}: empty response`);
}
for (const path of ['/database/schema.sql', '/README.md', '/.git/config']) {
  const response = await fetch(origin + path);
  if (response.status !== 404) throw new Error(`${path}: nonpublic file should not be served`);
}
const html = await readFile('index.html', 'utf8');
for (const target of [
  'js/app.js',
  'css/styles.css',
  'css/customer.css',
  'css/staff.css',
  'css/responsive.css',
]) {
  if (!html.includes(target)) throw new Error(`Missing application asset: ${target}`);
}
console.log(
  `HTTP checks passed: ${paths.length} application assets return 200; nonpublic SQL/docs/Git files return 404.`,
);
