import { store, uid } from './store.js';
import { lineTotal, validQuantity } from '../utils/currency.js';
export const cartService = {
  list: () => store.read().cart,
  add(item) {
    lineTotal(item);
    store.transact((s) =>
      s.cart.push({
        ...item,
        instructions: String(item.instructions || '').slice(0, 250),
        id: uid('item'),
      }),
    );
  },
  update(id, changes) {
    store.transact((s) => {
      const i = s.cart.findIndex((x) => x.id === id);
      if (i < 0) throw new Error('This item is no longer in the cart.');
      const item = { ...s.cart[i], ...changes, id };
      lineTotal(item);
      s.cart[i] = item;
    });
  },
  quantity(id, value) {
    this.update(id, { quantity: validQuantity(value) });
  },
  remove(id) {
    store.transact((s) => {
      s.cart = s.cart.filter((x) => x.id !== id);
    });
  },
};
