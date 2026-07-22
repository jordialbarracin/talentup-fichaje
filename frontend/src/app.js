/* ===================================================================
   TalentUP Fichaje v2.0 — Frontend SPA
   =================================================================== */

// ===== STATE =====
let state = {
  user: null,
  employees: [],
  shifts: [],
  schedules: [],
  clockHistory: [],
  overtime: [],
  vacations: [],
  leaves: [],
  holidays: [],
  currentPage: 'dashboard',
  isOnline: true,
  isDemo: false,
  calendarDate: new Date(),
  calendarView: 'month',
  empPage: 1,
  clockPage: 1,
  empFiltered: [],
  clockFiltered: [],
  leaveFiltered: [],
  empSearch: '',
  empFilterStatus: '',
  empFilterTurno: '',
  clockFilterEmpleado: '',
  clockFilterTipo: '',
  clockFilterEstado: '',
  clockFilterDate: '',
  leaveFilterStatus: '',
  leaveFilterType: '',
  vacFilterSearch: '',
  vacFilterStatus: '',
  vacFiltered: [],
  vacPage: 1,
  leavePage: 1,
  pendingConfirm: null
};

const API_BASE = window.location.hostname === 'localhost'
  ? 'http://localhost:8000/api'
  : '/api';
const PAGE_SIZE = 20;

// Show demo button only on localhost
(function showDemoButtonIfLocalhost() {
  const host = window.location.hostname;
  if (host === 'localhost' || host === '127.0.0.1') {
    const demoBtn = document.getElementById('demo-btn');
    if (demoBtn) demoBtn.classList.remove('hidden');
  }
})();

const EMPTY_ICON = '<svg class="empty-state-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="9" y1="9" x2="15" y2="15"/><line x1="15" y1="9" x2="9" y2="15"/></svg>';

const LOADING_ROW = (cols, text) => `<tr><td colspan="${cols}" class="empty-state"><span class="spinner spinner-lg"></span><div class="empty-state-title" style="margin-top:8px">${text}</div></td></tr>`;
const EMPTY_ROW = (cols, title, desc) => `<tr><td colspan="${cols}" class="empty-state">${EMPTY_ICON}<div class="empty-state-title">${title}</div><div class="empty-state-desc">${desc}</div></td></tr>`;

// ===== API HELPER =====
async function api(method, path, body) {
  const url = `${API_BASE}${path}`;
  const opts = { method, credentials: 'include', headers: { 'Content-Type': 'application/json' } };
  if (body) opts.body = JSON.stringify(body);
  try {
    const res = await fetch(url, opts);
    if (res.status === 401) { logout(); return null; }
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `HTTP ${res.status}`);
    }
    state.isOnline = true;
    updateOnlineStatus();
    return await res.json();
  } catch(e) {
    console.warn(`API ${method} ${path} failed:`, e.message);
    if (e.message.includes('Failed to fetch') || e.message.includes('NetworkError') || e.message.includes('ERR_CONNECTION')) {
      state.isOnline = false;
      updateOnlineStatus();
    }
    return null;
  }
}

// ===== ONLINE/OFFLINE INDICATOR =====
function updateOnlineStatus() {
  const el = document.getElementById('online-indicator');
  const text = document.getElementById('online-text');
  if (state.isOnline && !state.isDemo) {
    el.className = 'online-indicator';
    text.textContent = 'Conectado';
  } else if (state.isDemo) {
    el.className = 'online-indicator offline';
    text.textContent = 'Demo';
  } else {
    el.className = 'online-indicator offline';
    text.textContent = 'Sin conexión';
  }
}

// ===== DEMO BANNER =====
function updateDemoBanner() {
  const banner = document.getElementById('demo-banner');
  if (state.isDemo) {
    banner.classList.remove('hidden');
  } else {
    banner.classList.add('hidden');
  }
}

