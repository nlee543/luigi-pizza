import { cartService } from '../services/cartService.js';
import { staffAuthService } from '../services/staffAuthService.js';
import { staffLinks } from '../services/staffAccess.js';
export function navigation(route) {
  const staff = (route === 'staff' || route.startsWith('staff/')) && staffAuthService.isSignedIn();
  const count = cartService.list().reduce((n, i) => n + i.quantity, 0);
  document.querySelector('#header').innerHTML =
    `<div class="header-inner"><a class="wordmark" href="#home" aria-label="Luigi's Pizzeria home">luigi’s<span>PIZZERIA</span></a><nav aria-label="${staff ? 'Staff workspace' : 'Main navigation'}">${(staff
      ? staffLinks()
      : [
          ['home', 'Home'],
          ['menu', 'Menu'],
          ['builder', 'Build a pizza'],
          ['track', 'Track order'],
          ['rewards', 'Rewards'],
        ]
    )
      .map(
        ([id, label]) =>
          `<a href="#${id}" ${route === id ? 'aria-current="page"' : ''}>${label}</a>`,
      )
      .join(
        '',
      )}</nav><div class="header-actions">${staff ? '<a class="account-link" href="#home">Customer site</a><button class="button secondary" id="staff-sign-out">Sign out</button>' : `<a class="account-link" href="#account" aria-label="Your account">Account</a><a class="button cart-link" href="#cart">Bag <span aria-label="${count} items">${count}</span></a>`}</div></div>`;
  const signOut = document.querySelector('#staff-sign-out');
  if (signOut)
    signOut.onclick = async () => {
      await staffAuthService.signOut();
      location.hash = 'employee-login';
    };
}
