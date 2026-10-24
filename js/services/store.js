import { CONFIG } from '../config.js';
import { initialData } from '../data.js';
import { apiClient } from './apiClient.js';
let storageError = '';
function anonymousState(cart = []) {
  return {
    ...initialData(),
    cart,
    orders: [],
    ingredients: [],
    employees: [],
    shifts: [],
    customers: [
      { id: 'guest', firstName: 'Guest', lastName: '', email: '', phone: '', address: null },
    ],
    currentCustomerId: 'guest',
    rewards: {},
    rewardTransactions: [],
    tickets: [],
    lastOrderId: null,
    selectedPromotion: null,
    integrationUserId: null,
  };
}
function load() {
  try {
    if (apiClient.enabled()) {
      const saved = JSON.parse(localStorage.getItem('luigis-api-cart-v1') || '[]');
      return anonymousState(Array.isArray(saved) ? saved : []);
    }
    if (typeof localStorage === 'undefined') return initialData();
    const raw = localStorage.getItem(CONFIG.storageKey);
    if (!raw) return initialData();
    const value = JSON.parse(raw);
    if (
      value.version !== 1 ||
      !Array.isArray(value.orders) ||
      !Array.isArray(value.cart) ||
      !Array.isArray(value.ingredients) ||
      !value.customers?.length
    )
      throw new Error('Invalid saved data');
    return value;
  } catch {
    storageError = 'Saved demo data could not be loaded. A fresh demo was started.';
    return apiClient.enabled() ? anonymousState() : initialData();
  }
}
let state = load();
apiClient.onState((serverState) => {
  const branch = state.branchId;
  const employee = state.staffEmployeeId;
  const userChanged = state.integrationUserId !== apiClient.user()?.id;
  state = { ...state, ...serverState, integrationUserId: apiClient.user()?.id };
  // Preserve an admin's presentation selection only within the same login.
  if (!userChanged && apiClient.user()?.role === 'admin') {
    state.branchId = branch;
    if (state.employees.some((e) => e.id === employee && e.apiUserId === apiClient.user()?.id))
      state.staffEmployeeId = employee;
  }
  if (userChanged) {
    state.chat = [
      { role: 'assistant', text: 'Hi, I’m Luigi’s automated demo assistant. How can I help?' },
    ];
    state.selectedPromotion = null;
    state.lastOrderId = null;
  }
  if (typeof window !== 'undefined') window.dispatchEvent(new CustomEvent('luigis:change'));
});
export const store = {
  read: () => structuredClone(state),
  transact(fn) {
    const draft = structuredClone(state);
    const result = fn(draft);
    if (typeof localStorage !== 'undefined') {
      try {
        if (apiClient.enabled())
          localStorage.setItem('luigis-api-cart-v1', JSON.stringify(draft.cart));
        else localStorage.setItem(CONFIG.storageKey, JSON.stringify(draft));
      } catch {
        throw new Error(
          'Unable to save demo data. Your change was not applied. Free browser storage and try again.',
        );
      }
    }
    state = draft;
    if (typeof window !== 'undefined') window.dispatchEvent(new CustomEvent('luigis:change'));
    return result;
  },
  warning: () => storageError,
  reset() {
    const draft = initialData();
    if (typeof localStorage !== 'undefined')
      localStorage.setItem(CONFIG.storageKey, JSON.stringify(draft));
    state = draft;
  },
  clearSession() {
    state = anonymousState(state.cart);
  },
};
export const uid = (prefix) =>
  prefix +
  '-' +
  (globalThis.crypto?.randomUUID?.() || Date.now() + '-' + Math.random().toString(36).slice(2, 9));
export function page(items, index = 1, size = CONFIG.pageSize) {
  const pages = Math.max(1, Math.ceil(items.length / size));
  const current = Math.max(1, Math.min(pages, index));
  return {
    items: items.slice((current - 1) * size, current * size),
    total: items.length,
    page: current,
    pages,
  };
}