// ===== TOAST =====
function showToast(message, type = 'error') {
  const container = document.getElementById('toast-container');
  const icons = {
    error: createSvgIcon('error'),
    success: createSvgIcon('success'),
    warning: createSvgIcon('warning'),
    info: createSvgIcon('info')
  };
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.appendChild(icons[type] || icons.error);
  const msg = document.createElement('span');
  msg.textContent = message;
  toast.appendChild(msg);
  container.appendChild(toast);
  setTimeout(() => {
    toast.classList.add('toast-out');
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

function createSvgIcon(type) {
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('class', 'toast-icon');
  svg.setAttribute('viewBox', '0 0 24 24');
  svg.setAttribute('fill', 'none');
  svg.setAttribute('stroke', 'currentColor');
  svg.setAttribute('stroke-width', '2');
  svg.setAttribute('stroke-linecap', 'round');
  if (type === 'error') {
    svg.innerHTML = '<circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>';
  } else if (type === 'success') {
    svg.innerHTML = '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>';
  } else if (type === 'warning') {
    svg.innerHTML = '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>';
  } else {
    svg.innerHTML = '<circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>';
  }
  return svg;
}

// ===== JWT HELPERS =====
function decodeJwt(token) {
  try {
    const payload = token.split('.')[1];
    return JSON.parse(atob(payload.replace(/-/g, '+').replace(/_/g, '/')));
  } catch { return null; }
}
function isTokenExpired(token) {
  const payload = decodeJwt(token);
  if (!payload || !payload.exp) return false;
  return Date.now() >= payload.exp * 1000;
}

// Cookie helper for httpOnly access_token cookie
function getCookie(name) {
  const match = document.cookie.match(new RegExp('(?:^|; )' + name.replace(/([$?*|{}()[\]\\/+^])/g, '\\$1') + '=([^;]*)'));
  return match ? decodeURIComponent(match[1]) : null;
}
function getInitialToken() {
  return getCookie('access_token');
}

// ===== NAVIGATION =====
function navigate(page) {
  state.currentPage = page;
  document.querySelectorAll('.nav-item[data-page]').forEach(el => {
    el.classList.toggle('active', el.dataset.page === page);
  });
  const titles = {
    dashboard:'Dashboard', empleados:'Empleados', calendario:'Calendario',
    turnos:'Turnos', fichajes:'Fichajes', vacaciones:'Vacaciones',
    bajas:'Bajas', informes:'Informes', configuracion:'Configuración'
  };
  document.getElementById('navbar-title').textContent = titles[page] || 'Dashboard';
  document.querySelectorAll('.page-content[id^="page-"]').forEach(el => el.classList.add('hidden'));
  const target = document.getElementById(`page-${page}`);
  if (target) target.classList.remove('hidden');
  document.getElementById('sidebar').classList.remove('open');
  switch(page) {
    case 'dashboard': loadDashboard(); break;
    case 'empleados': loadEmpleados(); break;
    case 'calendario': renderCalendar(); break;
    case 'turnos': loadTurnos(); break;
    case 'fichajes': loadFichajes(); break;
    case 'vacaciones': loadVacaciones(); break;
    case 'bajas': loadBajas(); break;
    case 'informes': initReports(); break;
    case 'configuracion': loadSettings(); break;
  }
}

// ===== LOGIN =====
document.getElementById('login-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const email = document.getElementById('login-email').value.trim();
  const password = document.getElementById('login-password').value;
  const errorEl = document.getElementById('login-error');
  const btn = document.getElementById('login-btn');
  const btnText = document.getElementById('login-btn-text');
  const spinner = document.getElementById('login-spinner');
  errorEl.textContent = '';

  if (!email || !password) {
    errorEl.textContent = 'Completa todos los campos';
    return;
  }

  // Show loading
  btn.disabled = true;
  btnText.textContent = 'Iniciando sesión…';
  spinner.classList.remove('hidden');

  const result = await api('POST', '/auth/login', { email, password });

  btn.disabled = false;
  btnText.textContent = 'Iniciar sesión';
  spinner.classList.add('hidden');

  if (result && result.ok && result.user) {
    state.user = result.user;
    state.isDemo = false;
    enterApp();
  } else {
    // Only real credentials work — no mock fallback
    errorEl.textContent = result && result.detail ? result.detail : 'Credenciales incorrectas. Verifica tu email y contraseña.';
  }
});

// ===== DEMO LOGIN (temporal — quitar después) =====
document.getElementById('demo-btn').addEventListener('click', () => {
  state.user = { name: 'Demo', email: 'demo@talentup.es', role: 'owner', tenant_id: 'demo' };
  state.isDemo = true;
  enterApp();
});

// ===== REGISTER MODAL =====
document.getElementById('register-link').addEventListener('click', () => {
  const modal = document.getElementById('register-modal');
  modal.style.display = 'flex';
  modal.classList.remove('hidden');
});

function closeRegisterModal() {
  const modal = document.getElementById('register-modal');
  modal.style.display = 'none';
  modal.classList.add('hidden');
  document.getElementById('register-error').textContent = '';
}

// Close register modal on overlay click
document.getElementById('register-modal').addEventListener('click', (e) => {
  if (e.target === e.currentTarget) closeRegisterModal();
});

// Register form submit
document.getElementById('register-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const restaurantName = document.getElementById('reg-restaurant').value.trim();
  const ownerName = document.getElementById('reg-name').value.trim();
  const email = document.getElementById('reg-email').value.trim();
  const password = document.getElementById('reg-password').value;
  const phone = document.getElementById('reg-phone').value.trim();
  const errorEl = document.getElementById('register-error');
  const btn = document.getElementById('register-btn');
  const btnText = document.getElementById('register-btn-text');
  const spinner = document.getElementById('register-spinner');

  errorEl.textContent = '';

  if (!restaurantName || !ownerName || !email || !password) {
    errorEl.textContent = 'Completa todos los campos obligatorios';
    return;
  }
  if (password.length < 6) {
    errorEl.textContent = 'La contraseña debe tener al menos 6 caracteres';
    return;
  }

  btn.disabled = true;
  btnText.textContent = 'Creando cuenta...';
  spinner.classList.remove('hidden');

  const result = await api('POST', '/auth/register', {
    restaurant_name: restaurantName,
    owner_name: ownerName,
    email: email,
    password: password,
    phone: phone || undefined
  });

  btn.disabled = false;
  btnText.textContent = 'Crear cuenta';
  spinner.classList.add('hidden');

  if (result && result.ok && result.user) {
    state.user = result.user;
    state.isDemo = false;
    state.isNewTenant = result.is_new_tenant || false;
    state.tenantId = result.tenant_id;
    closeRegisterModal();
    enterApp();
    // Show onboarding wizard for new tenants
    if (state.isNewTenant) {
      setTimeout(() => openOnboarding(), 500);
    }
  } else {
    errorEl.textContent = result && result.detail ? result.detail : 'Error al crear la cuenta. Intentalo de nuevo.';
  }
});

// ===== ONBOARDING WIZARD =====
let onbTempEmployees = [];

function openOnboarding() {
  const modal = document.getElementById('onboarding-modal');
  modal.style.display = 'flex';
  modal.classList.remove('hidden');

  // Pre-fill step 1 with registration data
  const regName = document.getElementById('reg-restaurant').value.trim();
  const regPhone = document.getElementById('reg-phone').value.trim();
  document.getElementById('onb-name').value = regName || '';
  document.getElementById('onb-phone').value = regPhone || '';

  // Reset to step 1
  onbGoToStep(1);
  onbTempEmployees = [];
  loadOnbShifts();
}

function closeOnboarding() {
  const modal = document.getElementById('onboarding-modal');
  modal.style.display = 'none';
  modal.classList.add('hidden');
  onbTempEmployees = [];
}

function onbGoToStep(step) {
  // Update indicators
  document.querySelectorAll('.onb-step-indicator').forEach(el => {
    const s = parseInt(el.dataset.step);
    el.style.background = s <= step ? '#FF6B35' : 'rgba(0,0,0,0.08)';
  });
  // Show/hide steps
  document.querySelectorAll('.onb-step').forEach(el => {
    el.classList.toggle('hidden', parseInt(el.dataset.step) !== step);
  });
}

async function onbNext(currentStep) {
  if (currentStep === 1) {
    // Save restaurant config
    const name = document.getElementById('onb-name').value.trim();
    const address = document.getElementById('onb-address').value.trim();
    const phone = document.getElementById('onb-phone').value.trim();
    if (name) {
      await api('PUT', '/settings', { name, address, phone });
    }
    onbGoToStep(2);
    loadOnbShifts();
  } else if (currentStep === 2) {
    onbGoToStep(3);
  }
}

function initOnboardingListeners() {
  document.querySelectorAll('.onb-skip').forEach(btn => {
    btn.addEventListener('click', closeOnboarding);
  });
  document.querySelectorAll('.onb-next').forEach(btn => {
    btn.addEventListener('click', () => onbNext(parseInt(btn.dataset.step)));
  });
  const addEmpBtn = document.getElementById('onb-add-employee');
  if (addEmpBtn) addEmpBtn.addEventListener('click', onbAddEmployee);
  const finishBtn = document.getElementById('onb-finish');
  if (finishBtn) finishBtn.addEventListener('click', finishOnboarding);
}

function onbAddEmployee() {
  const container = document.getElementById('onb-employees-list');
  const idx = onbTempEmployees.length;
  const row = document.createElement('div');
  row.className = 'onb-emp-row';
  row.dataset.idx = idx;
  row.style.cssText = 'background:#f5f5f7;border-radius:8px;padding:10px 12px';
  row.innerHTML = `
    <div style="display:grid;grid-template-columns:1fr 1fr 80px 24px;gap:6px;align-items:center">
      <input type="text" class="onb-emp-name" placeholder="Nombre" style="font-size:0.8125rem;padding:6px 8px">
      <input type="text" class="onb-emp-dni" placeholder="DNI" style="font-size:0.8125rem;padding:6px 8px">
      <input type="text" class="onb-emp-pin" placeholder="PIN" maxlength="4" style="font-size:0.8125rem;padding:6px 8px;font-family:monospace">
      <button class="btn btn-ghost btn-sm onb-emp-remove" data-idx="${idx}" style="color:#FF3B30;padding:4px">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
      </button>
    </div>`;
  container.appendChild(row);
  row.querySelector('.onb-emp-remove').addEventListener('click', () => onbRemoveEmployee(idx));
  onbTempEmployees.push({ idx });
}

function initOnbShiftListeners(container) {
  container.querySelectorAll('.onb-shift-edit').forEach(btn => {
    btn.addEventListener('click', () => onbEditShift(btn.dataset.shiftId));
  });
}

async function loadOnbShifts() {
  const container = document.getElementById('onb-shifts-list');
  let shifts = await api('GET', '/shifts');
  if (!shifts || shifts.length === 0) {
    container.textContent = 'No hay turnos configurados';
    container.className = 'text-muted text-sm';
    container.style.cssText = 'padding:12px;text-align:center';
    return;
  }
  container.innerHTML = '';
  shifts.forEach(s => {
    const start = s.start_time || s.start || '--:--';
    const end = s.end_time || s.end || '--:--';
    const card = document.createElement('div');
    card.style.cssText = 'display:flex;align-items:center;justify-content:space-between;background:#f5f5f7;border-radius:8px;padding:10px 12px';
    card.innerHTML = `
      <div>
        <div style="font-weight:500;font-size:0.875rem;color:#1d1d1f">${s.name}</div>
        <div style="font-size:0.75rem;color:rgba(0,0,0,0.45)">${start} — ${end}</div>
      </div>
      <div style="display:flex;gap:6px">
        <button class="btn btn-ghost btn-sm onb-shift-edit" data-shift-id="${s.id}">Editar</button>
      </div>`;
    container.appendChild(card);
  });
  initOnbShiftListeners(container);
}

function onbRemoveEmployee(idx) {
  const row = document.querySelector(`.onb-emp-row[data-idx="${idx}"]`);
  if (row) row.remove();
  onbTempEmployees = onbTempEmployees.filter(e => e.idx !== idx);
}

async function finishOnboarding() {
  // Save any employees added
  const rows = document.querySelectorAll('.onb-emp-row');
  let saved = 0;
  for (const row of rows) {
    const name = row.querySelector('.onb-emp-name').value.trim();
    const dni = row.querySelector('.onb-emp-dni').value.trim();
    const pin = row.querySelector('.onb-emp-pin').value.trim();
    if (name && pin) {
      const body = { name, dni: dni || undefined, pin };
      const result = await api('POST', '/employees', body);
      if (result) saved++;
    }
  }

  // Mark tenant setup as completed
  await api('PUT', '/settings', { setup_completed: true });

  closeOnboarding();
  if (saved > 0) {
    showToast(`${saved} empleado(s) anadido(s) correctamente`, 'success');
  } else {
    showToast('Configuracion completada', 'success');
  }
  // Refresh dashboard
  navigate('dashboard');
}

function enterApp() {
  document.getElementById('login-screen').classList.add('hidden');
  document.getElementById('app').classList.remove('hidden');
  const initial = (state.user.name || state.user.email || 'A')[0].toUpperCase();
  document.getElementById('navbar-avatar').textContent = initial;
  document.getElementById('navbar-name').textContent = state.user.name || state.user.email;
  updateOnlineStatus();
  updateDemoBanner();
  navigate('dashboard');
}

// ===== LOGOUT =====
async function logout() {
  try {
    await fetch(`${API_BASE}/auth/logout`, { method: 'POST', credentials: 'include' });
  } catch (e) {
    console.warn('Logout request failed:', e.message);
  }
  state.user = null;
  state.isDemo = false;
  document.getElementById('app').classList.add('hidden');
  document.getElementById('login-screen').classList.remove('hidden');
  document.getElementById('login-email').value = '';
  document.getElementById('login-password').value = '';
  document.getElementById('login-error').textContent = '';
}
document.getElementById('navbar-logout').addEventListener('click', logout);
document.getElementById('sidebar-logout').addEventListener('click', logout);

// ===== SIDEBAR NAV =====
document.querySelectorAll('.nav-item[data-page]').forEach(el => {
  el.addEventListener('click', () => navigate(el.dataset.page));
});

// ===== HAMBURGER =====
document.getElementById('hamburger-btn').addEventListener('click', () => {
  document.getElementById('sidebar').classList.toggle('open');
});

function bindStaticEventListeners() {
  // Register modal close
  const registerModalClose = document.getElementById('register-modal-close');
  if (registerModalClose) registerModalClose.addEventListener('click', closeRegisterModal);

  // Onboarding listeners
  initOnboardingListeners();

  // Page buttons
  const addEmployeeBtn = document.getElementById('btn-add-employee');
  if (addEmployeeBtn) addEmployeeBtn.addEventListener('click', () => openModal('empleado'));

  const empSearch = document.getElementById('emp-search');
  const empFilterStatus = document.getElementById('emp-filter-status');
  const empFilterTurno = document.getElementById('emp-filter-turno');
  if (empSearch) empSearch.addEventListener('input', filterEmpleados);
  if (empFilterStatus) empFilterStatus.addEventListener('change', filterEmpleados);
  if (empFilterTurno) empFilterTurno.addEventListener('change', filterEmpleados);

  const btnCalWeek = document.getElementById('btn-cal-week');
  const btnCalMonth = document.getElementById('btn-cal-month');
  const btnCalPrev = document.getElementById('btn-cal-prev');
  const btnCalNext = document.getElementById('btn-cal-next');
  const btnCalToday = document.getElementById('btn-cal-today');
  if (btnCalWeek) btnCalWeek.addEventListener('click', () => calendarView('week'));
  if (btnCalMonth) btnCalMonth.addEventListener('click', () => calendarView('month'));
  if (btnCalPrev) btnCalPrev.addEventListener('click', () => calendarNav(-1));
  if (btnCalNext) btnCalNext.addEventListener('click', () => calendarNav(1));
  if (btnCalToday) btnCalToday.addEventListener('click', calendarToday);

  const addShiftBtn = document.getElementById('btn-add-shift');
  if (addShiftBtn) addShiftBtn.addEventListener('click', () => openModal('turno'));

  const clockFilterEmpleado = document.getElementById('clock-filter-empleado');
  const clockFilterTipo = document.getElementById('clock-filter-tipo');
  const clockFilterEstado = document.getElementById('clock-filter-estado');
  const clockFilterDate = document.getElementById('clock-filter-date');
  if (clockFilterEmpleado) clockFilterEmpleado.addEventListener('change', filterFichajes);
  if (clockFilterTipo) clockFilterTipo.addEventListener('change', filterFichajes);
  if (clockFilterEstado) clockFilterEstado.addEventListener('change', filterFichajes);
  if (clockFilterDate) clockFilterDate.addEventListener('change', filterFichajes);

  const addVacationBtn = document.getElementById('btn-add-vacation');
  if (addVacationBtn) addVacationBtn.addEventListener('click', () => openModal('vacacion'));
  const vacSearch = document.getElementById('vac-search');
  const vacFilterStatus = document.getElementById('vac-filter-status');
  if (vacSearch) vacSearch.addEventListener('input', filterVacaciones);
  if (vacFilterStatus) vacFilterStatus.addEventListener('change', filterVacaciones);

  const addLeaveBtn = document.getElementById('btn-add-leave');
  if (addLeaveBtn) addLeaveBtn.addEventListener('click', () => openModal('baja'));
  const leaveSearch = document.getElementById('leave-search');
  const leaveFilterStatus = document.getElementById('leave-filter-status');
  const leaveFilterType = document.getElementById('leave-filter-type');
  if (leaveSearch) leaveSearch.addEventListener('input', filterBajas);
  if (leaveFilterStatus) leaveFilterStatus.addEventListener('change', filterBajas);
  if (leaveFilterType) leaveFilterType.addEventListener('change', filterBajas);

  const reportType = document.getElementById('report-type');
  const btnLoadReports = document.getElementById('btn-load-reports');
  const btnExportPdf = document.getElementById('btn-export-pdf');
  const btnExportExcel = document.getElementById('btn-export-excel');
  if (reportType) reportType.addEventListener('change', loadReports);
  if (btnLoadReports) btnLoadReports.addEventListener('click', loadReports);
  if (btnExportPdf) btnExportPdf.addEventListener('click', () => exportReport('pdf'));
  if (btnExportExcel) btnExportExcel.addEventListener('click', () => exportReport('excel'));

  const btnSaveRestaurant = document.getElementById('btn-save-restaurant');
  const btnSaveConvenio = document.getElementById('btn-save-convenio');
  const btnSaveCalendar = document.getElementById('btn-save-calendar');
  const btnAddHoliday = document.getElementById('btn-add-holiday');
  const btnSaveNotifications = document.getElementById('btn-save-notifications');
  if (btnSaveRestaurant) btnSaveRestaurant.addEventListener('click', saveSettings);
  if (btnSaveConvenio) btnSaveConvenio.addEventListener('click', saveSettings);
  if (btnSaveCalendar) btnSaveCalendar.addEventListener('click', saveSettings);
  if (btnAddHoliday) btnAddHoliday.addEventListener('click', addHoliday);
  if (btnSaveNotifications) btnSaveNotifications.addEventListener('click', saveSettings);
}

// Run static event listener binding when DOM is ready
document.addEventListener('DOMContentLoaded', bindStaticEventListeners);

// ===== DASHBOARD =====
async function loadDashboard() {
  const today = new Date().toISOString().slice(0,10);
  document.getElementById('dashboard-date').textContent = new Date().toLocaleDateString('es-ES', { weekday:'long', day:'numeric', month:'long', year:'numeric' });

  // Load stats from API
  const [history_, employees_, overtime_, vacations_] = await Promise.all([
    api('GET', `/clock/history?date=${today}`),
    api('GET', '/employees'),
    api('GET', '/overtime?week=' + getWeekStart()),
    api('GET', '/vacations?status=pending')
  ]);
  let history = Array.isArray(history_) ? history_ : [];
  let employees = Array.isArray(employees_) ? employees_ : [];
  let overtime = Array.isArray(overtime_) ? overtime_ : [];
  let vacations = Array.isArray(vacations_) ? vacations_ : [];

  if (!history && !employees) {
    // If backend is down, show demo banner
    state.isDemo = true;
    updateDemoBanner();
    updateOnlineStatus();
    document.getElementById('stat-empleados').textContent = '—';
    document.getElementById('stat-fichajes').textContent = '—';
    document.getElementById('stat-incidencias').textContent = '—';
    document.getElementById('stat-extras').textContent = '—';
    document.getElementById('dashboard-table-body').innerHTML = '<tr><td colspan="4" class="text-center text-muted" style="padding:32px">No hay datos disponibles — servidor no responde</td></tr>';
    document.getElementById('alert-no-clock').textContent = 'No disponible';
    document.getElementById('alert-vacaciones').textContent = 'No disponible';
    return;
  }

  state.isDemo = false;
  updateDemoBanner();
  updateOnlineStatus();

  if (history) state.clockHistory = history;
  if (employees) state.employees = employees;
  if (overtime) state.overtime = overtime;
  if (vacations) state.vacations = vacations;

  history = Array.isArray(history) ? history : [];
  const safeEmployees = Array.isArray(employees) ? employees : [];
  overtime = Array.isArray(overtime) ? overtime : [];

  const activeEmployees = new Set(history.map(r => r.employee_id)).size;
  const totalClocks = history.length;
  const incidents = history.filter(r => r.status === 'incident').length;

  // Overtime from API (GET /api/overtime)
  let extraHours = '0.0';
  if (overtime && overtime.length > 0) {
    const totalMin = overtime.reduce((sum, o) => sum + (o.total_minutes || 0), 0);
    extraHours = (totalMin / 60).toFixed(1);
  }

  // Alert: employees without clock today
  const clockedIds = new Set(history.map(r => r.employee_id));
  const noClock = safeEmployees.filter(e => e.is_active !== false && !clockedIds.has(e.id));
  document.getElementById('stat-extras').textContent = `${extraHours}h`;

  document.getElementById('stat-empleados').textContent = activeEmployees;
  document.getElementById('stat-fichajes').textContent = totalClocks;
  document.getElementById('stat-incidencias').textContent = incidents;

  const alertNoClock = document.getElementById('alert-no-clock');
  alertNoClock.innerHTML = '';
  if (noClock.length === 0) {
    const span = document.createElement('span');
    span.style.color = '#248A3D';
    span.textContent = '✓ Todos han fichado';
    alertNoClock.appendChild(span);
  } else {
    const fragment = document.createDocumentFragment();
    noClock.slice(0, 5).forEach(e => {
      const div = document.createElement('div');
      div.style.padding = '4px 0';
      div.textContent = `• ${e.full_name || e.name}`;
      fragment.appendChild(div);
    });
    if (noClock.length > 5) {
      const more = document.createElement('div');
      more.style.cssText = 'padding:4px 0;color:rgba(0,0,0,0.3)';
      more.textContent = `+${noClock.length - 5} más`;
      fragment.appendChild(more);
    }
    alertNoClock.appendChild(fragment);
  }

  // Alert: pending vacations
  const pendingVac = (vacations || []).filter(v => v.status === 'pending');
  const alertVacaciones = document.getElementById('alert-vacaciones');
  alertVacaciones.innerHTML = '';
  if (pendingVac.length === 0) {
    const span = document.createElement('span');
    span.style.color = '#248A3D';
    span.textContent = '✓ Sin solicitudes pendientes';
    alertVacaciones.appendChild(span);
  } else {
    const fragment = document.createDocumentFragment();
    pendingVac.slice(0, 5).forEach(v => {
      const div = document.createElement('div');
      div.style.padding = '4px 0';
      div.textContent = `• ${v.employee_name || '—'} (${v.start_date} — ${v.end_date})`;
      fragment.appendChild(div);
    });
    if (pendingVac.length > 5) {
      const more = document.createElement('div');
      more.style.cssText = 'padding:4px 0;color:rgba(0,0,0,0.3)';
      more.textContent = `+${pendingVac.length - 5} más`;
      fragment.appendChild(more);
    }
    alertVacaciones.appendChild(fragment);
  }

  // Table
  const tbody = document.getElementById('dashboard-table-body');
  if (!history || history.length === 0) {
    tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted" style="padding:32px">No hay fichajes hoy</td></tr>';
    return;
  }
  tbody.innerHTML = history.slice(0, 20).map(r => {
    const statusBadge = r.status === 'ok' ? 'badge-ok' : r.status === 'late' ? 'badge-late' : 'badge-incident';
    const statusLabel = r.status === 'ok' ? 'OK' : r.status === 'late' ? 'Tarde' : 'Incidencia';
    const typeLabel = r.type === 'in' ? 'Entrada' : r.type === 'out' ? 'Salida' : r.type === 'break_start' ? 'Pausa' : 'Vuelta';
    return `<tr>
      <td>${r.employee_name || '—'}</td>
      <td>${typeLabel}</td>
      <td>${r.time || r.timestamp ? (r.time || r.timestamp.slice(11,16)) : '—'}</td>
      <td><span class="badge ${statusBadge}">${statusLabel}</span></td>
    </tr>`;
  }).join('');
}

function getWeekStart() {
  const now = new Date();
  const day = now.getDay();
  const diff = now.getDate() - day + (day === 0 ? -6 : 1);
  const monday = new Date(now.setDate(diff));
  return monday.toISOString().slice(0,10);
}

// ===== EMPLEADOS =====
async function loadEmpleados() {
  let employees = await api('GET', '/employees');
  employees = Array.isArray(employees) ? employees : [];
  if (employees.length === 0) {
    state.isDemo = true;
    updateDemoBanner();
    updateOnlineStatus();
    document.getElementById('empleados-table-body').innerHTML = EMPTY_ROW(9, 'No se pudieron cargar los empleados', 'Servidor no responde. Revisa la conexión.');
    return;
  }
  state.isDemo = false;
  updateDemoBanner();
  updateOnlineStatus();
  state.employees = employees;

  // Populate filter dropdowns
  const turnoFilter = document.getElementById('emp-filter-turno');
  const shiftIds = new Set(employees.map(e => e.shift_id || e.default_shift_id).filter(Boolean));
  const shifts = state.shifts.length ? state.shifts : await api('GET', '/shifts') || [];
  state.shifts = Array.isArray(shifts) ? shifts : [];
  turnoFilter.innerHTML = '';
  const defaultOpt = document.createElement('option');
  defaultOpt.value = '';
  defaultOpt.textContent = 'Todos los turnos';
  turnoFilter.appendChild(defaultOpt);
  state.shifts.filter(s => shiftIds.has(s.id)).forEach(s => {
    const opt = document.createElement('option');
    opt.value = s.id;
    opt.textContent = s.name;
    turnoFilter.appendChild(opt);
  });

  state.empPage = 1;
  filterEmpleados();
}

function filterEmpleados() {
  const search = document.getElementById('emp-search').value.toLowerCase().trim();
  const status = document.getElementById('emp-filter-status').value;
  const turno = document.getElementById('emp-filter-turno').value;
  state.empSearch = search;
  state.empFilterStatus = status;
  state.empFilterTurno = turno;

  let filtered = state.employees.filter(e => {
    if (search && !(e.full_name || e.name || '').toLowerCase().includes(search) &&
        !(e.dni || '').toLowerCase().includes(search) &&
        !(e.nss || '').toLowerCase().includes(search)) return false;
    if (status && (e.status || (e.is_active ? 'active' : 'inactive')) !== status) return false;
    if (turno && e.shift_id != turno && e.default_shift_id != turno) return false;
    return true;
  });

  state.empFiltered = filtered;
  renderEmpleadosPage(1);
}

function renderEmpleadosPage(page) {
  state.empPage = page;
  const total = state.empFiltered.length;
  const totalPages = Math.ceil(total / PAGE_SIZE) || 1;
  const start = (page - 1) * PAGE_SIZE;
  const pageItems = state.empFiltered.slice(start, start + PAGE_SIZE);

  const tbody = document.getElementById('empleados-table-body');
  if (pageItems.length === 0) {
    tbody.innerHTML = EMPTY_ROW(9, 'No hay empleados', 'Prueba con otros filtros de búsqueda.');
  } else {
    tbody.innerHTML = '';
    const nfcIcon = createNfcIcon();
    pageItems.forEach(e => {
      const status = e.status || (e.is_active ? 'active' : 'inactive');
      const statusBadge = status === 'active' ? 'badge-active' : status === 'on_vacation' ? 'badge-pending' : status === 'on_leave' ? 'badge-on-leave' : 'badge-inactive';
      const statusLabel = status === 'active' ? 'Activo' : status === 'inactive' ? 'Inactivo' : status === 'on_vacation' ? 'Vacaciones' : status === 'on_leave' ? 'De baja' : status;
      const shiftName = e.shift_name || (state.shifts.find(s => s.id === (e.shift_id || e.default_shift_id)) || {}).name || '—';
      const tr = document.createElement('tr');
      const nameTd = document.createElement('td');
      const nameSpan = document.createElement('span');
      nameSpan.className = 'font-medium';
      nameSpan.textContent = e.full_name || e.name;
      if (e.nfc_uid) {
        nameSpan.appendChild(nfcIcon.cloneNode(true));
      }
      nameTd.appendChild(nameSpan);
      tr.appendChild(nameTd);

      [e.dni || '—', e.nss || '—', e.professional_category || '—', e.contract_type || '—', shiftName].forEach(text => {
        const td = document.createElement('td');
        td.textContent = text;
        tr.appendChild(td);
      });

      const pinTd = document.createElement('td');
      const pinSpan = document.createElement('span');
      pinSpan.className = 'pin-hidden';
      pinSpan.textContent = '••••';
      pinSpan.addEventListener('click', () => togglePin(pinSpan, e.id));
      pinTd.appendChild(pinSpan);
      tr.appendChild(pinTd);

      const statusTd = document.createElement('td');
      const badge = document.createElement('span');
      badge.className = `badge ${statusBadge}`;
      badge.textContent = statusLabel;
      statusTd.appendChild(badge);
      tr.appendChild(statusTd);

      const actionsTd = document.createElement('td');
      const editBtn = document.createElement('button');
      editBtn.className = 'btn btn-ghost btn-sm';
      editBtn.textContent = 'Editar';
      editBtn.addEventListener('click', () => openModal('empleado', e.id));
      const delBtn = document.createElement('button');
      delBtn.className = 'btn btn-danger btn-sm';
      delBtn.textContent = 'Eliminar';
      delBtn.addEventListener('click', () => deleteEmpleado(e.id));
      actionsTd.appendChild(editBtn);
      actionsTd.appendChild(delBtn);
      tr.appendChild(actionsTd);

      tbody.appendChild(tr);
    });
  }

  // Pagination
  renderPagination('emp-pagination', page, totalPages, renderEmpleadosPage);
}

function createNfcIcon() {
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('width', '14');
  svg.setAttribute('height', '14');
  svg.setAttribute('viewBox', '0 0 24 24');
  svg.setAttribute('fill', 'none');
  svg.setAttribute('stroke', '#FF6B35');
  svg.setAttribute('stroke-width', '1.5');
  svg.setAttribute('stroke-linecap', 'round');
  svg.setAttribute('stroke-linejoin', 'round');
  svg.setAttribute('style', 'margin-left:6px;vertical-align:-2px');
  svg.setAttribute('title', 'NFC asignada');
  svg.innerHTML = '<rect x="2" y="2" width="20" height="20" rx="3"/><path d="M8 8a4 4 0 0 1 0 8"/><path d="M16 8a4 4 0 0 0 0 8"/><path d="M10 10a2 2 0 0 1 0 4"/><path d="M14 10a2 2 0 0 0 0 4"/>';
  return svg;
}

// ===== PIN TOGGLE (PIN from API, not in HTML) =====
async function togglePin(el, employeeId) {
  if (el.classList.contains('pin-hidden')) {
    // Load PIN from API
    const emp = await api('GET', `/employees/${employeeId}`);
    if (emp && emp.pin) {
      el.textContent = emp.pin;
      el.className = 'pin-visible';
    } else if (emp && emp.pin_hash) {
      // PIN is hashed, can't display — show message
      showToast('El PIN está cifrado y no puede mostrarse', 'warning');
    } else {
      showToast('No se pudo cargar el PIN', 'error');
    }
  } else {
    el.textContent = '••••';
    el.className = 'pin-hidden';
  }
}

async function deleteEmpleado(id) {
  openConfirmModal({
    title: '¿Eliminar empleado?',
    message: 'Esta acción no se puede deshacer. Se eliminarán todos los datos asociados a este empleado.',
    confirmText: 'Eliminar',
    confirmClass: 'btn-danger',
    onConfirm: async () => {
      const result = await api('DELETE', `/employees/${id}`);
      if (result) {
        showToast('Empleado eliminado correctamente', 'success');
        loadEmpleados();
      } else {
        showToast('Error al eliminar el empleado', 'error');
      }
    }
  });
}

// ===== CALENDARIO =====
function calendarView(view) {
  state.calendarView = view;
  renderCalendar();
}

function calendarNav(delta) {
  const d = new Date(state.calendarDate);
  if (state.calendarView === 'month') {
    d.setMonth(d.getMonth() + delta);
  } else {
    d.setDate(d.getDate() + delta * 7);
  }
  state.calendarDate = d;
  renderCalendar();
}

function calendarToday() {
  state.calendarDate = new Date();
  renderCalendar();
}

async function renderCalendar() {
  const container = document.getElementById('calendar-container');
  const year = state.calendarDate.getFullYear();
  const month = state.calendarDate.getMonth();

  const title = state.calendarDate.toLocaleDateString('es-ES', { month:'long', year:'numeric' });
  document.getElementById('calendar-title').textContent = title.charAt(0).toUpperCase() + title.slice(1);

  // Load holidays and schedules
  const [holidays, schedules] = await Promise.all([
    api('GET', `/calendar/holidays?year=${year}`),
    api('GET', `/schedules?month=${month + 1}&year=${year}`)
  ]);

  if (holidays) state.holidays = holidays;
  if (schedules) state.schedules = schedules;

  const holidayDates = new Set((state.holidays || []).map(h => h.date));

  if (state.calendarView === 'month') {
    renderMonthCalendar(container, year, month, holidayDates, schedules || []);
  } else {
    renderWeekCalendar(container, year, month, holidayDates, schedules || []);
  }
}

function renderMonthCalendar(container, year, month, holidayDates, schedules) {
  const firstDay = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const daysInPrev = new Date(year, month, 0).getDate();
  const today = new Date().toISOString().slice(0,10);
  const dayNames = ['Lun','Mar','Mié','Jue','Vie','Sáb','Dom'];

  // Adjust for Monday start
  const startOffset = firstDay === 0 ? 6 : firstDay - 1;

  container.innerHTML = '';
  const grid = document.createElement('div');
  grid.className = 'calendar-grid';
  dayNames.forEach(d => {
    const header = document.createElement('div');
    header.className = 'calendar-header-cell';
    header.textContent = d;
    grid.appendChild(header);
  });

  // Previous month days
  for (let i = startOffset - 1; i >= 0; i--) {
    const d = daysInPrev - i;
    const cell = document.createElement('div');
    cell.className = 'calendar-cell other-month';
    const num = document.createElement('div');
    num.className = 'day-num';
    num.textContent = d;
    cell.appendChild(num);
    grid.appendChild(cell);
  }

  // Current month days
  for (let d = 1; d <= daysInMonth; d++) {
    const dateStr = `${year}-${String(month+1).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
    const isToday = dateStr === today;
    const isHoliday = holidayDates.has(dateStr);
    const daySchedules = (schedules || []).filter(s => s.date === dateStr);
    const hasEvent = daySchedules.length > 0 || isHoliday;

    let cls = 'calendar-cell';
    if (isToday) cls += ' today';
    if (hasEvent) cls += ' has-event';
    if (isHoliday) cls += ' schedule-holiday';

    const cell = document.createElement('div');
    cell.className = cls;
    cell.addEventListener('click', () => openDayDetail(dateStr));
    const num = document.createElement('div');
    num.className = 'day-num';
    num.textContent = d;
    cell.appendChild(num);

    if (isHoliday) {
      const h = (state.holidays || []).find(h => h.date === dateStr);
      const eventDiv = document.createElement('div');
      eventDiv.className = 'calendar-event holiday';
      eventDiv.textContent = h ? h.name : 'Festivo';
      cell.appendChild(eventDiv);
    }
    daySchedules.slice(0, 2).forEach(s => {
      const shift = state.shifts.find(sh => sh.id === s.shift_id);
      const eventDiv = document.createElement('div');
      eventDiv.className = 'calendar-event shift';
      eventDiv.textContent = shift ? shift.name : 'Turno';
      cell.appendChild(eventDiv);
    });
    if (daySchedules.length > 2) {
      const more = document.createElement('div');
      more.style.cssText = 'font-size:0.6rem;color:rgba(0,0,0,0.3)';
      more.textContent = `+${daySchedules.length - 2} más`;
      cell.appendChild(more);
    }
    grid.appendChild(cell);
  }

  // Fill remaining cells
  const totalCells = startOffset + daysInMonth;
  const remaining = (7 - (totalCells % 7)) % 7;
  for (let d = 1; d <= remaining; d++) {
    const cell = document.createElement('div');
    cell.className = 'calendar-cell other-month';
    const num = document.createElement('div');
    num.className = 'day-num';
    num.textContent = d;
    cell.appendChild(num);
    grid.appendChild(cell);
  }

  container.appendChild(grid);
}

function renderWeekCalendar(container, year, month, holidayDates, schedules) {
  // Simple week view as table
  const employees = state.employees;
  if (!employees || employees.length === 0) {
    container.innerHTML = '<div class="loading-overlay">Carga empleados primero</div>';
    return;
  }

  const monday = new Date(state.calendarDate);
  const day = monday.getDay();
  const diff = monday.getDate() - day + (day === 0 ? -6 : 1);
  monday.setDate(diff);
  monday.setHours(0,0,0,0);

  const days = ['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo'];
  const dates = [];
  for (let i = 0; i < 7; i++) {
    const d = new Date(monday);
    d.setDate(d.getDate() + i);
    dates.push(d.toISOString().slice(0,10));
  }

  container.innerHTML = '';
  const wrapper = document.createElement('div');
  wrapper.className = 'schedule-wrapper';
  const table = document.createElement('table');
  table.className = 'schedule-table';

  const thead = document.createElement('thead');
  const headerRow = document.createElement('tr');
  const thEmployee = document.createElement('th');
  thEmployee.textContent = 'Empleado';
  headerRow.appendChild(thEmployee);
  days.forEach((d, i) => {
    const th = document.createElement('th');
    const isHoliday = holidayDates.has(dates[i]);
    th.textContent = d;
    const br = document.createElement('br');
    th.appendChild(br);
    const span = document.createElement('span');
    span.className = 'text-xs text-muted';
    span.textContent = dates[i].slice(5);
    th.appendChild(span);
    if (isHoliday) {
      th.appendChild(document.createTextNode(' •'));
    }
    headerRow.appendChild(th);
  });
  thead.appendChild(headerRow);
  table.appendChild(thead);

  const tbody = document.createElement('tbody');
  employees.filter(e => e.is_active !== false).forEach(emp => {
    const tr = document.createElement('tr');
    const nameTd = document.createElement('td');
    nameTd.textContent = emp.full_name || emp.name;
    tr.appendChild(nameTd);

    dates.forEach(dateStr => {
      const sched = (schedules || []).find(s => s.employee_id === emp.id && s.date === dateStr);
      const isHoliday = holidayDates.has(dateStr);
      const td = document.createElement('td');
      td.addEventListener('click', () => openAssignShift(emp.id, dateStr));
      if (isHoliday) {
        td.className = 'schedule-holiday';
        const emptySpan = document.createElement('span');
        emptySpan.className = 'schedule-empty';
        emptySpan.textContent = '•';
        td.appendChild(emptySpan);
      } else if (sched) {
        const shift = state.shifts.find(sh => sh.id === sched.shift_id);
        const color = shift ? shift.color : '#FF6B35';
        const cellSpan = document.createElement('span');
        cellSpan.className = 'schedule-cell';
        cellSpan.style.cssText = `background:${color}22;color:${color}`;
        cellSpan.textContent = shift ? shift.name : 'Turno';
        td.appendChild(cellSpan);
      } else {
        const emptySpan = document.createElement('span');
        emptySpan.className = 'schedule-empty';
        emptySpan.textContent = '—';
        td.appendChild(emptySpan);
      }
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);
  wrapper.appendChild(table);
  container.appendChild(wrapper);
}

function openDayDetail(dateStr) {
  showToast(`Detalle del día ${dateStr} — próximamente`, 'info');
}

// ===== ASSIGN SHIFT (NO prompt() — visual modal) =====
function openAssignShift(employeeId, date) {
  const emp = state.employees.find(e => e.id === employeeId);
  const empName = emp ? (emp.full_name || emp.name) : `#${employeeId}`;
  const shifts = state.shifts;
  const currentSched = (state.schedules || []).find(s => s.employee_id === employeeId && s.date === date);
  const currentShiftId = currentSched ? currentSched.shift_id : null;

  const container = document.getElementById('modal-container');
  container.innerHTML = '';
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay';
  overlay.addEventListener('click', (e) => { if (e.target === overlay) closeModal(); });
  const modal = document.createElement('div');
  modal.className = 'modal';
  modal.style.maxWidth = '400px';

  const header = document.createElement('div');
  header.className = 'modal-header';
  const h3 = document.createElement('h3');
  h3.textContent = 'Asignar turno';
  header.appendChild(h3);
  const closeBtn = document.createElement('button');
  closeBtn.className = 'modal-close';
  closeBtn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>';
  closeBtn.addEventListener('click', closeModal);
  header.appendChild(closeBtn);
  modal.appendChild(header);

  const body = document.createElement('div');
  body.className = 'modal-body';
  const p = document.createElement('p');
  p.style.cssText = 'margin-bottom:16px;color:rgba(0,0,0,0.5);font-size:0.875rem';
  const strong = document.createElement('strong');
  strong.style.color = '#1d1d1f';
  strong.textContent = empName;
  p.appendChild(strong);
  p.appendChild(document.createTextNode(` — ${date}`));
  body.appendChild(p);

  const formGroup = document.createElement('div');
  formGroup.className = 'form-group';
  const label = document.createElement('label');
  label.textContent = 'Seleccionar turno';
  formGroup.appendChild(label);
  const select = document.createElement('select');
  select.id = 'assign-shift-select';
  const defaultOpt = document.createElement('option');
  defaultOpt.value = '';
  defaultOpt.textContent = 'Sin turno (descanso)';
  select.appendChild(defaultOpt);
  shifts.forEach(s => {
    const opt = document.createElement('option');
    opt.value = s.id;
    opt.textContent = `${s.name} (${s.start}—${s.end})`;
    if (currentShiftId === s.id) opt.selected = true;
    select.appendChild(opt);
  });
  formGroup.appendChild(select);
  body.appendChild(formGroup);
  modal.appendChild(body);

  const footer = document.createElement('div');
  footer.className = 'modal-footer';
  const cancelBtn = document.createElement('button');
  cancelBtn.className = 'btn btn-ghost';
  cancelBtn.textContent = 'Cancelar';
  cancelBtn.addEventListener('click', closeModal);
  const assignBtn = document.createElement('button');
  assignBtn.className = 'btn btn-primary';
  assignBtn.textContent = 'Asignar';
  assignBtn.addEventListener('click', () => saveAssignShift(employeeId, date));
  footer.appendChild(cancelBtn);
  footer.appendChild(assignBtn);
  modal.appendChild(footer);

  overlay.appendChild(modal);
  container.appendChild(overlay);
}

async function saveAssignShift(employeeId, date) {
  const shiftId = document.getElementById('assign-shift-select').value;
  const body = { employee_id: employeeId, date, shift_id: shiftId ? parseInt(shiftId) : null };
  const result = await api('POST', '/schedules', body);
  if (result) {
    showToast('Turno asignado correctamente', 'success');
    closeModal();
    renderCalendar();
  } else {
    showToast('Error al asignar turno', 'error');
  }
}

// ===== TURNOS =====
async function loadTurnos() {
  let shifts = await api('GET', '/shifts');
  if (!shifts) {
    state.isDemo = true;
    updateDemoBanner();
    document.getElementById('turnos-grid').innerHTML = '<div class="text-center text-muted" style="padding:32px;grid-column:1/-1">No se pudieron cargar los turnos — servidor no responde</div>';
    return;
  }
  state.isDemo = false;
  updateDemoBanner();
  state.shifts = shifts;

  const grid = document.getElementById('turnos-grid');
  if (shifts.length === 0) {
    grid.innerHTML = '<div class="text-center text-muted" style="padding:32px;grid-column:1/-1">No hay turnos configurados</div>';
    return;
  }
  grid.innerHTML = '';
  const typeLabels = { morning:'Mañana', afternoon:'Tarde', night:'Noche', split:'Partido', rotating:'Rotativo', custom:'Personalizado' };
  shifts.forEach(s => {
    const card = document.createElement('div');
    card.className = 'shift-card';
    card.style.borderLeftColor = s.color;

    const header = document.createElement('div');
    header.className = 'shift-card-header';
    const nameSpan = document.createElement('span');
    nameSpan.className = 'shift-card-name';
    nameSpan.textContent = s.name;
    header.appendChild(nameSpan);
    const dot = document.createElement('div');
    dot.style.cssText = `width:12px;height:12px;border-radius:50%;background:${s.color};flex-shrink:0`;
    header.appendChild(dot);
    card.appendChild(header);

    const timeDiv = document.createElement('div');
    timeDiv.className = 'shift-card-time';
    timeDiv.textContent = `${s.start_time || s.start} — ${s.end_time || s.end}`;
    card.appendChild(timeDiv);

    const toleranceDiv = document.createElement('div');
    toleranceDiv.className = 'shift-card-tolerance';
    toleranceDiv.textContent = `Tolerancia: ${s.tolerance_min || s.tolerance || 5} min · ${typeLabels[s.shift_type] || s.shift_type || '—'}`;
    card.appendChild(toleranceDiv);

    const actions = document.createElement('div');
    actions.className = 'shift-card-actions';
    const editBtn = document.createElement('button');
    editBtn.className = 'btn btn-ghost btn-sm';
    editBtn.textContent = 'Editar';
    editBtn.addEventListener('click', () => openModal('turno', s.id));
    const delBtn = document.createElement('button');
    delBtn.className = 'btn btn-danger btn-sm';
    delBtn.textContent = 'Eliminar';
    delBtn.addEventListener('click', () => deleteTurno(s.id));
    actions.appendChild(editBtn);
    actions.appendChild(delBtn);
    card.appendChild(actions);

    grid.appendChild(card);
  });
}

async function deleteTurno(id) {
  openConfirmModal({
    title: '¿Eliminar turno?',
    message: 'Esta acción no se puede deshacer. Los empleados asignados a este turno quedarán sin turno asociado.',
    confirmText: 'Eliminar',
    confirmClass: 'btn-danger',
    onConfirm: async () => {
      const result = await api('DELETE', `/shifts/${id}`);
      if (result) {
        showToast('Turno eliminado correctamente', 'success');
        loadTurnos();
      } else {
        showToast('Error al eliminar el turno', 'error');
      }
    }
  });
}

// ===== FICHAJES =====
async function loadFichajes() {
  const [history, employees] = await Promise.all([
    api('GET', '/clock/history'),
    api('GET', '/employees')
  ]);
  if (!history) {
    state.isDemo = true;
    updateDemoBanner();
    document.getElementById('fichajes-table-body').innerHTML = EMPTY_ROW(5, 'No se pudieron cargar los fichajes', 'Servidor no responde. Revisa la conexión.');
    return;
  }
  state.isDemo = false;
  updateDemoBanner();
  state.clockHistory = history;
  if (employees) state.employees = employees;

  // Populate employee filter
  const empFilter = document.getElementById('clock-filter-empleado');
  const empIds = new Set(history.map(r => r.employee_id));
  empFilter.innerHTML = '';
  const allOpt = document.createElement('option');
  allOpt.value = '';
  allOpt.textContent = 'Todos los empleados';
  empFilter.appendChild(allOpt);
  (employees || []).filter(e => empIds.has(e.id)).forEach(e => {
    const opt = document.createElement('option');
    opt.value = e.id;
    opt.textContent = e.full_name || e.name;
    empFilter.appendChild(opt);
  });

  // Set default date to today
  document.getElementById('clock-filter-date').value = new Date().toISOString().slice(0,10);

  state.clockPage = 1;
  filterFichajes();
}

function filterFichajes() {
  const date = document.getElementById('clock-filter-date').value;
  const empId = document.getElementById('clock-filter-empleado').value;
  const tipo = document.getElementById('clock-filter-tipo').value;
  const estado = document.getElementById('clock-filter-estado').value;
  state.clockFilterDate = date;
  state.clockFilterEmpleado = empId;
  state.clockFilterTipo = tipo;
  state.clockFilterEstado = estado;

  let filtered = state.clockHistory.filter(r => {
    if (date && r.date !== date && (!r.timestamp || r.timestamp.slice(0,10) !== date)) return false;
    if (empId && r.employee_id != empId) return false;
    if (tipo && r.type !== tipo) return false;
    if (estado && r.status !== estado) return false;
    return true;
  });

  state.clockFiltered = filtered;
  renderFichajesPage(1);
}

function renderFichajesPage(page) {
  state.clockPage = page;
  const total = state.clockFiltered.length;
  const totalPages = Math.ceil(total / PAGE_SIZE) || 1;
  const start = (page - 1) * PAGE_SIZE;
  const pageItems = state.clockFiltered.slice(start, start + PAGE_SIZE);

  const tbody = document.getElementById('fichajes-table-body');
  if (pageItems.length === 0) {
    tbody.innerHTML = EMPTY_ROW(5, 'No hay fichajes', 'Prueba con otros filtros de fecha, empleado o estado.');
  } else {
    tbody.innerHTML = '';
    pageItems.forEach(r => {
      const statusBadge = r.status === 'ok' ? 'badge-ok' : r.status === 'late' ? 'badge-late' : 'badge-incident';
      const statusLabel = r.status === 'ok' ? 'OK' : r.status === 'late' ? 'Tarde' : 'Incidencia';
      const typeLabel = r.type === 'in' ? 'Entrada' : r.type === 'out' ? 'Salida' : r.type === 'break_start' ? 'Pausa' : r.type === 'break_end' ? 'Vuelta' : r.type;
      const dateStr = r.date || (r.timestamp ? r.timestamp.slice(0,10) : '—');
      const timeStr = r.time || (r.timestamp ? r.timestamp.slice(11,16) : '—');
      const tr = document.createElement('tr');
      [r.employee_name || '—', dateStr, typeLabel, timeStr].forEach(text => {
        const td = document.createElement('td');
        td.textContent = text;
        tr.appendChild(td);
      });
      const statusTd = document.createElement('td');
      const badge = document.createElement('span');
      badge.className = `badge ${statusBadge}`;
      badge.textContent = statusLabel;
      statusTd.appendChild(badge);
      tr.appendChild(statusTd);
      tbody.appendChild(tr);
    });
  }

  renderPagination('clock-pagination', page, totalPages, renderFichajesPage);
}

// ===== VACACIONES =====
async function loadVacaciones() {
  const [vacations, employees] = await Promise.all([
    api('GET', '/vacations'),
    api('GET', '/employees')
  ]);
  if (!vacations) {
    state.isDemo = true;
    updateDemoBanner();
    document.getElementById('vacaciones-table-body').innerHTML = EMPTY_ROW(7, 'No se pudieron cargar las solicitudes', 'Servidor no responde. Revisa la conexión.');
    return;
  }
  state.isDemo = false;
  updateDemoBanner();
  // Si la API devuelve paginación, extraer items
  let vacationItems = Array.isArray(vacations) ? vacations : (vacations.items || []);
  state.vacations = vacationItems;
  if (employees) state.employees = employees;

  state.vacFilterSearch = '';
  state.vacFilterStatus = '';
  state.vacPage = 1;
  filterVacaciones();
}

function filterVacaciones() {
  const search = (document.getElementById('vac-search')?.value || '').toLowerCase().trim();
  const status = document.getElementById('vac-filter-status')?.value || '';
  state.vacFilterSearch = search;
  state.vacFilterStatus = status;

  let filtered = state.vacations.filter(v => {
    const empName = (v.employee_name || '').toLowerCase();
    const typeLabel = (v.type === 'vacation' ? 'Vacaciones' : v.type === 'personal_leave' ? 'Permiso personal' : v.type === 'unpaid_leave' ? 'Permiso no retribuido' : v.type || '').toLowerCase();
    if (search && !empName.includes(search) && !typeLabel.includes(search)) return false;
    if (status && v.status !== status) return false;
    return true;
  });

  state.vacFiltered = filtered;
  renderVacacionesPage(1);
}

function renderVacacionesPage(page) {
  state.vacPage = page;
  const total = state.vacFiltered.length;
  const totalPages = Math.ceil(total / PAGE_SIZE) || 1;
  const start = (page - 1) * PAGE_SIZE;
  const pageItems = state.vacFiltered.slice(start, start + PAGE_SIZE);

  const tbody = document.getElementById('vacaciones-table-body');
  if (pageItems.length === 0) {
    tbody.innerHTML = EMPTY_ROW(7, 'No hay solicitudes', 'Prueba con otros filtros de búsqueda o estado.');
  } else {
    tbody.innerHTML = '';
    pageItems.forEach(v => {
      const statusBadge = v.status === 'pending' ? 'badge-pending' : v.status === 'approved' ? 'badge-approved' : 'badge-rejected';
      const statusLabel = v.status === 'pending' ? 'Pendiente' : v.status === 'approved' ? 'Aprobada' : 'Rechazada';
      const typeLabel = v.type === 'vacation' ? 'Vacaciones' : v.type === 'personal_leave' ? 'Permiso personal' : v.type || '—';
      const tr = document.createElement('tr');
      [v.employee_name || '—', typeLabel, v.start_date || '—', v.end_date || '—', v.total_days || '—'].forEach(text => {
        const td = document.createElement('td');
        td.textContent = text;
        tr.appendChild(td);
      });
      const statusTd = document.createElement('td');
      const badge = document.createElement('span');
      badge.className = `badge ${statusBadge}`;
      badge.textContent = statusLabel;
      statusTd.appendChild(badge);
      tr.appendChild(statusTd);

      const actionsTd = document.createElement('td');
      if (v.status === 'pending') {
        const approveBtn = document.createElement('button');
        approveBtn.className = 'btn btn-sm btn-secondary';
        approveBtn.textContent = 'Aprobar';
        approveBtn.addEventListener('click', () => approveVacacion(v.id));
        const rejectBtn = document.createElement('button');
        rejectBtn.className = 'btn btn-sm btn-danger';
        rejectBtn.textContent = 'Rechazar';
        rejectBtn.addEventListener('click', () => rejectVacacion(v.id));
        actionsTd.appendChild(approveBtn);
        actionsTd.appendChild(rejectBtn);
      } else {
        const emptySpan = document.createElement('span');
        emptySpan.className = 'text-xs text-muted';
        emptySpan.textContent = '—';
        actionsTd.appendChild(emptySpan);
      }
      tr.appendChild(actionsTd);
      tbody.appendChild(tr);
    });
  }

  renderPagination('vac-pagination', page, totalPages, renderVacacionesPage);
  renderVacacionesCalendar();
}

function renderVacacionesCalendar() {
  const container = document.getElementById('vacaciones-calendar');
  const approved = state.vacations.filter(v => v.status === 'approved');
  if (approved.length === 0) {
    container.innerHTML = EMPTY_ROW(1, 'No hay vacaciones aprobadas', 'Las solicitudes aprobadas aparecerán aquí.');
    return;
  }
  container.innerHTML = '';
  const wrapper = document.createElement('div');
  wrapper.style.cssText = 'display:flex;flex-wrap:wrap;gap:8px';
  approved.forEach(v => {
    const card = document.createElement('div');
    card.style.cssText = 'background:rgba(52,199,89,0.1);border:1px solid rgba(52,199,89,0.2);border-radius:8px;padding:8px 12px;font-size:0.8rem';
    const strong = document.createElement('strong');
    strong.style.color = '#248A3D';
    strong.textContent = v.employee_name || '—';
    const br = document.createElement('br');
    const span = document.createElement('span');
    span.style.color = 'rgba(0,0,0,0.5)';
    span.textContent = `${v.start_date} → ${v.end_date}`;
    card.appendChild(strong);
    card.appendChild(br);
    card.appendChild(span);
    wrapper.appendChild(card);
  });
  container.appendChild(wrapper);
}

async function approveVacacion(id) {
  const result = await api('POST', `/vacations/${id}/approve`);
  if (result) { showToast('Vacaciones aprobadas', 'success'); loadVacaciones(); }
  else showToast('Error al aprobar', 'error');
}

function rejectVacacion(id) {
  // Use modal instead of prompt
  const container = document.getElementById('modal-container');
  container.innerHTML = '';
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay';
  overlay.addEventListener('click', (e) => { if (e.target === overlay) closeModal(); });
  const modal = document.createElement('div');
  modal.className = 'modal';
  modal.style.maxWidth = '400px';

  const header = document.createElement('div');
  header.className = 'modal-header';
  const h3 = document.createElement('h3');
  h3.textContent = 'Rechazar solicitud';
  header.appendChild(h3);
  const closeBtn = document.createElement('button');
  closeBtn.className = 'modal-close';
  closeBtn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>';
  closeBtn.addEventListener('click', closeModal);
  header.appendChild(closeBtn);
  modal.appendChild(header);

  const body = document.createElement('div');
  body.className = 'modal-body';
  const formGroup = document.createElement('div');
  formGroup.className = 'form-group';
  const label = document.createElement('label');
  label.textContent = 'Motivo del rechazo';
  formGroup.appendChild(label);
  const textarea = document.createElement('textarea');
  textarea.id = 'reject-reason';
  textarea.rows = 3;
  textarea.placeholder = 'Indica el motivo…';
  textarea.style.width = '100%';
  formGroup.appendChild(textarea);
  body.appendChild(formGroup);
  modal.appendChild(body);

  const footer = document.createElement('div');
  footer.className = 'modal-footer';
  const cancelBtn = document.createElement('button');
  cancelBtn.className = 'btn btn-ghost';
  cancelBtn.textContent = 'Cancelar';
  cancelBtn.addEventListener('click', closeModal);
  const rejectBtn = document.createElement('button');
  rejectBtn.className = 'btn btn-danger';
  rejectBtn.textContent = 'Rechazar';
  rejectBtn.addEventListener('click', () => confirmRejectVacacion(id));
  footer.appendChild(cancelBtn);
  footer.appendChild(rejectBtn);
  modal.appendChild(footer);

  overlay.appendChild(modal);
  container.appendChild(overlay);
}

async function confirmRejectVacacion(id) {
  const reason = document.getElementById('reject-reason').value.trim();
  if (!reason) { showToast('Indica un motivo para el rechazo', 'warning'); return; }
  const result = await api('POST', `/vacations/${id}/reject`, { reason });
  if (result) { showToast('Vacaciones rechazadas', 'success'); closeModal(); loadVacaciones(); }
  else showToast('Error al rechazar', 'error');
}

// ===== BAJAS =====
async function loadBajas() {
  const [leaves, employees] = await Promise.all([
    api('GET', '/leave'),
    api('GET', '/employees')
  ]);
  if (!leaves) {
    state.isDemo = true;
    updateDemoBanner();
    document.getElementById('bajas-table-body').innerHTML = EMPTY_ROW(7, 'No se pudieron cargar las bajas', 'Servidor no responde. Revisa la conexión.');
    return;
  }
  state.isDemo = false;
  updateDemoBanner();
  // Si la API devuelve paginación, extraer items
  let leaveItems = Array.isArray(leaves) ? leaves : (leaves.items || []);
  state.leaves = leaveItems;
  if (employees) state.employees = employees;

  state.leaveFilterStatus = '';
  state.leaveFilterType = '';
  filterBajas();
}

function filterBajas() {
  const status = document.getElementById('leave-filter-status').value;
  const type = document.getElementById('leave-filter-type').value;
  const search = (document.getElementById('leave-search')?.value || '').toLowerCase().trim();
  state.leaveFilterStatus = status;
  state.leaveFilterType = type;
  state.leaveFilterSearch = search;

  let filtered = state.leaves.filter(l => {
    const empName = (l.employee_name || '').toLowerCase();
    const typeLabels = { EC:'Enf. Común', ANL:'Acc. No Laboral', AL:'Acc. Laboral', EP:'Enf. Profesional', MAT:'Maternidad', PAT:'Paternidad' };
    const typeLabel = (typeLabels[l.leave_type] || l.leave_type || '').toLowerCase();
    if (search && !empName.includes(search) && !typeLabel.includes(search)) return false;
    if (status && l.status !== status) return false;
    if (type && l.leave_type !== type) return false;
    return true;
  });

  state.leaveFiltered = filtered;
  renderBajasPage(1);
}

function renderBajasPage(page) {
  state.leavePage = page;
  const total = state.leaveFiltered.length;
  const totalPages = Math.ceil(total / PAGE_SIZE) || 1;
  const start = (page - 1) * PAGE_SIZE;
  const pageItems = state.leaveFiltered.slice(start, start + PAGE_SIZE);

  const tbody = document.getElementById('bajas-table-body');
  if (pageItems.length === 0) {
    tbody.innerHTML = EMPTY_ROW(7, 'No hay bajas', 'Prueba con otros filtros de búsqueda, estado o tipo.');
  } else {
    const typeLabels = { EC:'Enf. Común', ANL:'Acc. No Laboral', AL:'Acc. Laboral', EP:'Enf. Profesional', MAT:'Maternidad', PAT:'Paternidad' };
    tbody.innerHTML = pageItems.map(l => {
      const statusBadge = l.status === 'active' ? 'badge-incident' : 'badge-ok';
      const statusLabel = l.status === 'active' ? 'Activa' : 'Finalizada';
      const days = l.total_days || (l.start_date && l.end_date ? Math.ceil((new Date(l.end_date) - new Date(l.start_date)) / (1000*60*60*24)) + 1 : '—');
      return `<tr>
        <td>${l.employee_name || '—'}</td>
        <td>${typeLabels[l.leave_type] || l.leave_type || '—'}</td>
        <td>${l.start_date || '—'}</td>
        <td>${l.expected_end_date || l.end_date || '—'}</td>
        <td>${days}</td>
        <td><span class="badge ${statusBadge}">${statusLabel}</span></td>
        <td>
          ${l.status === 'active' ? `<button class="btn btn-sm btn-secondary" onclick="closeLeave(${l.id})">Dar alta</button>` : '<span class="text-xs text-muted">—</span>'}
        </td>
      </tr>`;
    }).join('');
  }

  renderPagination('leave-pagination', page, totalPages, renderBajasPage);
}

async function closeLeave(id) {
  openConfirmModal({
    title: '¿Confirmar alta médica?',
    message: 'Se registrará la fecha de hoy como fin de la baja por incapacidad temporal.',
    confirmText: 'Confirmar alta',
    confirmClass: 'btn-primary',
    onConfirm: async () => {
      const result = await api('POST', `/leave/${id}/close`);
      if (result) { showToast('Baja cerrada correctamente', 'success'); loadBajas(); }
      else showToast('Error al cerrar la baja', 'error');
    }
  });
}

// ===== INFORMES =====
function initReports() {
  const today = new Date();
  const monthAgo = new Date(today);
  monthAgo.setDate(monthAgo.getDate() - 30);
  document.getElementById('report-start').value = monthAgo.toISOString().slice(0,10);
  document.getElementById('report-end').value = today.toISOString().slice(0,10);
  loadReports();
}

async function loadReports() {
  const start = document.getElementById('report-start').value;
  const end = document.getElementById('report-end').value;
  const type = document.getElementById('report-type').value;
  if (!start || !end) return;

  const titles = {
    hours: 'Horas trabajadas',
    overtime: 'Horas extra',
    absenteeism: 'Absentismo',
    'labor-costs': 'Costes laborales',
    inspection: 'Inspección de trabajo',
    payroll: 'Nómina'
  };
  document.getElementById('report-title').textContent = titles[type] || 'Informe';

  let data = null;
  let theadHtml = '';
  let tbodyHtml = '';

  switch(type) {
    case 'hours':
      data = await api('GET', `/reports/hours?start=${start}&end=${end}`);
      theadHtml = '<tr><th>Empleado</th><th>Horas ordinarias</th><th>Horas extra</th><th>Total</th></tr>';
      if (data && data.length > 0) {
        tbodyHtml = data.map(r => `<tr><td>${r.employee_name}</td><td>${r.ordinarias || r.regular_hours || 0}h</td><td>${r.extra || r.overtime_hours || 0}h</td><td><strong>${r.total || (parseFloat(r.regular_hours||0) + parseFloat(r.overtime_hours||0)).toFixed(1)}h</strong></td></tr>`).join('');
      }
      break;
    case 'overtime':
      data = await api('GET', `/reports/overtime?start=${start}&end=${end}`);
      theadHtml = '<tr><th>Empleado</th><th>Fecha</th><th>Tipo</th><th>Minutos</th><th>Estado</th></tr>';
      if (data && data.length > 0) {
        tbodyHtml = data.map(r => `<tr><td>${r.employee_name}</td><td>${r.date}</td><td>${r.overtime_type === 'structural' ? 'Estructural' : 'Fuerza Mayor'}</td><td>${r.total_minutes} min</td><td>${r.compensation_type || 'Pendiente'}</td></tr>`).join('');
      }
      break;
    case 'absenteeism':
      data = await api('GET', `/reports/absenteeism?start=${start}&end=${end}`);
      theadHtml = '<tr><th>Empleado</th><th>Días ausencia</th><th>Tasa</th><th>Tipo</th></tr>';
      if (data && data.length > 0) {
        tbodyHtml = data.map(r => `<tr><td>${r.employee_name}</td><td>${r.absent_days || 0}</td><td>${r.rate || '0%'}</td><td>${r.type || '—'}</td></tr>`).join('');
      }
      break;
    case 'labor-costs':
      data = await api('GET', `/reports/labor-costs?start=${start}&end=${end}`);
      theadHtml = '<tr><th>Empleado</th><th>Salario base</th><th>Complementos</th><th>Horas extra</th><th>Total</th></tr>';
      if (data && data.length > 0) {
        tbodyHtml = data.map(r => `<tr><td>${r.employee_name}</td><td>${r.base_salary || 0}€</td><td>${r.complements || 0}€</td><td>${r.overtime_amount || 0}€</td><td><strong>${r.total || 0}€</strong></td></tr>`).join('');
      }
      break;
    case 'inspection':
      data = await api('GET', `/reports/daily?start=${start}&end=${end}`);
      theadHtml = '<tr><th>Empleado</th><th>DNI</th><th>Fecha</th><th>Entrada</th><th>Salida</th><th>Total</th></tr>';
      if (data && data.length > 0) {
        tbodyHtml = data.map(r => `<tr><td>${r.employee_name}</td><td>${r.dni || '—'}</td><td>${r.date}</td><td>${r.clock_in || '—'}</td><td>${r.clock_out || '—'}</td><td>${r.total_hours || '—'}h</td></tr>`).join('');
      }
      break;
    case 'payroll':
      data = await api('GET', `/reports/monthly-hours?start=${start}&end=${end}`);
      theadHtml = '<tr><th>Empleado</th><th>Programadas</th><th>Trabajadas</th><th>Extra</th><th>Festivos</th><th>Ausencias</th></tr>';
      if (data && data.length > 0) {
        tbodyHtml = data.map(r => `<tr><td>${r.employee_name}</td><td>${r.scheduled_hours || 0}h</td><td>${r.worked_hours || 0}h</td><td>${r.overtime_hours || 0}h</td><td>${r.holiday_hours || 0}h</td><td>${r.absent_days || 0}d</td></tr>`).join('');
      }
      break;
  }

  document.getElementById('report-thead').innerHTML = theadHtml;
  const body = document.getElementById('report-body');
  if (!data || data.length === 0) {
    body.innerHTML = '<tr><td colspan="10" class="text-center text-muted" style="padding:32px">No hay datos en el período seleccionado</td></tr>';
  } else {
    body.innerHTML = tbodyHtml;
  }
}

async function exportReport(format) {
  const start = document.getElementById('report-start').value;
  const end = document.getElementById('report-end').value;
  const type = document.getElementById('report-type').value;
  try {
    const resp = await fetch(`${API_BASE}/reports/export?format=${format}&start=${start}&end=${end}&type=${type}`, {
      credentials: 'include'
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `informe_${type}_${start}_${end}.${format === 'pdf' ? 'pdf' : 'xlsx'}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast('Informe descargado correctamente', 'success');
  } catch(e) {
    console.warn('Export failed:', e.message);
    showToast('Error al descargar el informe', 'error');
  }
}

// ===== CONFIGURACIÓN =====
async function loadSettings() {
  const settings = await api('GET', '/settings');
  if (!settings) {
    state.isDemo = true;
    updateDemoBanner();
    return;
  }
  state.isDemo = false;
  updateDemoBanner();

  document.getElementById('cfg-nombre').value = settings.name || settings.nombre || '';
  document.getElementById('cfg-cif').value = settings.cif || '';
  document.getElementById('cfg-direccion').value = settings.address || settings.direccion || '';
  document.getElementById('cfg-telefono').value = settings.phone || '';
  document.getElementById('cfg-email').value = settings.email || '';
  document.getElementById('cfg-convenio').value = settings.convenio || '';
  document.getElementById('cfg-ccaa').value = settings.ccaa || '';
  document.getElementById('cfg-tolerancia').value = settings.tolerancia_min || settings.tolerancia || 5;
  document.getElementById('cfg-vacation-days').value = settings.vacation_days_per_year || 30;
  document.getElementById('cfg-weekly-hours').value = settings.weekly_hours || 40;
  document.getElementById('cfg-work-days').value = settings.work_days || 5;
  document.getElementById('cfg-notif-email').value = settings.notif_email || 'all';
  document.getElementById('cfg-notif-clock').value = settings.notif_clock || '15';
  document.getElementById('cfg-notif-vacation').value = settings.notif_vacation || 'weekly';

  // Load holidays
  loadHolidays();
}

async function loadHolidays() {
  const year = document.getElementById('cfg-holiday-year').value || 2026;
  const holidays = await api('GET', `/calendar/holidays?year=${year}`);
  if (!holidays) return;
  state.holidays = holidays;
  const tbody = document.getElementById('holidays-table-body');
  if (holidays.length === 0) {
    tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted" style="padding:16px">No hay festivos registrados</td></tr>';
  } else {
    tbody.innerHTML = '';
    holidays.forEach(h => {
      const typeLabel = h.type === 'national' ? 'Nacional' : h.type === 'regional' ? 'Autonómico' : 'Local';
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${h.date}</td>
        <td>${h.name}</td>
        <td>${typeLabel}</td>
        <td><button class="btn btn-danger btn-sm holiday-delete" data-holiday-id="${h.id}">✕</button></td>`;
      tbody.appendChild(tr);
    });
    tbody.querySelectorAll('.holiday-delete').forEach(btn => {
      btn.addEventListener('click', () => deleteHoliday(btn.dataset.holidayId));
    });
  }
}

function initHolidayListeners(tbody) {
  tbody.querySelectorAll('.holiday-delete').forEach(btn => {
    btn.addEventListener('click', () => deleteHoliday(btn.dataset.holidayId));
  });
}

async function addHoliday() {
  const date = document.getElementById('cfg-holiday-date').value;
  const name = document.getElementById('cfg-holiday-name').value.trim();
  if (!date || !name) { showToast('Completa fecha y nombre del festivo', 'warning'); return; }
  const result = await api('POST', '/calendar/holidays', { date, name, type: 'local', year: parseInt(date.slice(0,4)) });
  if (result) {
    showToast('Festivo añadido', 'success');
    document.getElementById('cfg-holiday-date').value = '';
    document.getElementById('cfg-holiday-name').value = '';
    loadHolidays();
  } else {
    showToast('Error al añadir festivo', 'error');
  }
}

async function deleteHoliday(id) {
  openConfirmModal({
    title: '¿Eliminar festivo?',
    message: 'Esta acción no se puede deshacer.',
    confirmText: 'Eliminar',
    confirmClass: 'btn-danger',
    onConfirm: async () => {
      const result = await api('DELETE', `/calendar/holidays/${id}`);
      if (result) { showToast('Festivo eliminado', 'success'); loadHolidays(); }
      else showToast('Error al eliminar', 'error');
    }
  });
}

async function saveSettings() {
  const body = {
    name: document.getElementById('cfg-nombre').value,
    cif: document.getElementById('cfg-cif').value,
    address: document.getElementById('cfg-direccion').value,
    phone: document.getElementById('cfg-telefono').value,
    email: document.getElementById('cfg-email').value,
    convenio: document.getElementById('cfg-convenio').value,
    ccaa: document.getElementById('cfg-ccaa').value,
    tolerancia_min: parseInt(document.getElementById('cfg-tolerancia').value) || 5,
    vacation_days_per_year: parseInt(document.getElementById('cfg-vacation-days').value) || 30,
    weekly_hours: parseInt(document.getElementById('cfg-weekly-hours').value) || 40,
    work_days: parseInt(document.getElementById('cfg-work-days').value) || 5,
    notif_email: document.getElementById('cfg-notif-email').value,
    notif_clock: document.getElementById('cfg-notif-clock').value,
    notif_vacation: document.getElementById('cfg-notif-vacation').value
  };
  const result = await api('PUT', '/settings', body);
  if (result) {
    showToast('Configuración guardada correctamente', 'success');
  } else {
    showToast('Error al guardar la configuración', 'error');
  }
}

// ===== FACTURACIÓN / BILLING =====
async function loadBilling() {
  const loading = document.getElementById('billing-loading');
  const content = document.getElementById('billing-content');
  const error = document.getElementById('billing-error');
  loading.classList.remove('hidden');
  content.classList.add('hidden');
  error.classList.add('hidden');

  const tenantId = state.user?.tenant_id;
  if (!tenantId) {
    loading.classList.add('hidden');
    error.classList.remove('hidden');
    error.textContent = 'No hay tenant asociado a tu cuenta.';
    return;
  }

  const status = await api('GET', `/billing/status/${tenantId}`);
  if (!status) {
    loading.classList.add('hidden');
    error.classList.remove('hidden');
    return;
  }

  loading.classList.add('hidden');
  content.classList.remove('hidden');

  // Plan name
  const planNames = { basic: 'Básico', pro: 'Pro', kit: 'Kit inicial' };
  document.getElementById('billing-plan-name').textContent = planNames[status.plan] || status.plan;

  // Status badge
  const statusEl = document.getElementById('billing-status');
  const statusLabels = {
    active: 'Activa',
    canceled: 'Cancelada',
    past_due: 'Pendiente de pago',
    trialing: 'Prueba gratuita',
    incomplete: 'Incompleta',
    unpaid: 'No pagada',
  };
  const statusColor = status.subscription_status === 'active' || status.subscription_status === 'trialing'
    ? '#34C759' : status.subscription_status === 'canceled' ? '#FF3B30' : '#FF9500';
  statusEl.innerHTML = '';
  const statusSpan = document.createElement('span');
  statusSpan.style.cssText = 'display:inline-flex;align-items:center;gap:4px';
  const dot = document.createElement('span');
  dot.style.cssText = `width:8px;height:8px;border-radius:50%;background:${statusColor};display:inline-block`;
  const label = document.createElement('span');
  label.textContent = statusLabels[status.subscription_status] || status.subscription_status;
  statusSpan.appendChild(dot);
  statusSpan.appendChild(label);
  statusEl.appendChild(statusSpan);

  // Next payment
  const nextPaymentEl = document.getElementById('billing-next-payment');
  if (status.current_period_end) {
    const d = new Date(status.current_period_end);
    nextPaymentEl.textContent = d.toLocaleDateString('es-ES', {
      year: 'numeric', month: 'long', day: 'numeric'
    });
  } else {
    nextPaymentEl.textContent = '—';
  }

  // Amount
  const planAmounts = { basic: '29€/mes', pro: '39€/mes', kit: '49€ (único)' };
  document.getElementById('billing-amount').textContent = planAmounts[status.plan] || '—';
}

async function changePlan() {
  const tenantId = state.user?.tenant_id;
  if (!tenantId) { showToast('No hay tenant asociado', 'error'); return; }

  // Show a simple plan selector modal
  const plans = [
    { id: 'basic', name: 'Básico', price: '29€/mes' },
    { id: 'pro', name: 'Pro', price: '39€/mes' },
    { id: 'kit', name: 'Kit inicial', price: '49€ (único)' },
  ];

  const modal = document.createElement('div');
  modal.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.3);z-index:1000;display:flex;align-items:center;justify-content:center;padding:20px';
  modal.innerHTML = `
    <div style="background:#fff;border-radius:12px;padding:24px;max-width:400px;width:100%;box-shadow:0 8px 32px rgba(0,0,0,0.12)">
      <h3 style="font-size:1rem;font-weight:600;margin:0 0 4px">Seleccionar plan</h3>
      <p style="font-size:0.8125rem;color:rgba(0,0,0,0.45);margin:0 0 16px">Elige el plan al que deseas cambiarte</p>
      <div style="display:flex;flex-direction:column;gap:8px;margin-bottom:16px">
        ${plans.map(p => `
          <label style="display:flex;align-items:center;gap:10px;padding:12px;border:1px solid rgba(0,0,0,0.08);border-radius:8px;cursor:pointer;transition:border-color 200ms">
            <input type="radio" name="plan-select" value="${p.id}" style="accent-color:#FF6B35">
            <div>
              <div style="font-weight:500;font-size:0.875rem">${p.name}</div>
              <div style="font-size:0.75rem;color:rgba(0,0,0,0.45)">${p.price}</div>
            </div>
          </label>
        `).join('')}
      </div>
      <div style="display:flex;gap:8px;justify-content:flex-end">
        <button class="btn btn-ghost" onclick="this.closest('div[style]').parentElement.remove()">Cancelar</button>
        <button class="btn btn-primary" id="btn-confirm-plan">Continuar al pago</button>
      </div>
    </div>
  `;
  document.body.appendChild(modal);

  document.getElementById('btn-confirm-plan').addEventListener('click', async () => {
    const selected = modal.querySelector('input[name="plan-select"]:checked');
    if (!selected) { showToast('Selecciona un plan', 'warning'); return; }
    modal.remove();

    showToast('Redirigiendo a Stripe…', 'info');
    const result = await api('POST', '/billing/checkout-session', {
      plan: selected.value,
      tenant_id: tenantId,
    });
    if (result && result.url) {
      window.location.href = result.url;
    } else {
      showToast('Error al crear la sesión de pago', 'error');
    }
  });
}

async function manageSubscription() {
  const tenantId = state.user?.tenant_id;
  if (!tenantId) { showToast('No hay tenant asociado', 'error'); return; }

  const result = await api('POST', `/billing/portal/${tenantId}`);
  if (result && result.url) {
    window.location.href = result.url;
  } else {
    showToast('Error al abrir el portal de gestión', 'error');
  }
}

// ===== SETTINGS TABS =====
function initBillingListeners() {
  const changePlanBtn = document.getElementById('billing-change-plan-btn');
  const manageSubscriptionBtn = document.getElementById('billing-manage-subscription-btn');
  if (changePlanBtn) changePlanBtn.addEventListener('click', changePlan);
  if (manageSubscriptionBtn) manageSubscriptionBtn.addEventListener('click', manageSubscription);
}

document.querySelectorAll('.settings-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.settings-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.settings-panel').forEach(p => p.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById(`panel-${tab.dataset.tab}`).classList.add('active');

    // Load billing data when billing tab is selected
    if (tab.dataset.tab === 'facturacion') {
      loadBilling();
    }
  });
});
initBillingListeners();

