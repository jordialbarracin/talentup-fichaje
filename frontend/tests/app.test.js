import { describe, it, expect, beforeEach, vi } from 'vitest';
import {
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
  filterBajas,
} from '../src/app.js';

beforeEach(() => {
  clearFetchCalls();
  setFetchResponse(null);
  // Reset shared state before each test to avoid cross-test leakage
  Object.assign(state, {
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
    pendingConfirm: null,
  });
});

describe('JWT helpers', () => {
  it('decodeJwt returns payload from a valid token', () => {
    const payload = { sub: '123', exp: 1893456000, role: 'owner' };
    const token = `header.${btoa(JSON.stringify(payload)).replace(/=/g, '')}.sig`;
    expect(decodeJwt(token)).toEqual(payload);
  });

  it('decodeJwt returns null for malformed token', () => {
    expect(decodeJwt('not-a-jwt')).toBeNull();
    expect(decodeJwt('')).toBeNull();
  });

  it('isTokenExpired detects an expired token', () => {
    const past = Math.floor(Date.now() / 1000) - 60;
    const token = `h.${btoa(JSON.stringify({ exp: past })).replace(/=/g, '')}.s`;
    expect(isTokenExpired(token)).toBe(true);
  });

  it('isTokenExpired returns false for a future token', () => {
    const future = Math.floor(Date.now() / 1000) + 3600;
    const token = `h.${btoa(JSON.stringify({ exp: future })).replace(/=/g, '')}.s`;
    expect(isTokenExpired(token)).toBe(false);
  });

  it('isTokenExpired returns false when no exp claim', () => {
    const token = `h.${btoa(JSON.stringify({ sub: 'x' })).replace(/=/g, '')}.s`;
    expect(isTokenExpired(token)).toBe(false);
  });
});

describe('Cookie helper', () => {
  it('getInitialToken reads the access_token cookie', () => {
    document.cookie = 'access_token=my-token-value; path=/';
    expect(getInitialToken()).toBe('my-token-value');
  });

  it('getInitialToken returns null when cookie is absent', () => {
    // jsdom concatenates cookies, so clear them completely before asserting absence
    document.cookie = 'access_token=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/';
    expect(getInitialToken()).toBeNull();
  });
});

describe('api helper', () => {
  it('returns parsed JSON on successful response', async () => {
    const originalFetch = global.fetch;
    global.fetch = async (url, options) => {
      getFetchCalls().push({ url, options });
      return { ok: true, status: 200, json: async () => ({ ok: true, items: [] }) };
    };
    const result = await api('GET', '/shifts');
    global.fetch = originalFetch;
    expect(result).toEqual({ ok: true, items: [] });
    const calls = getFetchCalls();
    expect(calls).toHaveLength(1);
    expect(calls[0].url).toContain('/api/shifts');
    expect(calls[0].options.method).toBe('GET');
  });

  it('sends JSON body on POST and returns data', async () => {
    const originalFetch = global.fetch;
    global.fetch = async (url, options) => {
      getFetchCalls().push({ url, options });
      return { ok: true, status: 200, json: async () => ({ id: 42 }) };
    };
    const result = await api('POST', '/employees', { name: 'Ana' });
    global.fetch = originalFetch;
    expect(result).toEqual({ id: 42 });
    const calls = getFetchCalls();
    expect(calls[0].options.body).toBe(JSON.stringify({ name: 'Ana' }));
  });

  it('returns null and sets offline when fetch throws network error', async () => {
    const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const originalFetch = global.fetch;
    global.fetch = async () => { throw new Error('Failed to fetch'); };
    const result = await api('GET', '/employees');
    expect(result).toBeNull();
    expect(state.isOnline).toBe(false);
    global.fetch = originalFetch;
    consoleWarnSpy.mockRestore();
  });
});

