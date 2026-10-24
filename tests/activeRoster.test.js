import test from 'node:test';
import assert from 'node:assert/strict';
import { store } from '../js/services/store.js';
import { employeeService } from '../js/services/employeeService.js';
import { staffTeam } from '../js/components/teamTime.js';

test('admin clocked-in count includes all branches and roster identifies each location', () => {
  store.reset();
  const roster = employeeService.activeEmployees();
  assert.equal(roster.length, 2);
  assert.equal(roster.find((person) => person.employeeId === 'e2').branchName, 'Downtown');
  assert.equal(roster.find((person) => person.employeeId === 'e3').branchName, 'Riverside');
  let html = staffTeam(() => {}).html;
  assert.match(html, /Currently clocked in<\/span><strong>2<\/strong>/);
  assert.match(html, /<small>All branches<\/small>/);
  assert.doesNotMatch(html, /All branches ·/);
  assert.match(html, /Robin Demo/);
  assert.match(html, /See who’s clocked in/);
  employeeService.setBranch('riverside');
  html = staffTeam(() => {}).html;
  assert.match(html, /Currently clocked in<\/span><strong>2<\/strong>/);
  assert.match(html, /<small>All branches<\/small>/);
});

test('clocking out updates the roster and total together', () => {
  store.reset();
  employeeService.select('e2');
  employeeService.toggleClock();
  employeeService.select('e1');
  assert.deepEqual(employeeService.activeEmployees().map((person) => person.employeeId), ['e3']);
  const html = staffTeam(() => {}).html;
  assert.match(html, /Currently clocked in<\/span><strong>1<\/strong>/);
  assert.match(html, /<small>All branches<\/small>/);
});

test('employee roster contains only their own shift and handles clocked-out state', () => {
  store.reset();
  employeeService.select('e2');
  assert.deepEqual(employeeService.activeEmployees().map((person) => person.employeeId), ['e2']);
  assert.doesNotMatch(staffTeam(() => {}).html, /Robin Demo|All branches/);
  employeeService.toggleClock();
  assert.deepEqual(employeeService.activeEmployees(), []);
  assert.match(staffTeam(() => {}).html, /You are currently clocked out/);
});