// ===== PAGINATION HELPER =====
function renderPagination(containerId, currentPage, totalPages, callback) {
  const container = document.getElementById(containerId);
  if (totalPages <= 1) {
    container.innerHTML = '';
    return;
  }
  let html = '';
  html += `<button class="page-btn" onclick="callback(${currentPage - 1})" ${currentPage <= 1 ? 'disabled' : ''}>Anterior</button>`;
  const start = Math.max(1, currentPage - 2);
  const end = Math.min(totalPages, currentPage + 2);
  if (start > 1) html += `<button class="page-btn" onclick="callback(1)">1</button>${start > 2 ? '<span class="page-info">…</span>' : ''}`;
  for (let i = start; i <= end; i++) {
    html += `<button class="page-btn ${i === currentPage ? 'active' : ''}" onclick="callback(${i})">${i}</button>`;
  }
  if (end < totalPages) html += `${end < totalPages - 1 ? '<span class="page-info">…</span>' : ''}<button class="page-btn" onclick="callback(${totalPages})">${totalPages}</button>`;
  html += `<button class="page-btn" onclick="callback(${currentPage + 1})" ${currentPage >= totalPages ? 'disabled' : ''}>Siguiente</button>`;
  container.innerHTML = html;
}

// ===== CONFIRM MODAL =====
function openConfirmModal({ title, message, confirmText = 'Confirmar', cancelText = 'Cancelar', confirmClass = 'btn-primary', onConfirm }) {
  state.pendingConfirm = onConfirm;
  const container = document.getElementById('modal-container');
  container.innerHTML = `
    <div class="modal-overlay" onclick="if(event.target===this)closeConfirmModal()">
      <div class="modal" style="max-width:420px">
        <div class="modal-header">
          <h3>${title || '¿Estás seguro?'}</h3>
          <button class="modal-close" onclick="closeConfirmModal()">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>
        <div class="modal-body">
          <p style="font-size:0.875rem;color:rgba(0,0,0,0.6);line-height:1.5">${message || ''}</p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-ghost" onclick="closeConfirmModal()">${cancelText}</button>
          <button class="btn ${confirmClass}" onclick="executeConfirm()">${confirmText}</button>
        </div>
      </div>
    </div>
  `;
}

