import { store, page } from '../services/store.js';
import { employeeService } from '../services/employeeService.js';
import { $, escapeHTML, dateTime, notify } from '../utils/dom.js';

export function staffTeam(refresh) {
  const employee = employeeService.current();
  const admin = employeeService.isAdmin();
  const branch = employeeService.branch();
  const state = store.read();
  const branchName = state.branches.find((b) => b.id === branch)?.name || branch;
  const shifts = employeeService.shifts(branch);
  const employees = employeeService
    .list()
    .filter((e) => (admin ? e.branchId === branch : e.id === employee.id));
  const activeRoster = employeeService.activeEmployees();
  const active = activeRoster.length;
  const todayStart = new Date();
  todayStart.setHours(0, 0, 0, 0);
  const hoursToday = shifts.reduce((sum, shift) => {
    const start = Math.max(new Date(shift.clockIn).getTime(), todayStart.getTime());
    const end = Math.min(new Date(shift.clockOut || Date.now()).getTime(), Date.now());
    return sum + Math.max(0, end - start) / 3600000;
  }, 0);
  const currentShift =
    shifts.find((s) => s.employeeId === employee.id && !s.clockOut) ||
    state.shifts.find((s) => s.employeeId === employee.id && !s.clockOut);
  let pageNumber = 1;
  return {
    html: `<section class="section compact staff-content">
      <div class="section-heading"><div><p class="eyebrow">THE PEOPLE BEHIND THE PIZZA</p>
        <h1>${admin ? 'Team & time.' : 'My shifts.'}</h1>
        <p class="muted">${admin ? 'Review and verify clock-in and clock-out records by branch.' : 'Your clock-in, clock-out, and hours worked.'}</p></div>
        <button class="button" id="clock-toggle">${currentShift ? 'Clock out' : 'Clock in'} · ${escapeHTML(employee.firstName)}</button></div>
      ${
        admin
          ? `<div class="filters"><div><label for="team-review-branch">Branch to review</label>
        <select id="team-review-branch">${state.branches.map((b) => `<option value="${b.id}" ${b.id === branch ? 'selected' : ''}>${escapeHTML(b.name)}</option>`).join('')}</select></div></div>`
          : ''
      }
      <div class="kpi-grid three">
        <article class="kpi"><span>${admin ? 'Currently clocked in' : 'Your active shifts'}</span><strong>${active}</strong>
          <small>${admin ? 'All branches' : 'Only your records'}</small>
          <details class="clocked-in-roster"><summary>${admin ? 'See who’s clocked in' : 'See your active shift'}</summary>
            ${activeRoster.length ? `<ul>${activeRoster.map((person) => `<li><strong>${escapeHTML(person.name)}</strong><span>${escapeHTML(person.branchName)}</span><small>Clocked in ${dateTime(person.clockIn)}</small></li>`).join('')}</ul>` : `<p>${admin ? 'No employees are currently clocked in.' : 'You are currently clocked out.'}</p>`}
          </details>
        </article>
        <article class="kpi"><span>${admin ? 'Branch hours worked today' : 'Your hours worked today'}</span><strong>${hoursToday.toFixed(2)}</strong><small>Includes active shifts</small></article>
        <article class="kpi"><span>Your status</span><strong class="text-kpi">${currentShift ? 'On shift' : 'Off shift'}</strong><small>${currentShift ? 'Since ' + dateTime(currentShift.clockIn) : 'Ready when you are'}</small></article>
      </div>
      ${admin ? `<section class="panel"><h2>${escapeHTML(branchName)} team</h2><div class="table-wrap"><table><thead><tr><th>Employee</th><th>Position</th><th>Status</th></tr></thead><tbody>${employees.map((e) => `<tr><td>${escapeHTML(e.firstName + ' ' + e.lastName)}</td><td>${escapeHTML(e.position)}</td><td>${escapeHTML(e.status)}</td></tr>`).join('')}</tbody></table></div></section>` : ''}
      <section class="panel"><h2>${admin ? escapeHTML(branchName) + ' shift records' : 'Your shift records'}</h2><div id="shift-records"></div></section>
    </section>`,
    mount() {
      function renderRecords() {
        const result = page(employeeService.shifts(branch), pageNumber);
        const directory = employeeService.list();
        $('#shift-records').innerHTML =
          `<div class="table-wrap"><table><caption class="sr-only">${admin ? 'Branch' : 'Personal'} clock-in and clock-out records</caption>
          <thead><tr><th>Employee / date</th><th>Clock in</th><th>Clock out</th><th>Hours worked</th><th>Branch</th><th>Verification</th></tr></thead>
          <tbody>${
            result.items
              .map((shift) => {
                const person = directory.find((e) => e.id === shift.employeeId);
                const reviewer = directory.find((e) => e.id === shift.verifiedBy);
                const location = state.branches.find((b) => b.id === shift.branchId);
                const hours = Math.max(
                  0,
                  (new Date(shift.clockOut || Date.now()) - new Date(shift.clockIn)) / 3600000,
                );
                return `<tr><td>${escapeHTML(person?.firstName + ' ' + person?.lastName)}<small>${new Date(shift.clockIn).toLocaleDateString()}</small></td>
              <td>${dateTime(shift.clockIn)}</td><td>${shift.clockOut ? dateTime(shift.clockOut) : 'Still clocked in'}</td><td>${hours.toFixed(2)}</td><td>${escapeHTML(location?.name || shift.branchId)}</td>
              <td>${shift.verifiedAt ? `Verified by ${escapeHTML(reviewer?.firstName || 'administrator')}<small>${dateTime(shift.verifiedAt)}</small>` : admin && shift.clockOut ? `<button class="button small secondary" data-verify-shift="${shift.id}">Verify shift</button>` : shift.clockOut ? 'Awaiting verification' : 'Active shift'}</td></tr>`;
              })
              .join('') || '<tr><td colspan="6">No shift records yet.</td></tr>'
          }</tbody></table></div>
          <div class="pagination"><span>${result.total} shifts · page ${result.page} of ${result.pages}</span><div>
            <button class="button small secondary" data-shift-page="${result.page - 1}" ${result.page <= 1 ? 'disabled' : ''}>Previous</button>
            <button class="button small secondary" data-shift-page="${result.page + 1}" ${result.page >= result.pages ? 'disabled' : ''}>Next</button></div></div>`;
      }
      $('#clock-toggle').onclick = async () => {
        try {
          notify(await employeeService.toggleClock());
          refresh();
        } catch (error) {
          notify(error.message);
        }
      };
      if (admin)
        $('#team-review-branch').onchange = (event) => {
          employeeService.setBranch(event.target.value);
          refresh();
        };
      $('#shift-records').onclick = async (event) => {
        const button = event.target.closest('button');
        if (!button) return;
        if (button.dataset.shiftPage) {
          pageNumber = Number(button.dataset.shiftPage);
          renderRecords();
        }
        if (button.dataset.verifyShift) {
          try {
            await employeeService.verifyShift(button.dataset.verifyShift);
            renderRecords();
            notify('Shift verified.');
          } catch (error) {
            notify(error.message);
          }
        }
      };
      renderRecords();
    },
  };
}
