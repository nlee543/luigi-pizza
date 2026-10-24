import { store } from './store.js';
import { apiClient } from './apiClient.js';
export const customerService = {
  current: () => {
    const s = store.read();
    return (
      s.customers.find((c) => c.id === s.currentCustomerId) || {
        id: 'guest',
        firstName: 'Guest',
        lastName: '',
        email: '',
        phone: '',
        address: null,
      }
    );
  },
  list: () => store.read().customers,
  update(changes) {
    if (apiClient.enabled()) return apiClient.command('profile', changes);
    store.transact((s) => {
      const c = s.customers.find((c) => c.id === s.currentCustomerId);
      Object.assign(c, changes);
    });
  },
  select(id) {
    store.transact((s) => {
      if (!s.customers.some((c) => c.id === id)) throw new Error('Customer not found');
      s.currentCustomerId = id;
      s.selectedPromotion = null;
      s.chat = [
        { role: 'assistant', text: 'Hi, I’m Luigi’s automated demo assistant. How can I help?' },
      ];
    });
  },
  history: () => {
    const s = store.read();
    return s.orders.filter((o) => o.customerId === s.currentCustomerId);
  },
};