function closeConfirmModal() {
  state.pendingConfirm = null;
  document.getElementById('modal-container').innerHTML = '';
}

async function executeConfirm() {
  const fn = state.pendingConfirm;
  closeConfirmModal();
  if (typeof fn === 'function') {
    try {
      await fn();
    } catch (e) {
      console.error('Confirm action failed:', e);
      showToast('Error al ejecutar la acción', 'error');
    }
  }
}

// ===== MODAL =====
function openModal(type, id) {
  const container = document.getElementById('modal-container');
  let title = '', fields = '', wide = false;

  if (type === 'empleado') {
    const emp = id ? state.employees.find(e => e.id === id) : null;
    title = id ? 'Editar empleado' : 'Añadir empleado';
    wide = true;
    const shifts = state.shifts;
    const buildShiftOptions = () => {
      const opts = [];
      opts.push({ value: '', label: 'Sin turno', selected: false });
      shifts.forEach(s => {
        const selected = emp && (emp.shift_id === s.id || emp.default_shift_id === s.id);
        opts.push({ value: s.id, label: s.name, selected });
      });
      return opts;
    };
    const shiftOptions = buildShiftOptions();
    const shiftOptionsHtml = shiftOptions.map(o => `<option value="${o.value}" ${o.selected ? 'selected' : ''}>${o.label}</option>`).join('');
    fields = `
      <div class="form-row">
        <div class="form-group">
          <label>Nombre</label>
          <input type="text" id="modal-emp-name" value="${emp ? (emp.full_name || emp.name) : ''}" placeholder="Nombre">
        </div>
        <div class="form-group">
          <label>Apellidos</label>
          <input type="text" id="modal-emp-lastname" value="${emp ? (emp.last_name || '') : ''}" placeholder="Apellidos">
        </div>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>DNI / NIE</label>
          <input type="text" id="modal-emp-dni" value="${emp ? (emp.dni || '') : ''}" placeholder="12345678A">
        </div>
        <div class="form-group">
          <label>N.º Seguridad Social</label>
          <input type="text" id="modal-emp-nss" value="${emp ? (emp.nss || '') : ''}" placeholder="N.º SS">
        </div>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>Categoría profesional</label>
          <input type="text" id="modal-emp-category" value="${emp ? (emp.professional_category || '') : ''}" placeholder="Ej: Camarero/a">
        </div>
        <div class="form-group">
          <label>Tipo de contrato</label>
          <select id="modal-emp-contract">
            <option value="">Seleccionar…</option>
            <option value="IND" ${emp && emp.contract_type === 'IND' ? 'selected' : ''}>Indefinido</option>
            <option value="TEM-OC" ${emp && emp.contract_type === 'TEM-OC' ? 'selected' : ''}>Temporal obra</option>
            <option value="TEM-CIR" ${emp && emp.contract_type === 'TEM-CIR' ? 'selected' : ''}>Temporal circunstancias</option>
            <option value="TEM-INT" ${emp && emp.contract_type === 'TEM-INT' ? 'selected' : ''}>Interinidad</option>
            <option value="PAR-IND" ${emp && emp.contract_type === 'PAR-IND' ? 'selected' : ''}>Tiempo parcial indefinido</option>
            <option value="PAR-TEMP" ${emp && emp.contract_type === 'PAR-TEMP' ? 'selected' : ''}>Tiempo parcial temporal</option>
          </select>
        </div>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>Turno habitual</label>
          <select id="modal-emp-shift">${shiftOptionsHtml}</select>
        </div>
        <div class="form-group">
          <label>Estado</label>
          <select id="modal-emp-status">
            <option value="active" ${emp && (emp.status === 'active' || emp.is_active !== false) ? 'selected' : ''}>Activo</option>
            <option value="inactive" ${emp && (emp.status === 'inactive' || emp.is_active === false) ? 'selected' : ''}>Inactivo</option>
          </select>
        </div>
      </div>
      <div class="form-group">
        <label>PIN (4 dígitos) — solo si se cambia</label>
        <input type="text" id="modal-emp-pin" placeholder="Dejar vacío para mantener el actual" maxlength="4" pattern="[0-9]{4}">
      </div>
      <div class="form-group">
        <label>Tarjeta NFC (UID)</label>
        <div style="display:flex;gap:8px;align-items:center">
          <input type="text" id="modal-emp-nfc" value="${emp ? (emp.nfc_uid || '') : ''}" placeholder="Ej: 04:12:34:56:78:9A:BC" style="flex:1;font-family:ui-monospace,SF Mono,monospace;font-size:0.8125rem">
          <button type="button" class="btn btn-secondary btn-sm" onclick="scanNfc()" style="white-space:nowrap">Escanear NFC</button>
        </div>
        <div id="nfc-scan-result" style="margin-top:6px;font-size:0.75rem;color:rgba(0,0,0,0.45);min-height:0"></div>
      </div>
      <div class="form-group" id="qr-section" style="${id ? '' : 'display:none'}">
        <label>Codigo QR del empleado</label>
        <div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap">
          <div id="qr-code-container" style="background:#ffffff;border:1px solid rgba(0,0,0,0.08);border-radius:8px;padding:8px;display:inline-flex"></div>
          <div style="display:flex;flex-direction:column;gap:6px">
            <button type="button" class="btn btn-secondary btn-sm" onclick="downloadQR()">Descargar QR</button>
            <button type="button" class="btn btn-secondary btn-sm" onclick="printQR()">Imprimir QR</button>
          </div>
        </div>
      </div>
    `;
  } else if (type === 'turno') {
    const shift = id ? state.shifts.find(s => s.id === id) : null;
    title = id ? 'Editar turno' : 'Crear turno';
    fields = `
      <div class="form-group">
        <label>Nombre del turno</label>
        <input type="text" id="modal-shift-name" value="${shift ? shift.name : ''}" placeholder="Ej: Mañana">
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>Hora de inicio</label>
          <input type="time" id="modal-shift-start" value="${shift ? (shift.start_time || shift.start) : '07:00'}">
        </div>
        <div class="form-group">
          <label>Hora de fin</label>
          <input type="time" id="modal-shift-end" value="${shift ? (shift.end_time || shift.end) : '15:00'}">
        </div>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>Tipo de turno</label>
          <select id="modal-shift-type">
            <option value="morning" ${shift && shift.shift_type === 'morning' ? 'selected' : ''}>Mañana</option>
            <option value="afternoon" ${shift && shift.shift_type === 'afternoon' ? 'selected' : ''}>Tarde</option>
            <option value="night" ${shift && shift.shift_type === 'night' ? 'selected' : ''}>Noche</option>
            <option value="split" ${shift && (shift.shift_type === 'split' || shift.is_split) ? 'selected' : ''}>Partido</option>
            <option value="rotating" ${shift && shift.shift_type === 'rotating' ? 'selected' : ''}>Rotativo</option>
          </select>
        </div>
        <div class="form-group">
          <label>Tolerancia (minutos)</label>
          <input type="number" id="modal-shift-tolerance" value="${shift ? (shift.tolerance_min || shift.tolerance || 5) : 5}" min="0" max="60">
        </div>
      </div>
      <div class="form-group">
        <label>Color del turno</label>
        <div id="modal-shift-color" style="display:flex;gap:8px;flex-wrap:wrap">
          ${['#FF6B35','#FF9500','#FFCC00','#34C759','#007AFF','#5856D6','#AF52DE','#FF2D55','#A2845E','#8E8E93'].map(c => `<button type="button" data-color="${c}" class="color-swatch" style="width:32px;height:32px;border-radius:50%;background:${c};border:2px solid ${shift && shift.color === c ? '#1d1d1f' : 'transparent'};cursor:pointer;transition:all 200ms ease"></button>`).join('')}
        </div>
      </div>
    `;
  } else if (type === 'vacacion') {
    title = 'Nueva solicitud de vacaciones';
    const employees = state.employees;
    fields = `
      <div class="form-group">
        <label>Empleado</label>
        <select id="modal-vac-employee">
          <option value="">Seleccionar…</option>
          ${employees.map(e => `<option value="${e.id}">${e.full_name || e.name}</option>`).join('')}
        </select>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>Fecha inicio</label>
          <input type="date" id="modal-vac-start">
        </div>
        <div class="form-group">
          <label>Fecha fin</label>
          <input type="date" id="modal-vac-end">
        </div>
      </div>
      <div class="form-group">
        <label>Tipo</label>
        <select id="modal-vac-type">
          <option value="vacation">Vacaciones</option>
          <option value="personal_leave">Permiso personal</option>
          <option value="unpaid_leave">Permiso no retribuido</option>
        </select>
      </div>
      <div class="form-group">
        <label>Motivo (opcional)</label>
        <textarea id="modal-vac-reason" rows="2" placeholder="Motivo de la solicitud…"></textarea>
      </div>
    `;
  } else if (type === 'baja') {
    title = 'Registrar baja médica';
    const employees = state.employees;
    fields = `
      <div class="form-group">
        <label>Empleado</label>
        <select id="modal-leave-employee">
          <option value="">Seleccionar…</option>
          ${employees.map(e => `<option value="${e.id}">${e.full_name || e.name}</option>`).join('')}
        </select>
      </div>
      <div class="form-group">
        <label>Tipo de baja</label>
        <select id="modal-leave-type">
          <option value="EC">Enfermedad Común</option>
          <option value="ANL">Accidente No Laboral</option>
          <option value="AL">Accidente Laboral</option>
          <option value="EP">Enfermedad Profesional</option>
          <option value="MAT">Maternidad</option>
          <option value="PAT">Paternidad</option>
        </select>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>Fecha inicio</label>
          <input type="date" id="modal-leave-start">
        </div>
        <div class="form-group">
          <label>Fin previsto</label>
          <input type="date" id="modal-leave-end">
        </div>
      </div>
      <div class="form-group">
        <label>Diagnóstico (opcional)</label>
        <input type="text" id="modal-leave-diagnosis" placeholder="Código / descripción">
      </div>
    `;
  }

  container.innerHTML = `
    <div class="modal-overlay" onclick="if(event.target===this)closeModal()">
      <div class="modal ${wide ? 'modal-wide' : ''}">
        <div class="modal-header">
          <h3>${title}</h3>
          <button class="modal-close" onclick="closeModal()">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>
        <div class="modal-body">
          ${fields}
        </div>
        <div class="modal-footer">
          <button class="btn btn-ghost" onclick="closeModal()">Cancelar</button>
          <button class="btn btn-primary" onclick="saveModal('${type}',${id || 'null'})">Guardar</button>
        </div>
      </div>
    </div>
  `;

  // Color swatch handler for shift modal
  document.querySelectorAll('#modal-shift-color .color-swatch').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('#modal-shift-color .color-swatch').forEach(b => b.style.border = '2px solid transparent');
      btn.style.border = '2px solid #1d1d1f';
    });
  });

  // Generate QR if editing existing employee
  if (type === 'empleado' && id) {
    generateEmployeeQR(id);
  }
}

