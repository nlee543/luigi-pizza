import { apiClient } from './apiClient.js';
import { store } from './store.js';
export const promotionService = {
  update(id, changes) {
    if (apiClient.enabled()) return apiClient.command('promotion', { id, changes });
    return store.transact((state) =>
      Object.assign(
        state.promotions.find((p) => p.id === id),
        changes,
      ),
    );
  },
};
