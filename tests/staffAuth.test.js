import test from 'node:test';
import assert from 'node:assert/strict';
import { staffAuthService, staffDestination } from '../js/services/staffAuthService.js';
import { staffLogin } from '../js/components/staffLogin.js';

test('employee demo requires the requested credentials and supports sign-out', () => {
  staffAuthService.signOut();
  assert.equal(staffAuthService.isSignedIn(), false);
  assert.throws(() => staffAuthService.signIn('Luigi', 'wrong'), /Incorrect/);
  assert.throws(() => staffAuthService.signIn('Other', 'Pizza'), /Incorrect/);
  assert.equal(staffAuthService.isSignedIn(), false);
  staffAuthService.signIn('Luigi', 'Pizza');
  assert.equal(staffAuthService.isSignedIn(), true);
  staffAuthService.signOut();
  assert.equal(staffAuthService.isSignedIn(), false);
});

test('login redirects only to known staff routes and uses a labeled password field', () => {
  assert.equal(staffDestination('staff/inventory'), 'staff/inventory');
  assert.equal(staffDestination('https://example.com'), 'staff');
  assert.equal(staffDestination('home'), 'staff');
  const html = staffLogin(new URLSearchParams()).html;
  assert.match(html, /type="password"/);
  assert.match(html, /autocomplete="current-password"/);
  assert.match(html, /for="staff-username"/);
  assert.match(html, /secure server authentication/);
});