function closeModal() {
  document.getElementById('modal-container').innerHTML = '';
}

async function saveModal(type, id) {
  if (type === 'empleado') {
    const name = document.getElementById('modal-emp-name').value.trim();
    const lastname = document.getElementById('modal-emp-lastname').value.trim();
    const dni = document.getElementById('modal-emp-dni').value.trim();
    const nss = document.getElementById('modal-emp-nss').value.trim();
    const category = document.getElementById('modal-emp-category').value.trim();
    const contractType = document.getElementById('modal-emp-contract').value;
    const shiftId = document.getElementById('modal-emp-shift').value;
    const status = document.getElementById('modal-emp-status').value;
    const pin = document.getElementById('modal-emp-pin').value.trim();
    const nfcUid = document.getElementById('modal-emp-nfc').value.trim();

    if (!name) { showToast('El nombre es obligatorio', 'warning'); return; }

    const body = {
      first_name: name,
      last_name: lastname,
      full_name: `${name} ${lastname}`.trim(),
      dni: dni || undefined,
      nss: nss || undefined,
      professional_category: category || undefined,
      contract_type: contractType || undefined,
      default_shift_id: shiftId ? parseInt(shiftId) : null,
      status: status,
      is_active: status === 'active'
    };
    if (pin) body.pin = pin;
    if (nfcUid) body.nfc_uid = nfcUid;

    const result = id
      ? await api('PUT', `/employees/${id}`, body)
      : await api('POST', '/employees', body);

    if (result) {
      showToast(id ? 'Empleado actualizado' : 'Empleado creado', 'success');
      closeModal();
      loadEmpleados();
    } else {
      showToast('Error al guardar el empleado', 'error');
    }
  } else if (type === 'turno') {
    const name = document.getElementById('modal-shift-name').value.trim();
    const start = document.getElementById('modal-shift-start').value;
    const end = document.getElementById('modal-shift-end').value;
    const shiftType = document.getElementById('modal-shift-type').value;
    const tolerance = parseInt(document.getElementById('modal-shift-tolerance').value) || 5;
    const color = document.querySelector('#modal-shift-color .color-swatch[style*="border:2px solid #1d1d1f"]')?.dataset.color || '#FF6B35';

    if (!name || !start || !end) { showToast('Completa todos los campos', 'warning'); return; }

    const body = { name, start_time: start, end_time: end, shift_type: shiftType, tolerance_min: tolerance, color };
    const result = id
      ? await api('PUT', `/shifts/${id}`, body)
      : await api('POST', '/shifts', body);

    if (result) {
      showToast(id ? 'Turno actualizado' : 'Turno creado', 'success');
      closeModal();
      loadTurnos();
    } else {
      showToast('Error al guardar el turno', 'error');
    }
  } else if (type === 'vacacion') {
    const employeeId = document.getElementById('modal-vac-employee').value;
    const start = document.getElementById('modal-vac-start').value;
    const end = document.getElementById('modal-vac-end').value;
    const vacType = document.getElementById('modal-vac-type').value;
    const reason = document.getElementById('modal-vac-reason').value.trim();

    if (!employeeId || !start || !end) { showToast('Completa todos los campos', 'warning'); return; }

    const body = { employee_id: parseInt(employeeId), start_date: start, end_date: end, type: vacType, reason: reason || undefined };
    const result = await api('POST', '/vacations', body);
    if (result) {
      showToast('Solicitud creada', 'success');
      closeModal();
      loadVacaciones();
    } else {
      showToast('Error al crear la solicitud', 'error');
    }
  } else if (type === 'baja') {
    const employeeId = document.getElementById('modal-leave-employee').value;
    const leaveType = document.getElementById('modal-leave-type').value;
    const start = document.getElementById('modal-leave-start').value;
    const end = document.getElementById('modal-leave-end').value;
    const diagnosis = document.getElementById('modal-leave-diagnosis').value.trim();

    if (!employeeId || !start) { showToast('Completa los campos obligatorios', 'warning'); return; }

    const body = { employee_id: parseInt(employeeId), leave_type: leaveType, start_date: start, expected_end_date: end || undefined, diagnosis_code: diagnosis || undefined };
    const result = await api('POST', '/leave', body);
    if (result) {
      showToast('Baja registrada', 'success');
      closeModal();
      loadBajas();
    } else {
      showToast('Error al registrar la baja', 'error');
    }
  }
}

