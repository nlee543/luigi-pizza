import { staffAuthService, staffDestination } from '../services/staffAuthService.js';
import { employeeService } from '../services/employeeService.js';
import { apiClient } from '../services/apiClient.js';
import { $, errorBox, notify } from '../utils/dom.js';

export function staffLogin(params) {
  return {
    html: `<section class="page-head"><p class="eyebrow">THE PEOPLE BEHIND THE PIZZA</p><h1>Employee login.</h1><p>Sign in to open the staff workspace.</p></section>
      <section class="section compact"><div class="panel staff-login-panel">
        <h2>Welcome back.</h2>
        <form id="staff-login-form">
          <div id="staff-login-error" tabindex="-1"></div>
          <label for="staff-username">Username</label>
          <input id="staff-username" name="username" autocomplete="username" required maxlength="100">
          <label for="staff-password">Password</label>
          <input id="staff-password" name="password" type="password" autocomplete="current-password" required maxlength="100" aria-describedby="staff-login-note">
          <button class="button full" type="submit">Sign in</button>
        </form>
        <p class="field-hint" id="staff-login-note">Employee login. The integrated server verifies your credentials and permissions; the standalone preview uses secure server authentication only when connected.</p>
        <a class="text-link" href="#home">Back to the customer site</a>
      </div></section>`,
    mount() {
      $('#staff-login-form').onsubmit = async (event) => {
        event.preventDefault();
        const button = event.target.querySelector('button[type="submit"]');
        if (button.disabled) return;
        button.disabled = true;
        const data = new FormData(event.target);
        try {
          // Universal demo login opens Luigi's administrator workspace.
          const username = data.get('username');
          const password = data.get('password');
          await staffAuthService.signIn(username, password);
          if (!apiClient.enabled()) employeeService.select('e1');
          $('#staff-password').value = '';
          notify('Welcome, ' + employeeService.current().firstName + '.');
          location.hash = staffDestination(params.get('next'));
        } catch (error) {
          try {
            await staffAuthService.signOut();
          } catch {
            /* Preserve the original login error. */
          }
          $('#staff-login-error').innerHTML = errorBox(error.message);
          $('#staff-password').value = '';
          $('#staff-login-error').focus();
        } finally {
          button.disabled = false;
        }
      };
    },
  };
}
