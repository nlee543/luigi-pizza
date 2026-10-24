import { escapeHTML } from '../utils/dom.js';
import { money } from '../utils/currency.js';
export function chart(title, entries, { currency = false, line = false, summary = '' } = {}) {
  const pairs = Array.isArray(entries) ? entries : Object.entries(entries);
  const max = Math.max(1, ...pairs.map(([, v]) => v));
  const format = (v) => (currency ? money(v) : String(v));
  const graph = line
    ? lineGraph(title, pairs, max, format)
    : `<div class="bar-chart" aria-hidden="true">${pairs.map(([label, value]) => `<div class="bar-row"><span>${escapeHTML(label)}</span><div><i style="width:${Math.max(value ? 2 : 0, (value / max) * 100)}%"></i></div><strong>${format(value)}</strong></div>`).join('')}</div>`;
  return `<section class="panel chart-panel"><h2>${escapeHTML(title)}</h2><p class="field-hint">${escapeHTML(summary || 'Fictional demonstration data.')}</p>${pairs.length ? graph : '<p>No data for this selection.</p>'}<details><summary>View chart data</summary><div class="table-wrap"><table><caption class="sr-only">${escapeHTML(title)} data</caption><thead><tr><th scope="col">Category / date</th><th scope="col">Value</th></tr></thead><tbody>${pairs.map(([label, value]) => `<tr><th scope="row">${escapeHTML(label)}</th><td>${format(value)}</td></tr>`).join('')}</tbody></table></div></details></section>`;
}

function lineGraph(title, pairs, maximum, format) {
  const ceiling = Math.max(1, Math.ceil(maximum / 4) * 4);
  const x = (index) => 90 + (index * 625) / Math.max(1, pairs.length - 1);
  const y = (value) => 180 - (value / ceiling) * 150;
  const grid = Array.from({ length: 5 }, (_, index) => {
    const value = (ceiling * index) / 4;
    return `<line x1="90" x2="715" y1="${y(value)}" y2="${y(value)}" stroke="#dedbd2"/>
      <text x="80" y="${y(value) + 4}" text-anchor="end" fill="#666b61" font-size="12">${escapeHTML(format(value))}</text>`;
  }).join('');
  const interval = Math.max(1, Math.ceil(pairs.length / 5));
  const labels = pairs
    .map(([label], index) =>
      index % interval === 0 || index === pairs.length - 1
        ? `<text x="${x(index)}" y="210" text-anchor="middle" fill="#666b61" font-size="12">${escapeHTML(label)}</text>`
        : '',
    )
    .join('');
  return `<svg class="line-chart" viewBox="0 0 760 235" role="img" aria-label="${escapeHTML(title)}; exact values are in the data table">
    <title>${escapeHTML(title)}</title>${grid}
    <polyline points="${pairs.map(([, value], index) => `${x(index)},${y(value)}`).join(' ')}" fill="none" stroke="#bd3626" stroke-width="3" stroke-linejoin="round"/>
    ${pairs.map(([label, value], index) => `<circle cx="${x(index)}" cy="${y(value)}" r="4" fill="#bd3626"><title>${escapeHTML(label)}: ${escapeHTML(format(value))}</title></circle>`).join('')}
    ${labels}</svg>`;
}