// ===== NFC & QR =====
function scanNfc() {
  const resultEl = document.getElementById('nfc-scan-result');
  const inputEl = document.getElementById('modal-emp-nfc');

  if ('NDEFReader' in window) {
    resultEl.textContent = 'Acerca la tarjeta NFC al dispositivo...';
    resultEl.style.color = '#FF6B35';
    try {
      const reader = new NDEFReader();
      reader.addEventListener('reading', ({ message }) => {
        for (const record of message.records) {
          if (record.recordType === 'text' || record.recordType === 'mime') {
            const decoder = new TextDecoder(record.encoding || 'utf-8');
            const text = decoder.decode(record.data);
            inputEl.value = text;
            resultEl.textContent = 'Tarjeta NFC leida correctamente';
            resultEl.style.color = '#34C759';
            return;
          }
        }
        // If no text record, use the serial number if available
        inputEl.value = reader.serialNumber || '';
        resultEl.textContent = 'Tarjeta NFC leida correctamente';
        resultEl.style.color = '#34C759';
      });
      reader.addEventListener('readingerror', () => {
        resultEl.textContent = 'Error al leer la tarjeta. Intentalo de nuevo.';
        resultEl.style.color = '#FF3B30';
      });
      reader.scan().catch(err => {
        resultEl.textContent = 'Error al iniciar el escaner: ' + err.message;
        resultEl.style.color = '#FF3B30';
      });
    } catch (err) {
      resultEl.textContent = 'Error: ' + err.message;
      resultEl.style.color = '#FF3B30';
    }
  } else {
    // Web NFC not available — show instructions
    resultEl.innerHTML = 'Web NFC no esta disponible en este navegador. Introduce el UID manualmente. El UID suele estar impreso en la tarjeta o puedes leerlo con una app NFC.';
    resultEl.style.color = 'rgba(0,0,0,0.45)';
    inputEl.focus();
  }
}

