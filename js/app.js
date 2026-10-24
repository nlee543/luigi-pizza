import { navigation } from './components/navigation.js';
import { home, menu } from './components/home.js?v=pizza-photos-1';
import { pizzaBuilder } from './components/pizzaBuilder.js?v=pizza-photos-1';
import { cart } from './components/cart.js';
import { checkout } from './components/checkout.js';
import { tracker } from './components/orderTracker.js';
import { rewards, account } from './components/account.js';
import { supportChat } from './components/supportChat.js';
import { dashboard } from './components/dashboard.js';
import { staffLogin } from './components/staffLogin.js';
import { staffAuthService } from './services/staffAuthService.js';
import { allowedStaffRoute } from './services/staffAccess.js';
import { apiClient } from './services/apiClient.js';
import { customerLogin } from './components/customerLogin.js';
import {
  staffShell,
  mountStaffShell,
  staffOrders,
  staffInventory,
  staffTeam,
  staffSupport,
  staffPromotions,
} from './components/staff.js';
import { store } from './services/store.js';
import { $, notify, escapeHTML } from './utils/dom.js';
let currentRoute = '';
function render({ focus = false } = {}) {
  let [route = 'home', query = ''] = (location.hash.slice(1) || 'home').split('?');
  const params = new URLSearchParams(query);
  if (
    apiClient.enabled() &&
    ['account', 'checkout'].includes(route) &&
    apiClient.user()?.role !== 'customer'
  ) {
    params.set('next', route);
    route = 'customer-login';
    history.replaceState(null, '', '#customer-login?' + params.toString());
  }
  if ((route === 'staff' || route.startsWith('staff/')) && !staffAuthService.isSignedIn()) {
    params.set('next', route);
    route = 'employee-login';
    history.replaceState(null, '', '#employee-login?' + params.toString());
  }
  if (route === 'staff' || route.startsWith('staff/')) {
    const allowed = allowedStaffRoute(route);
    if (allowed !== route) {
      route = allowed;
      history.replaceState(null, '', '#' + route);
    }
  }
  const main = $('#main');
  main.onclick = null;
  main.onchange = null;
  try {
    let component;
    const refresh = () => {
      const active = document.activeElement;
      const id = active?.id;
      render();
      if (id) document.getElementById(id)?.focus();
    };
    const routes = {
      home: () => ({ html: home() }),
      menu: () => ({ html: menu() }),
      builder: () => pizzaBuilder(params),
      cart: () => cart(refresh),
      checkout: () => checkout(),
      track: () => tracker(params, refresh),
      confirmation: () => tracker(params, refresh, true),
      rewards: () => rewards(),
      account: () => account(refresh),
      support: () => supportChat(),
      'employee-login': () => staffLogin(params),
      'customer-login': () => customerLogin(params),
      staff: () => dashboard(),
      'staff/orders': () => staffOrders(),
      'staff/inventory': () => staffInventory(),
      'staff/team': () => staffTeam(refresh),
      'staff/support': () => staffSupport(),
      'staff/promotions': () => staffPromotions(refresh),
    };
    component = routes[route]
      ? routes[route]()
      : {
          html: '<section class="section empty"><h1>This page isn’t on the menu.</h1><a class="button" href="#home">Back to home</a></section>',
        };
    navigation(route);
    main.innerHTML = route.startsWith('staff') ? staffShell(route, component.html) : component.html;
    if (route.startsWith('staff')) mountStaffShell(refresh);
    component.mount?.();
    document.title = `${route === 'home' ? 'Fresh from the oven' : route.split('/').at(-1)[0].toUpperCase() + route.split('/').at(-1).slice(1)} | Luigi’s Pizzeria`;
    if (focus) {
      window.scrollTo(0, 0);
      main.focus({ preventScroll: true });
    }
    currentRoute = route;
  } catch (error) {
    main.innerHTML = `<section class="section empty"><h1>Something needs a little attention.</h1><p role="alert">${escapeHTML(error.message)}</p><a class="button" href="#home">Back to home</a></section>`;
    console.error(error);
  }
}
window.addEventListener('hashchange', async () => {
  try {
    if (apiClient.enabled() && apiClient.user()) await apiClient.refresh();
    render({ focus: true });
  } catch (error) {
    if (error.status === 401) {
      await apiClient.restore();
      store.clearSession();
      render({ focus: true });
    }
    notify(error.message);
  }
});
window.addEventListener('unhandledrejection', (event) => {
  notify(event.reason?.message || 'The change could not be saved. Please try again.');
  event.preventDefault();
});
window.addEventListener('luigis:change', () => navigation(currentRoute));
// Demo storage belongs to this browser. Refresh on another tab's saved changes.
window.addEventListener('storage', (event) => {
  if (event.key === 'luigis-demo-v1') location.reload();
});
if (apiClient.enabled()) {
  $('#main').innerHTML =
    '<section class="section"><p role="status">Connecting to Luigi’s…</p></section>';
  try {
    await apiClient.restore();
    render();
  } catch (error) {
    $('#main').innerHTML =
      `<section class="section"><h1>We couldn’t reach the kitchen.</h1><p role="alert">${escapeHTML(error.message)}</p><button class="button" id="reload-app">Try again</button></section>`;
    $('#reload-app').onclick = () => location.reload();
  }
} else render();
if (store.warning()) notify(store.warning());
