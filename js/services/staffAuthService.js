// Demonstration credentials requested for the class project, not a secret.
// Production must replace this entire check with server authentication and
// server-enforced authorization on every staff API request.
const SESSION_KEY = 'luigis-staff-demo-session';
import { apiClient } from './apiClient.js';
import { store } from './store.js';
let memorySession = false;

export function staffDestination(value) {
  const routes = [
    'staff',
    'staff/orders',
    'staff/inventory',
    'staff/team',
    'staff/support',
    'staff/promotions',
  ];
  return routes.includes(value) ? value : 'staff';
}

export const staffAuthService = {
  isSignedIn() {
    if (apiClient.enabled()) return ['staff', 'admin'].includes(apiClient.user()?.role);
    try {
      return memorySession || globalThis.sessionStorage?.getItem(SESSION_KEY) === 'signed-in';
    } catch {
      return memorySession;
    }
  },
  signIn(username, password) {
    if (apiClient.enabled())
      return apiClient.login(username, password).then(async (user) => {
        if (!['staff', 'admin'].includes(user.role)) {
          await apiClient.logout();
          store.clearSession();
          throw new Error('Use an employee account for the staff workspace.');
        }
        return user;
      });
    if (String(username).trim() !== 'Luigi' || password !== 'Pizza') {
      throw new Error('Incorrect username or password. Please try again.');
    }
    memorySession = true;
    try {
      globalThis.sessionStorage?.setItem(SESSION_KEY, 'signed-in');
    } catch {
      // Storage-disabled browsers retain the demo session until page reload.
    }
  },
  signOut() {
    if (apiClient.enabled()) return apiClient.logout().then(() => store.clearSession());
    memorySession = false;
    try {
      globalThis.sessionStorage?.removeItem(SESSION_KEY);
    } catch {
      // The in-memory fallback is already cleared.
    }
  },
};
