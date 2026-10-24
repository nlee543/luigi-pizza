import { supportService } from '../services/supportService.js';
import { aiSupportService } from '../services/aiSupportService.js';
import { orderService } from '../services/orderService.js';
import { $, escapeHTML, errorBox, notify, openDialog } from '../utils/dom.js';
export function supportChat() {
  let busy = false;
  let category = 'Representative requested';
  return {
    html: `<section class="page-head"><p class="eyebrow">A LITTLE HELP, WHEN YOU NEED IT</p><h1>Let’s sort it out.</h1><p>Quick answers from our automated demo assistant. Real issues deserve a real person.</p></section><section class="section compact support-layout"><div class="panel chat-panel"><div class="chat-header"><div class="assistant-icon" aria-hidden="true">L</div><div><h2>Luigi’s assistant</h2><small>Automated · mock responses</small></div></div><div id="chat-messages" class="chat-messages" role="log" aria-live="polite" aria-label="Support conversation"></div><div id="chat-error"></div><form id="chat-form"><label class="sr-only" for="chat-input">Your message</label><div class="inline-field"><input id="chat-input" name="message" placeholder="Ask us anything about your pizza…" maxlength="1500" required><button class="button" id="send-chat">Send</button></div></form></div><aside><section class="panel"><p class="eyebrow">WE’VE GOT YOUR BACK</p><h2>Prefer a person?</h2><p>Payment, refunds, allergies, safety, or a tricky order issue? We’ll create a ticket for a representative.</p><button class="button full secondary" id="representative">Talk to a Representative</button><p class="field-hint">Demo tickets are saved locally. No real employee receives a notification.</p></section><section class="panel"><h3>Quick questions</h3>${['Where is my order?', 'What are your pizza prices?', 'How many reward points do I have?', 'What promotions are available?'].map((q) => `<button class="quick-question" data-question="${q}">${q}<span aria-hidden="true">+</span></button>`).join('')}</section><div id="ticket-result" aria-live="polite"></div></aside></section>`,
    mount() {
      const renderMessages = () => {
        const box = $('#chat-messages');
        if (!box) return;
        box.innerHTML = supportService
          .messages()
          .map(
            (m) =>
              `<div class="chat-message ${m.role}"><small>${m.role === 'assistant' ? 'Automated assistant' : 'You'}</small><p>${escapeHTML(m.text)}</p></div>`,
          )
          .join('');
        box.scrollTop = box.scrollHeight;
      };
      renderMessages();
      async function send(message) {
        if (busy) return;
        busy = true;
        try {
          supportService.addMessage('customer', message);
          renderMessages();
          $('#send-chat').disabled = true;
          $('#send-chat').textContent = 'Thinking…';
          $('#chat-input').value = '';
          const response = await aiSupportService.reply(message);
          supportService.addMessage('assistant', response.text);
          if (response.escalate) {
            category = response.category;
            supportService.addMessage(
              'assistant',
              'I’ll open a ticket form so you can confirm the details for a representative.',
            );
          }
          renderMessages();
          if (response.escalate && $('#representative')) $('#representative').click();
        } catch (err) {
          const error = $('#chat-error');
          if (error)
            error.innerHTML = errorBox(
              'The assistant is unavailable. You can still talk to a representative.',
            );
        } finally {
          busy = false;
          if ($('#send-chat')) {
            $('#send-chat').disabled = false;
            $('#send-chat').textContent = 'Send';
          }
        }
      }
      $('#chat-form').onsubmit = async (e) => {
        e.preventDefault();
        const message = new FormData(e.target).get('message').trim();
        if (message) send(message);
      };
      $('#main').onclick = (e) => {
        const button = e.target.closest('[data-question]');
        if (button) send(button.dataset.question);
      };
      $('#representative').onclick = () => {
        const customerMessage =
          supportService
            .messages()
            .filter((m) => m.role === 'customer')
            .at(-1)?.text || '';
        openDialog(
          'Talk to a Representative',
          `<form id="ticket-form"><div id="ticket-error"></div><label for="ticket-category">Issue category</label><select id="ticket-category" name="category">${['Representative requested', 'Order issue', 'Payment dispute', 'Safety or allergy', 'Employee complaint', 'Legal concern', 'Other / uncertain'].map((c) => `<option ${c === category ? 'selected' : ''}>${c}</option>`).join('')}</select><label for="ticket-order">Order number (optional)</label><input id="ticket-order" name="orderId" value="${escapeHTML(orderService.current()?.id || '')}" maxlength="30"><label for="ticket-description">What happened?</label><textarea id="ticket-description" name="description" required maxlength="1500" rows="5">${escapeHTML(customerMessage)}</textarea><p class="field-hint">Your recent conversation will be attached. This is a locally saved demo ticket.</p><button class="button full">Create support ticket</button></form>`,
          (dialog) => {
            $('#ticket-form', dialog).onsubmit = async (e) => {
              e.preventDefault();
              try {
                const ticket = await supportService.createTicket(
                  Object.fromEntries(new FormData(e.target)),
                );
                dialog.close();
                $('#ticket-result').innerHTML =
                  `<section class="panel success"><h3>Your issue has been recorded.</h3><p>Ticket <strong>${escapeHTML(ticket.id)}</strong><br>Status: Escalated</p><p>${escapeHTML(ticket.description)}</p><small>View and manage it in the Staff demo → Tickets.</small></section>`;
                notify('Demo ticket created and escalated.');
              } catch (err) {
                $('#ticket-error', dialog).innerHTML = errorBox(err.message);
              }
            };
          },
        );
      };
    },
  };
}