describe('Online / demo indicators', () => {
  it('updateOnlineStatus shows connected when online and not demo', () => {
    state.isOnline = true;
    state.isDemo = false;
    updateOnlineStatus();
    expect(document.getElementById('online-text').textContent).toBe('Conectado');
    expect(document.getElementById('online-indicator').classList.contains('offline')).toBe(false);
  });

  it('updateOnlineStatus shows demo when demo mode active', () => {
    state.isOnline = true;
    state.isDemo = true;
    updateOnlineStatus();
    expect(document.getElementById('online-text').textContent).toBe('Demo');
    expect(document.getElementById('online-indicator').classList.contains('offline')).toBe(true);
  });

  it('updateDemoBanner hides banner when not demo', () => {
    state.isDemo = false;
    updateDemoBanner();
    expect(document.getElementById('demo-banner').classList.contains('hidden')).toBe(true);
  });

  it('updateDemoBanner shows banner when demo', () => {
    state.isDemo = true;
    updateDemoBanner();
    expect(document.getElementById('demo-banner').classList.contains('hidden')).toBe(false);
  });
});

describe('Toast', () => {
  it('renders a toast message in the container', () => {
    showToast('Mensaje de prueba', 'success');
    const container = document.getElementById('toast-container');
    expect(container.querySelectorAll('.toast')).toHaveLength(1);
    expect(container.textContent).toContain('Mensaje de prueba');
  });
});

describe('Navigation', () => {
  it('navigate updates active nav item and title', () => {
    navigate('empleados');
    expect(state.currentPage).toBe('empleados');
    expect(document.getElementById('navbar-title').textContent).toBe('Empleados');
    expect(document.querySelector('.nav-item[data-page="empleados"]').classList.contains('active')).toBe(true);
    expect(document.getElementById('page-empleados').classList.contains('hidden')).toBe(false);
  });
});

describe('Empleados', () => {
  it('loadEmpleados stores employees and renders them', async () => {
    const originalFetch = global.fetch;
    global.fetch = async (url) => {
      if (url.includes('/employees')) {
        return {
          ok: true,
          status: 200,
          json: async () => [
            { id: 1, full_name: 'Ana López', dni: '12345678A', is_active: true, shift_id: null },
            { id: 2, full_name: 'Luis García', dni: '87654321B', is_active: false, shift_id: null },
          ],
        };
      }
      return { ok: true, status: 200, json: async () => [] };
    };
    await loadEmpleados();
    global.fetch = originalFetch;
    expect(state.employees).toHaveLength(2);
    const rows = document.querySelectorAll('#empleados-table-body tr');
    expect(rows.length).toBeGreaterThan(0);
    expect(document.getElementById('empleados-table-body').textContent).toContain('Ana López');
  });

  it('filterEmpleados filters by search term', async () => {
    state.employees = [
      { id: 1, full_name: 'Ana López', is_active: true },
      { id: 2, full_name: 'Luis García', is_active: true },
    ];
    document.getElementById('emp-search').value = 'Ana';
    document.getElementById('emp-filter-status').value = '';
    document.getElementById('emp-filter-turno').innerHTML = '<option value="">Todos los turnos</option>';
    document.getElementById('emp-filter-turno').value = '';
    filterEmpleados();
    expect(state.empFiltered).toHaveLength(1);
    expect(state.empFiltered[0].full_name).toBe('Ana López');
  });

  it('renderEmpleadosPage renders empty state when no employees', () => {
    state.empFiltered = [];
    renderEmpleadosPage(1);
    expect(document.getElementById('empleados-table-body').textContent).toContain('No hay empleados');
  });
});

describe('Turnos', () => {
  it('loadTurnos renders shift cards', async () => {
    const originalFetch = global.fetch;
    global.fetch = async () => ({
      ok: true,
      status: 200,
      json: async () => [
        { id: 1, name: 'Mañana', start: '07:00', end: '15:00', color: '#FF6B35', shift_type: 'morning', tolerance_min: 5 },
      ],
    });
    await loadTurnos();
    global.fetch = originalFetch;
    expect(state.shifts).toHaveLength(1);
    expect(document.getElementById('turnos-grid').textContent).toContain('Mañana');
  });
});

describe('Dashboard', () => {
  it('loadDashboard renders stats from history and employees', async () => {
    const originalFetch = global.fetch;
    global.fetch = async (url) => {
      if (url.includes('/clock/history')) {
        return { ok: true, status: 200, json: async () => [{ employee_id: 1, employee_name: 'Ana López', type: 'in', time: '08:30', status: 'ok' }] };
      }
      if (url.includes('/employees')) {
        return { ok: true, status: 200, json: async () => [{ id: 1, full_name: 'Ana López', is_active: true }] };
      }
      if (url.includes('/overtime')) {
        return { ok: true, status: 200, json: async () => [{ total_minutes: 90 }] };
      }
      if (url.includes('/vacations')) {
        return { ok: true, status: 200, json: async () => [] };
      }
      return { ok: true, status: 200, json: async () => ({}) };
    };
    await loadDashboard();
    global.fetch = originalFetch;
    expect(document.getElementById('stat-empleados').textContent).toBe('1');
    expect(document.getElementById('stat-fichajes').textContent).toBe('1');
    expect(document.getElementById('stat-extras').textContent).toBe('1.5h');
  });
});

