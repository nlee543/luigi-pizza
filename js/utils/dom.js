export const escapeHTML = (value) =>
  String(value ?? '').replace(
    /[&<>"']/g,
    (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c],
  );
export const $ = (selector, root = document) => root.querySelector(selector);
export const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
export const dateTime = (value) =>
  new Date(value).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
export const time = (value) =>
  new Date(value).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
let toastTimer;
export function notify(message) {
  const el = $('#toast');
  el.textContent = message;
  el.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove('show'), 4500);
}
export function debounce(fn, delay = 200) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}
export function openDialog(title, content, onReady) {
  const dialog = $('#modal');
  const previous = document.activeElement;
  const previousId = previous?.id;
  const triggerAttribute = [
    'data-stock',
    'data-restock',
    'data-ticket',
    'data-detail',
    'data-edit-promo',
  ].find((name) => previous?.hasAttribute(name));
  const triggerValue = triggerAttribute ? previous.getAttribute(triggerAttribute) : null;
  dialog.innerHTML = `<div class="dialog-heading"><h2 id="modal-title">${escapeHTML(title)}</h2><button type="button" class="icon-button" aria-label="Close dialog" data-close>×</button></div>${content}`;
  dialog.querySelector('[data-close]').onclick = () => dialog.close();
  dialog.onclose = () => {
    const replacement = previousId
      ? document.getElementById(previousId)
      : triggerAttribute
        ? document.querySelector(`[${triggerAttribute}="${CSS.escape(triggerValue)}"]`)
        : null;
    (previous?.isConnected ? previous : replacement || $('#main'))?.focus({ preventScroll: true });
  };
  dialog.showModal();
  onReady?.(dialog);
}
export const errorBox = (message) => `<p class="error" role="alert">${escapeHTML(message)}</p>`;
export const badge = (status) =>
  `<span class="badge ${status === 'Completed' ? 'good' : ''}">${escapeHTML(status)}</span>`;
