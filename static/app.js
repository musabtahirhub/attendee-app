

const API_BASE = '/api';

async function apiCall(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const defaultHeaders = { 'Content-Type': 'application/json' };
  const config = {
    headers: { ...defaultHeaders, ...options.headers },
    ...options,
  };

  try {
    const response = await fetch(url, config);

    if (response.status === 204) return null;

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || `HTTP ${response.status}`);
    }

    return data;
  } catch (error) {
    if (error.message.includes('Failed to fetch')) {
      throw new Error('Cannot connect to the server. Is it running?');
    }
    throw error;
  }
}

function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  container.appendChild(toast);

  setTimeout(() => toast.remove(), 3000);
}

function formatTime(dateStr) {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function formatDate(dateStr) {
  if (!dateStr) return '—';
  const d = new Date(dateStr + 'T00:00:00');
  return d.toLocaleDateString([], { year: 'numeric', month: 'short', day: 'numeric' });
}

function todayStr() {
  return new Date().toISOString().split('T')[0];
}

const navItems = document.querySelectorAll('.nav-item');
const tabContents = document.querySelectorAll('.tab-content');

navItems.forEach(item => {
  item.addEventListener('click', () => {
    const tabId = item.dataset.tab;

    navItems.forEach(n => n.classList.remove('active'));
    item.classList.add('active');

    tabContents.forEach(t => t.classList.remove('active'));
    document.getElementById(`tab-${tabId}`).classList.add('active');

    if (tabId === 'dashboard') loadDashboard();
    if (tabId === 'employees') loadEmployees();
    if (tabId === 'attendance') {
      loadEmployeesDropdown();
      loadAttendanceRecords();
    }

    document.getElementById('sidebar').classList.remove('open');
  });
});

document.getElementById('mobileMenuBtn').addEventListener('click', () => {
  document.getElementById('sidebar').classList.toggle('open');
});

async function loadDashboard() {
  try {
    const employees = await apiCall('/employees/');
    document.getElementById('statTotalEmployees').textContent = employees.length;

    const report = await apiCall(`/attendance/report?report_date=${todayStr()}`);
    document.getElementById('statPresent').textContent = report.total_present;
    document.getElementById('statLate').textContent = report.total_late;
    document.getElementById('statAbsent').textContent = report.total_absent;

    const tbody = document.getElementById('dashboardTableBody');
    if (report.records.length === 0) {
      tbody.innerHTML = `
        <tr><td colspan="4">
          <div class="empty-state">
            <div class="empty-icon">&#128203;</div>
            <h4>No records yet</h4>
            <p>Attendance records for today will appear here.</p>
          </div>
        </td></tr>`;
      return;
    }

    tbody.innerHTML = report.records.map(r => `
      <tr>
        <td>${r.employee_id}</td>
        <td>${formatTime(r.check_in)}</td>
        <td>${formatTime(r.check_out)}</td>
        <td><span class="badge ${r.status}">${r.status}</span></td>
      </tr>
    `).join('');
  } catch (err) {
    showToast(err.message, 'error');
  }
}

let allEmployees = [];

async function loadEmployees() {
  try {
    allEmployees = await apiCall('/employees/');
    renderEmployees(allEmployees);
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function renderEmployees(employees) {
  const tbody = document.getElementById('employeesTableBody');

  if (employees.length === 0) {
    tbody.innerHTML = `
      <tr><td colspan="6">
        <div class="empty-state">
          <div class="empty-icon">&#128101;</div>
          <h4>No employees yet</h4>
          <p>Click "Add Employee" to get started.</p>
        </div>
      </td></tr>`;
    return;
  }

  tbody.innerHTML = employees.map(emp => `
    <tr>
      <td>${emp.id}</td>
      <td><strong>${escapeHtml(emp.name)}</strong></td>
      <td>${escapeHtml(emp.email)}</td>
      <td>${emp.department ? escapeHtml(emp.department) : '<span style="color:var(--text-muted)">—</span>'}</td>
      <td>${formatDate(emp.created_at?.split('T')[0])}</td>
      <td>
        <div class="actions-cell">
          <button class="btn-icon" onclick="editEmployee(${emp.id})" title="Edit">&#9998;</button>
          <button class="btn-icon danger" onclick="confirmDeleteEmployee(${emp.id}, '${escapeHtml(emp.name)}')" title="Delete">&#128465;</button>
        </div>
      </td>
    </tr>
  `).join('');
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

document.getElementById('employeeSearch').addEventListener('input', (e) => {
  const q = e.target.value.toLowerCase();
  const filtered = allEmployees.filter(emp =>
    emp.name.toLowerCase().includes(q) ||
    emp.email.toLowerCase().includes(q) ||
    (emp.department || '').toLowerCase().includes(q)
  );
  renderEmployees(filtered);
});

document.getElementById('addEmployeeBtn').addEventListener('click', () => {
  document.getElementById('employeeModalTitle').textContent = 'Add Employee';
  document.getElementById('employeeEditId').value = '';
  document.getElementById('empName').value = '';
  document.getElementById('empEmail').value = '';
  document.getElementById('empDepartment').value = '';
  openModal('employeeModal');
});

async function editEmployee(id) {
  try {
    const emp = await apiCall(`/employees/${id}`);
    document.getElementById('employeeModalTitle').textContent = 'Edit Employee';
    document.getElementById('employeeEditId').value = emp.id;
    document.getElementById('empName').value = emp.name;
    document.getElementById('empEmail').value = emp.email;
    document.getElementById('empDepartment').value = emp.department || '';
    openModal('employeeModal');
  } catch (err) {
    showToast(err.message, 'error');
  }
}

document.getElementById('saveEmployeeBtn').addEventListener('click', async () => {
  const id = document.getElementById('employeeEditId').value;
  const name = document.getElementById('empName').value.trim();
  const email = document.getElementById('empEmail').value.trim();
  const department = document.getElementById('empDepartment').value.trim() || null;

  if (!name || !email) {
    showToast('Name and email are required.', 'error');
    return;
  }

  try {
    if (id) {
      await apiCall(`/employees/${id}`, {
        method: 'PUT',
        body: JSON.stringify({ name, email, department }),
      });
      showToast('Employee updated successfully.', 'success');
    } else {
      await apiCall('/employees/', {
        method: 'POST',
        body: JSON.stringify({ name, email, department }),
      });
      showToast('Employee created successfully.', 'success');
    }
    closeModal('employeeModal');
    loadEmployees();
  } catch (err) {
    showToast(err.message, 'error');
  }
});

let deleteEmployeeId = null;

function confirmDeleteEmployee(id, name) {
  deleteEmployeeId = id;
  document.getElementById('deleteEmployeeName').textContent = name;
  openModal('deleteModal');
}

document.getElementById('confirmDeleteBtn').addEventListener('click', async () => {
  if (!deleteEmployeeId) return;

  try {
    await apiCall(`/employees/${deleteEmployeeId}`, { method: 'DELETE' });
    showToast('Employee deleted.', 'success');
    closeModal('deleteModal');
    deleteEmployeeId = null;
    loadEmployees();
  } catch (err) {
    showToast(err.message, 'error');
  }
});

async function loadEmployeesDropdown() {
  try {
    const employees = await apiCall('/employees/');
    const select = document.getElementById('checkinEmployee');
    select.innerHTML = '<option value="">Select employee...</option>';
    employees.forEach(emp => {
      select.innerHTML += `<option value="${emp.id}">${escapeHtml(emp.name)} (ID: ${emp.id})</option>`;
    });
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function loadActiveCheckoutsDropdown() {
  try {
    const records = await apiCall(`/attendance/?record_date=${todayStr()}`);
    const activeRecords = records.filter(r => !r.check_out);
    const select = document.getElementById('checkoutRecord');
    select.innerHTML = '<option value="">Select active check-in...</option>';
    activeRecords.forEach(r => {
      select.innerHTML += `<option value="${r.id}">Record #${r.id} (Emp ID: ${r.employee_id}) - In: ${formatTime(r.check_in)}</option>`;
    });
  } catch (err) {
  }
}

async function loadAttendanceRecords(dateFilter = null) {
  try {
    let endpoint = '/attendance/';
    if (dateFilter) endpoint += `?record_date=${dateFilter}`;

    const records = await apiCall(endpoint);
    const tbody = document.getElementById('attendanceTableBody');

    loadActiveCheckoutsDropdown();

    if (records.length === 0) {
      tbody.innerHTML = `
        <tr><td colspan="7">
          <div class="empty-state">
            <div class="empty-icon">&#9989;</div>
            <h4>No attendance records</h4>
            <p>Check in an employee to see records here.</p>
          </div>
        </td></tr>`;
      return;
    }

    tbody.innerHTML = records.map(r => `
      <tr>
        <td>${r.id}</td>
        <td>Employee #${r.employee_id}</td>
        <td>${formatDate(r.date)}</td>
        <td>${formatTime(r.check_in)}</td>
        <td>${r.check_out ? formatTime(r.check_out) : '<span style="color:var(--text-muted)">—</span>'}</td>
        <td><span class="badge ${r.status}">${r.status}</span></td>
        <td>
          ${!r.check_out
            ? `<button class="btn btn-primary btn-sm" onclick="checkOut(${r.id})">&#128284; Check Out</button>`
            : '<span style="color:var(--success);font-size:0.8rem;font-weight:600;">✓ Checked Out</span>'
          }
        </td>
      </tr>
    `).join('');
  } catch (err) {
    showToast(err.message, 'error');
  }
}

document.getElementById('checkinBtn').addEventListener('click', async () => {
  const employeeId = document.getElementById('checkinEmployee').value;
  const status = document.getElementById('checkinStatus').value;

  if (!employeeId) {
    showToast('Please select an employee to check in.', 'error');
    return;
  }

  try {
    await apiCall('/attendance/check-in', {
      method: 'POST',
      body: JSON.stringify({ employee_id: parseInt(employeeId), status }),
    });
    showToast('Checked in successfully!', 'success');
    document.getElementById('checkinEmployee').value = '';
    loadAttendanceRecords();
  } catch (err) {
    showToast(err.message, 'error');
  }
});

document.getElementById('checkoutBtn').addEventListener('click', async () => {
  const recordId = document.getElementById('checkoutRecord').value;

  if (!recordId) {
    showToast('Please select an active check-in record to check out.', 'error');
    return;
  }

  await checkOut(recordId);
});

async function checkOut(recordId) {
  try {
    await apiCall(`/attendance/check-out/${recordId}`, { method: 'POST' });
    showToast('Checked out successfully!', 'success');
    loadAttendanceRecords();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

document.getElementById('filterAttendanceBtn').addEventListener('click', () => {
  const date = document.getElementById('attendanceDateFilter').value;
  if (date) loadAttendanceRecords(date);
});

document.getElementById('clearFilterBtn').addEventListener('click', () => {
  document.getElementById('attendanceDateFilter').value = '';
  loadAttendanceRecords();
});

document.getElementById('attendanceDateFilter').value = todayStr();

function openModal(id) {
  document.getElementById(id).classList.add('active');
}

function closeModal(id) {
  document.getElementById(id).classList.remove('active');
}

document.getElementById('closeEmployeeModal').addEventListener('click', () => closeModal('employeeModal'));
document.getElementById('cancelEmployeeModal').addEventListener('click', () => closeModal('employeeModal'));
document.getElementById('closeDeleteModal').addEventListener('click', () => closeModal('deleteModal'));
document.getElementById('cancelDeleteModal').addEventListener('click', () => closeModal('deleteModal'));

document.querySelectorAll('.modal-overlay').forEach(overlay => {
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) overlay.classList.remove('active');
  });
});

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-overlay.active').forEach(m => m.classList.remove('active'));
  }
});

loadDashboard();
