import { apiClient } from '../services/apiClient.js';
import { $, errorBox, notify } from '../utils/dom.js';

export function customerLogin(params) {
  return {
    html: `<section class="page-head"><p class="eyebrow">YOUR CORNER OF LUIGI’S</p><h1>Sign in for pizza night.</h1><p>Your account keeps orders and rewards together.</p></section>
      <section class="section compact"><div class="panel staff-login-panel">
        <form id="customer-login"><h2>Sign in</h2><div id="customer-auth-error" tabindex="-1"></div>
          <label for="customer-email">Email</label><input id="customer-email" name="email" type="email" autocomplete="username" required>
          <label for="customer-password">Password</label><input id="customer-password" name="password" type="password" autocomplete="current-password" required>
          <button class="button full">Sign in</button></form>
        <details><summary>Create a customer account</summary><form id="customer-register">
          <div id="register-error" tabindex="-1"></div>
          <label for="register-name">Full name</label><input id="register-name" name="name" autocomplete="name" maxlength="100" required>
          <label for="register-email">Email</label><input id="register-email" name="email" type="email" autocomplete="email" required>
          <label for="register-phone">Phone</label><input id="register-phone" name="phone_number" type="tel" autocomplete="tel" maxlength="40" required>
          <label for="register-address">Address</label><input id="register-address" name="address" autocomplete="street-address" maxlength="500" required>
          <label for="register-password">Password (at least 12 characters)</label><input id="register-password" name="password" type="password" minlength="12" maxlength="128" autocomplete="new-password" required>
          <button class="button full">Create account</button></form></details>
          <p class="field-hint">Local college demonstration. Use fictional details. Payments remain simulated.</p>
      </div></section>`,
    mount() {
      const destination = params.get('next') === 'checkout' ? 'checkout' : 'account';
      $('#customer-login').onsubmit = async (event) => {
        event.preventDefault();
        const button = event.target.querySelector('button');
        button.disabled = true;
        try {
          const data = Object.fromEntries(new FormData(event.target));
          const user = await apiClient.login(data.email, data.password);
          if (user.role !== 'customer') {
            location.hash = 'staff/orders';
            return;
          }
          notify('You’re signed in.');
          location.hash = destination;
        } catch (error) {
          $('#customer-auth-error').innerHTML = errorBox(error.message);
          $('#customer-auth-error').focus();
        } finally {
          button.disabled = false;
        }
      };
      $('#customer-register').onsubmit = async (event) => {
        event.preventDefault();
        const button = event.target.querySelector('button');
        button.disabled = true;
        try {
          const data = Object.fromEntries(new FormData(event.target));
          data.dine_in_name = data.name.split(' ')[0];
          await apiClient.register(data);
          await apiClient.login(data.email, data.password);
          notify('Account created.');
          location.hash = destination;
        } catch (error) {
          $('#register-error').innerHTML = errorBox(error.message);
          $('#register-error').focus();
        } finally {
          button.disabled = false;
        }
      };
    },
  };
}
