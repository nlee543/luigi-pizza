import { employeeService } from './employeeService.js';
// Demonstration role policy. Real enforcement belongs to the backend API.
export function staffLinks() {
  return [
    ...(employeeService.isAdmin() ? [['staff', 'Overview']] : []),
    ['staff/orders', 'Order queue'],
    ['staff/inventory', 'Inventory'],
    ['staff/team', employeeService.isAdmin() ? 'Team & time' : 'My shifts'],
    ['staff/support', 'Support tickets'],
    ...(employeeService.isAdmin() ? [['staff/promotions', 'Promotions']] : []),
  ];
}
export function allowedStaffRoute(route) {
  return !employeeService.isAdmin() && (route === 'staff' || route === 'staff/promotions')
    ? 'staff/orders'
    : route;
}
export function requireAdmin() {
  if (!employeeService.isAdmin())
    throw new Error('Administrator access is required for revenue and analytics.');
}
