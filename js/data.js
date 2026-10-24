import { TOPPINGS, DRINKS } from './config.js';
import { totals } from './utils/currency.js';
export function initialData() {
  const now = Date.now();
  const ago = (minutes) => new Date(now - minutes * 60000).toISOString();
  const customers = [
    {
      id: 'c1',
      firstName: 'Alex',
      lastName: 'Morgan',
      email: 'alex@example.test',
      phone: '202-555-0142',
      address: { street: '120 Demo Lane', city: 'Chicago', state: 'IL', zip: '60601' },
    },
    {
      id: 'c2',
      firstName: 'Jamie',
      lastName: 'Rivera',
      email: 'jamie@example.test',
      phone: '202-555-0116',
      address: null,
    },
    {
      id: 'c3',
      firstName: 'Casey',
      lastName: 'Taylor',
      email: 'casey@example.test',
      phone: '202-555-0193',
      address: null,
    },
  ];
  const ingredients = [
    {
      id: 'marinara',
      name: 'Marinara sauce',
      category: 'Base',
      unit: 'cups',
      quantity: 48,
      reorderLevel: 10,
    },
    {
      id: 'cheese',
      name: 'Cheese',
      category: 'Base',
      unit: 'cups',
      quantity: 62,
      reorderLevel: 15,
    },
    ...TOPPINGS.filter((t) => t.id !== 'extra-cheese').map((t, i) => ({
      id: t.id,
      name: t.name,
      category: t.category,
      unit: 'cups',
      quantity: i === 1 ? 3 : i === 9 ? 0 : 16 + i,
      reorderLevel: 4,
    })),
    ...DRINKS.map((d, i) => ({
      id: 'drink-' + d.id,
      name: d.name,
      category: 'Drinks',
      unit: 'units',
      quantity: i === 2 ? 5 : 50,
      reorderLevel: 10,
    })),
  ].map((i) => ({
    ...i,
    branchId: 'downtown',
    lastRestocked: ago(1400),
    supplier: i.category === 'Drinks' ? 'Demo Beverage Co.' : 'Fictional Fresh Supply',
  }));
  const employees = [
    {
      id: 'e1',
      firstName: 'Luigi',
      lastName: 'Demo',
      email: 'luigi@example.test',
      phone: '202-555-0100',
      role: 'Administrator',
      branchId: 'downtown',
      position: 'Manager',
      hireDate: '2023-03-01',
      status: 'Active',
    },
    {
      id: 'e2',
      firstName: 'Sam',
      lastName: 'Demo',
      email: 'sam@example.test',
      phone: '202-555-0101',
      role: 'Branch Employee',
      branchId: 'downtown',
      position: 'Kitchen lead',
      hireDate: '2024-08-12',
      status: 'Active',
    },
    {
      id: 'e3',
      firstName: 'Robin',
      lastName: 'Demo',
      email: 'robin@example.test',
      phone: '202-555-0102',
      role: 'Branch Employee',
      branchId: 'riverside',
      position: 'Shift lead',
      hireDate: '2025-02-04',
      status: 'Active',
    },
  ];
  const orders = Array.from({ length: 16 }, (_, i) => {
    const items = [
      {
        id: 'seed-' + i,
        kind: 'pizza',
        size: ['small', 'medium', 'large'][i % 3],
        toppings: i % 2 ? ['pepperoni'] : [],
        quantity: (i % 4) + 1,
        instructions: '',
      },
      { id: 'sd-' + i, kind: 'drink', size: 'medium', drinkId: 'cola', quantity: 1 },
    ];
    return {
      id: 'LP-' + (1041 + i),
      branchId: i === 15 ? 'riverside' : 'downtown',
      customerId: customers[i % 3].id,
      customer: { ...customers[i % 3] },
      items,
      type: i % 3 === 0 ? 'delivery' : 'pickup',
      payment: 'store',
      ...totals(items, { type: i % 3 === 0 ? 'delivery' : 'pickup' }),
      createdAt: ago(i < 5 ? i * 4 + 2 : 60 + i * 8),
      estimatedAt: ago(i < 5 ? -20 + i * 2 : 30 + i * 5),
      updatedAt: ago(i < 5 ? 1 : 30 + i * 5),
      status:
        i < 5
          ? ['Baking', 'Preparing', 'Order Received', 'Quality Check', 'Ready for Pickup'][i]
          : 'Completed',
      pointsEarned: i < 5 ? 0 : Math.floor(totals(items).total / 100),
      inventoryDeducted: true,
    };
  });
  const salesHistory = Array.from({ length: 14 }, (_, i) => ({
    date: new Date(now - (13 - i) * 86400000).toISOString().slice(0, 10),
    orders: 36 + ((i * 17) % 28),
    revenueCents: 65000 + ((i * 7933) % 65000),
  }));
  return {
    version: 1,
    branches: [
      { id: 'downtown', name: 'Downtown', address: '100 Example Avenue' },
      { id: 'riverside', name: 'Riverside', address: '200 Sample Street' },
    ],
    customers,
    ingredients,
    employees,
    orders,
    salesHistory,
    cart: [],
    currentCustomerId: 'c1',
    staffEmployeeId: 'e1',
    branchId: 'downtown',
    lastOrderId: null,
    rewards: { c1: 160, c2: 78, c3: 23 },
    rewardTransactions: [],
    promotions: [
      {
        id: 'WELCOME5',
        name: 'A little welcome',
        description: '$5 off an order of $20 or more. Use code WELCOME5.',
        discountType: 'fixed',
        discountValue: 500,
        minSubtotal: 2000,
        requiredPoints: 0,
        start: '2026-01-01',
        end: '2027-12-31',
        active: true,
      },
      {
        id: 'REWARD5',
        name: 'Your next slice of joy',
        description: 'Redeem 100 points for $5 off.',
        discountType: 'fixed',
        discountValue: 500,
        minSubtotal: 500,
        requiredPoints: 100,
        start: '2026-01-01',
        end: '2027-12-31',
        active: true,
      },
    ],
    selectedPromotion: null,
    shifts: [
      { id: 'sh1', employeeId: 'e2', branchId: 'downtown', clockIn: ago(180), clockOut: null },
      { id: 'sh2', employeeId: 'e1', branchId: 'downtown', clockIn: ago(480), clockOut: ago(60) },
      { id: 'sh3', employeeId: 'e3', branchId: 'riverside', clockIn: ago(240), clockOut: null },
    ],
    tickets: [
      {
        id: 'TK-1001',
        customerId: 'c2',
        customerName: 'Jamie Rivera',
        orderId: 'LP-1051',
        category: 'Order issue',
        description: 'A topping was missing.',
        summary: 'Customer requested help with missing pepperoni.',
        createdAt: ago(70),
        status: 'Escalated',
        messages: [{ role: 'customer', text: 'A topping was missing.' }],
      },
    ],
    chat: [
      {
        role: 'assistant',
        text: 'Hi, I’m Luigi’s automated demo assistant. Ask me about the menu, rewards, or your order. A representative is always one click away.',
      },
    ],
  };
}
