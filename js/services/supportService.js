import { store, uid, page } from './store.js';
import { apiClient } from './apiClient.js';
export const supportService = {
  messages: () => store.read().chat,
  addMessage(role, text) {
    store.transact((s) =>
      s.chat.push({ role, text: String(text).slice(0, 1500), createdAt: new Date().toISOString() }),
    );
  },
  createTicket({ category, description, orderId }) {
    if (apiClient.enabled())
      return apiClient.command('ticket', {
        category,
        description,
        orderId,
        messages: this.messages().slice(-20),
        summary: this.messages()
          .slice(-8)
          .map((m) => m.role + ': ' + m.text)
          .join('\n'),
      });
    if (!String(description || '').trim())
      throw new Error('Describe the issue so a representative can help.');
    return store.transact((s) => {
      const c = s.customers.find((c) => c.id === s.currentCustomerId);
      const reference = String(orderId || '')
        .trim()
        .toUpperCase();
      if (reference && !s.orders.some((o) => o.id === reference && o.customerId === c.id)) {
        throw new Error(
          'That order number was not found for this demo account. Check it or leave it blank.',
        );
      }
      const ticket = {
        id: uid('TK').slice(0, 15).toUpperCase(),
        customerId: c.id,
        customerName: c.firstName + ' ' + c.lastName,
        orderId: reference || null,
        category: String(category || 'Other / uncertain').slice(0, 100),
        description: String(description).trim().slice(0, 1500),
        summary: s.chat
          .slice(-8)
          .map((m) => m.role + ': ' + m.text)
          .join('\n')
          .slice(0, 5000),
        messages: structuredClone(s.chat.slice(-20)),
        createdAt: new Date().toISOString(),
        status: 'Escalated',
      };
      s.tickets.unshift(ticket);
      return ticket;
    });
  },
  list({ pageNumber = 1 } = {}) {
    return page(store.read().tickets, pageNumber);
  },
  update(id, status) {
    if (apiClient.enabled()) return apiClient.command('ticket-status', { id, status });
    if (!['Escalated', 'In Review', 'Resolved'].includes(status))
      throw new Error('Invalid ticket status.');
    store.transact((s) => {
      const t = s.tickets.find((t) => t.id === id);
      if (!t) throw new Error('Ticket not found.');
      t.status = status;
    });
  },
};
