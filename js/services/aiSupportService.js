import { orderService } from './orderService.js';
import { rewardsService } from './rewardsService.js';
import { money } from '../utils/currency.js';
// Production: POST /api/support/chat; server owns AI credentials and escalation policy.
export const aiSupportService = {
  async reply(message) {
    await new Promise((r) => setTimeout(r, 450));
    const text = message.toLowerCase();
    const categories = [
      [/allerg|safety|sick|injur/, 'Safety or allergy'],
      [/fraud|payment|charge|refund/, 'Payment dispute'],
      [/employee|rude/, 'Employee complaint'],
      [/legal|lawyer/, 'Legal concern'],
      [/missing|wrong|failed|late|delivery problem/, 'Order issue'],
      [/person|human|representative/, 'Representative requested'],
    ];
    const match = categories.find(([pattern]) => pattern.test(text));
    if (match)
      return {
        text: 'This needs a real representative. I can record the details and escalate your issue; I cannot issue refunds or resolve safety and payment disputes.',
        escalate: true,
        category: match[1],
      };
    if (/order|track|ready|status/.test(text)) {
      const order = orderService.current();
      return {
        text: order
          ? `Your order ${order.id} is ${order.status.toLowerCase()}. Estimated ${order.type === 'delivery' ? 'arrival' : 'ready'} time: ${new Date(order.estimatedAt).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}. Estimates may change.`
          : 'Use Track Order with your order number, or place your first order. I do not have a current order for this demo account.',
      };
    }
    if (/price|cost|menu|topping|pizza/.test(text))
      return {
        text: 'Small (8″): $5.00 + $1.00 per topping. Medium (12″): $7.00 + $2.00 per topping. Large (14″): $9.00 + $3.00 per topping. Marinara and cheese are included. Drinks are $1.00, $2.00, or $3.00 by size.',
      };
    if (/reward|point/.test(text))
      return {
        text: `Your demo balance is ${rewardsService.balance()} points. Earn 1 point per $1 spent, including tax and delivery. Redeem 100 points for ${money(500)} off in Rewards.`,
      };
    if (/deal|promo|discount/.test(text))
      return {
        text: 'Use WELCOME5 for $5.00 off an order of $20.00 or more before tax. Promotions are validated at checkout.',
      };
    if (/hour|open|close/.test(text))
      return {
        text: 'Luigi’s is open daily from 10:00 AM to 11:00 PM. This prototype accepts demo orders at any time.',
      };
    if (/account|email|phone|address|name/.test(text))
      return {
        text: 'You can edit your demo name, email, phone, and saved address from Account. If you need more help, talk to a representative.',
      };
    return {
      text: 'I’m not sure I can answer that accurately. Let’s pass your question to a representative.',
      escalate: true,
      category: 'Other / uncertain',
    };
  },
};
