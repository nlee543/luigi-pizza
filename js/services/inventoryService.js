import { store, page } from './store.js';
import { ingredientUsage } from '../utils/currency.js';
import { apiClient } from './apiClient.js';
export function ensureStock(state, items, branchId) {
  const usage = ingredientUsage(items);
  for (const [id, amount] of Object.entries(usage)) {
    const ingredient = state.ingredients.find((i) => i.id === id && i.branchId === branchId);
    if (!ingredient || ingredient.quantity < amount)
      throw new Error(
        `Not enough ${ingredient?.name || id} available. Please change your order or contact the store.`,
      );
  }
  return usage;
}
export const stockStatus = (item) =>
  item.quantity <= 0
    ? 'Out of Stock'
    : item.quantity <= item.reorderLevel
      ? 'Low Stock'
      : 'In Stock';
export const inventoryService = {
  list({ branchId = 'downtown', search = '', category = '', status = '', pageNumber = 1 } = {}) {
    return page(
      store
        .read()
        .ingredients.filter(
          (i) =>
            i.branchId === branchId &&
            i.name.toLowerCase().includes(search.toLowerCase()) &&
            (!category || i.category === category) &&
            (!status || stockStatus(i) === status),
        ),
      pageNumber,
    );
  },
  all: (branchId) => store.read().ingredients.filter((i) => i.branchId === branchId),
  update(id, branchId, quantity, restock = false) {
    if (apiClient.enabled())
      return apiClient.command('stock', { id, branchId, quantity: Number(quantity), restock });
    const amount = Number(quantity);
    if (!Number.isFinite(amount) || amount < 0 || amount > 100000)
      throw new Error('Stock must be a number from 0 to 100,000.');
    store.transact((s) => {
      const i = s.ingredients.find((x) => x.id === id && x.branchId === branchId);
      if (!i) throw new Error('Ingredient not found.');
      i.quantity = restock ? i.quantity + amount : amount;
      if (restock) i.lastRestocked = new Date().toISOString();
    });
  },
};