function generateEmployeeQR(employeeId) {
  const container = document.getElementById('qr-code-container');
  if (!container) return;
  const emp = state.employees.find(e => e.id === employeeId);
  if (!emp) return;
  const qrData = JSON.stringify({ id: emp.id, name: emp.full_name || emp.name });
  container.innerHTML = '';
  if (typeof QRCode !== 'undefined') {
    QRCode.toCanvas(qrData, { width: 120, margin: 1, color: { dark: '#1d1d1f', light: '#ffffff' } }, (err, canvas) => {
      if (err) {
        container.innerHTML = '<span class="text-xs text-muted">Error al generar QR</span>';
        return;
      }
      canvas.style.width = '120px';
      canvas.style.height = '120px';
      container.appendChild(canvas);
    });
  } else {
    container.innerHTML = '<span class="text-xs text-muted">Cargando libreria QR...</span>';
  }
}

function downloadQR() {
  const canvas = document.querySelector('#qr-code-container canvas');
  if (!canvas) { showToast('Genera primero el codigo QR', 'warning'); return; }
  const link = document.createElement('a');
  link.download = 'qr-empleado.png';
  link.href = canvas.toDataURL('image/png');
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  showToast('QR descargado', 'success');
}

function printQR() {
  const canvas = document.querySelector('#qr-code-container canvas');
  if (!canvas) { showToast('Genera primero el codigo QR', 'warning'); return; }
  const win = window.open('', '_blank');
  if (!win) { showToast('Permite ventanas emergentes para imprimir', 'warning'); return; }
  win.document.write('<!DOCTYPE html><html><head><title>Imprimir QR</title><style>body{display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0;font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#fff}img{max-width:90vw;max-height:90vh}</style></head><body>');
  win.document.write('<img src="' + canvas.toDataURL('image/png') + '" onload="window.print();window.close()">');
  win.document.write('</body></html>');
  win.document.close();
}

// ===== INIT =====
document.addEventListener('DOMContentLoaded', () => {
  const initialToken = getInitialToken();
  if (initialToken && !isTokenExpired(initialToken)) {
    api('GET', '/auth/me').then(user => {
      if (user) {
        state.user = user;
        state.isDemo = false;
        enterApp();
        return;
      }
      state.user = null;
    });
  }
  // Set default dates for reports
  const today = new Date();
  const monthAgo = new Date(today);
  monthAgo.setDate(monthAgo.getDate() - 30);
  const reportStart = document.getElementById('report-start');
  const reportEnd = document.getElementById('report-end');
  if (reportStart) reportStart.value = monthAgo.toISOString().slice(0,10);
  if (reportEnd) reportEnd.value = today.toISOString().slice(0,10);
});

// Exports for unit testing
export {
  state,
  api,
  navigate,
  filterEmpleados,
  renderEmpleadosPage,
  loadEmpleados,
  loadTurnos,
  loadDashboard,
  showToast,
  openModal,
  closeModal,
  saveModal,
  enterApp,
  logout,
  getInitialToken,
  isTokenExpired,
  decodeJwt,
  updateOnlineStatus,
  updateDemoBanner,
  filterFichajes,
  filterVacaciones,
  filterBajas
};