describe('Modal', () => {
  it('openModal renders employee modal fields', () => {
    state.shifts = [{ id: 1, name: 'Mañana' }];
    state.employees = [{ id: 1, full_name: 'Ana López' }];
    openModal('empleado', 1);
    expect(document.getElementById('modal-emp-name').value).toBe('Ana López');
    expect(document.querySelector('.modal-header h3').textContent).toBe('Editar empleado');
  });

  it('closeModal clears modal container', () => {
    state.shifts = [{ id: 1, name: 'Mañana' }];
    openModal('empleado');
    closeModal();
    expect(document.getElementById('modal-container').innerHTML).toBe('');
  });
});

describe('Auth flow', () => {
  it('enterApp switches from login to app and renders avatar', () => {
    state.user = { name: 'Jordi', email: 'jordi@talentup.es', role: 'owner', tenant_id: 'demo' };
    enterApp();
    expect(document.getElementById('login-screen').classList.contains('hidden')).toBe(true);
    expect(document.getElementById('app').classList.contains('hidden')).toBe(false);
    expect(document.getElementById('navbar-avatar').textContent).toBe('J');
    expect(document.getElementById('navbar-name').textContent).toBe('Jordi');
  });

  it('logout clears user and returns to login screen', async () => {
    const originalFetch = global.fetch;
    global.fetch = async () => ({ ok: true, status: 200, text: async () => '' });
    state.user = { name: 'Jordi' };
    await logout();
    global.fetch = originalFetch;
    expect(state.user).toBeNull();
    expect(document.getElementById('app').classList.contains('hidden')).toBe(true);
    expect(document.getElementById('login-screen').classList.contains('hidden')).toBe(false);
  });
});

describe('Fichajes filter', () => {
  it('filterFichajes filters by date and employee', () => {
    state.clockHistory = [
      { id: 1, employee_id: 1, employee_name: 'Ana', type: 'in', status: 'ok', timestamp: '2026-07-20T08:30:00' },
      { id: 2, employee_id: 2, employee_name: 'Luis', type: 'out', status: 'ok', timestamp: '2026-07-21T18:00:00' },
    ];
    document.getElementById('clock-filter-date').value = '2026-07-20';
    document.getElementById('clock-filter-empleado').innerHTML = '<option value="">Todos</option><option value="1">Ana</option>';
    document.getElementById('clock-filter-empleado').value = '';
    document.getElementById('clock-filter-tipo').value = '';
    document.getElementById('clock-filter-estado').value = '';
    filterFichajes();
    expect(state.clockFiltered).toHaveLength(1);
    expect(state.clockFiltered[0].employee_name).toBe('Ana');
  });
});

describe('Vacaciones filter', () => {
  it('filterVacaciones filters by status', () => {
    state.vacations = [
      { id: 1, employee_name: 'Ana', type: 'vacation', status: 'pending' },
      { id: 2, employee_name: 'Luis', type: 'vacation', status: 'approved' },
    ];
    document.getElementById('vac-search').value = '';
    document.getElementById('vac-filter-status').value = 'approved';
    filterVacaciones();
    expect(state.vacFiltered).toHaveLength(1);
    expect(state.vacFiltered[0].status).toBe('approved');
  });
});

describe('Bajas filter', () => {
  it('filterBajas filters by leave type', () => {
    state.leaves = [
      { id: 1, employee_name: 'Ana', leave_type: 'EC', status: 'active' },
      { id: 2, employee_name: 'Luis', leave_type: 'MAT', status: 'active' },
    ];
    document.getElementById('leave-search').value = '';
    document.getElementById('leave-filter-status').value = '';
    document.getElementById('leave-filter-type').value = 'MAT';
    filterBajas();
    expect(state.leaveFiltered).toHaveLength(1);
    expect(state.leaveFiltered[0].leave_type).toBe('MAT');
  });
});
