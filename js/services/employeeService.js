import { store, uid } from './store.js';
import { apiClient } from './apiClient.js';
export const employeeService = {
  current: () => {
    const s = store.read();
    return s.employees.find((e) => e.id === s.staffEmployeeId);
  },
  list: () => store.read().employees,
  select(id) {
    if (apiClient.enabled()) {
      const employee = store.read().employees.find((e) => e.id === id);
      if (employee?.apiUserId !== apiClient.user()?.id)
        throw new Error('Sign in with that employee’s account to switch identity.');
    }
    store.transact((s) => {
      const e = s.employees.find((e) => e.id === id);
      if (!e) throw new Error('Employee not found');
      s.staffEmployeeId = id;
      s.branchId = e.branchId;
    });
  },
  branch() {
    return store.read().branchId;
  },
  setBranch(id) {
    store.transact((s) => {
      const e = s.employees.find((e) => e.id === s.staffEmployeeId);
      if (e.role !== 'Administrator')
        throw new Error('Only an administrator can select another branch in this demo.');
      if (!s.branches.some((b) => b.id === id)) throw new Error('Branch not found');
      s.branchId = id;
    });
  },
  isAdmin: () => employeeService.current().role === 'Administrator',
  shifts(branchId) {
    const employee = this.current();
    return store
      .read()
      .shifts.filter((shift) =>
        employee.role === 'Administrator'
          ? !branchId || shift.branchId === branchId
          : shift.employeeId === employee.id,
      )
      .sort((a, b) => new Date(b.clockIn) - new Date(a.clockIn));
  },
  verifyShift(id) {
    if (apiClient.enabled()) return apiClient.command('verify', { id });
    if (!this.isAdmin()) throw new Error('Only an administrator can verify shifts.');
    store.transact((state) => {
      const shift = state.shifts.find((s) => s.id === id);
      if (!shift) throw new Error('Shift not found.');
      if (!shift.clockOut) throw new Error('Clock out before this shift can be verified.');
      shift.verifiedBy = state.staffEmployeeId;
      shift.verifiedAt = new Date().toISOString();
    });
  },
  activeEmployees(branchId) {
    const state = store.read();
    const roster = new Map();
    // shifts() enforces the demo role scope: all branches for admins,
    // only the signed-in employee's records for branch employees.
    for (const shift of this.shifts(branchId)) {
      if (shift.clockOut || roster.has(shift.employeeId)) continue;
      const person = state.employees.find((e) => e.id === shift.employeeId);
      const branch = state.branches.find((b) => b.id === shift.branchId);
      roster.set(shift.employeeId, {
        employeeId: shift.employeeId,
        name: person ? person.firstName + ' ' + person.lastName : 'Unknown employee',
        branchId: shift.branchId,
        branchName: branch?.name || shift.branchId,
        clockIn: shift.clockIn,
      });
    }
    return [...roster.values()];
  },
  toggleClock() {
    if (apiClient.enabled()) return apiClient.command('clock', {});
    return store.transact((s) => {
      const e = s.employees.find((e) => e.id === s.staffEmployeeId);
      const active = s.shifts.find((x) => x.employeeId === e.id && !x.clockOut);
      if (active) {
        active.clockOut = new Date().toISOString();
        return 'Clocked out.';
      }
      s.shifts.unshift({
        id: uid('shift'),
        employeeId: e.id,
        branchId: e.branchId,
        clockIn: new Date().toISOString(),
        clockOut: null,
      });
      return 'Clocked in.';
    });
  },
};
