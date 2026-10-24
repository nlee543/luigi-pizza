// Intentional seed/rule update tool. Does not modify an existing runtime DB.
import { initialData } from '../js/data.js';
import { SIZES, TOPPINGS, DRINKS } from '../js/config.js';
import { writeFileSync } from 'node:fs';
const fixture = { state: initialData(), sizes: SIZES, toppings: TOPPINGS, drinks: DRINKS };
// ASCII JSON escapes avoid editor/shell encoding conversion on Windows.
const json = JSON.stringify(fixture, null, 2).replace(
  /[^\x00-\x7f]/g,
  (character) => '\\u' + character.charCodeAt(0).toString(16).padStart(4, '0'),
);
writeFileSync(new URL('../backend/frontend-fixture.json', import.meta.url), json, 'utf8');
console.log('Versioned frontend fixture exported. Existing database unchanged.');
