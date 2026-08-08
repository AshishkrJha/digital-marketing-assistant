/**
 * ConversationAI – Frontend API Helper
 * Handles JWT storage, fetch wrappers, auth checks, and toast notifications.
 */

const API_BASE = '/api';

// ─── Token & User Storage ─────────────────────────────────────────────────────

const Auth = {
    getToken()   { return localStorage.getItem('access_token'); },
    getRefresh() { return localStorage.getItem('refresh_token'); },
    getUser()    {
        try { return JSON.parse(localStorage.getItem('user') || 'null'); }
        catch { return null; }
    },
    setAuth(access, refresh, user) {
        localStorage.setItem('access_token', access);
        localStorage.setItem('refresh_token', refresh);
        localStorage.setItem('user', JSON.stringify(user));
    },
    clear() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
    },
    isLoggedIn() { return !!this.getToken(); },
    getRole()    { return this.getUser()?.role || null; },
    isAdmin()    { return this.getRole() === 'admin'; },
    isModerator(){ return ['moderator','admin'].includes(this.getRole()); },
};

// ─── Core API Fetch ───────────────────────────────────────────────────────────

async function apiFetch(method, endpoint, data = null, isFormData = false) {
    const headers = { 'Authorization': `Bearer ${Auth.getToken()}` };
    if (!isFormData) headers['Content-Type'] = 'application/json';

    const options = { method, headers };
    if (data) options.body = isFormData ? data : JSON.stringify(data);

    const res = await fetch(`${API_BASE}${endpoint}`, options);

    // Try to parse JSON (even for errors)
    let json = null;
    try { json = await res.json(); } catch {}

    if (!res.ok) {
        // 401 → clear auth and redirect to login
        if (res.status === 401) {
            Auth.clear();
            window.location.href = '/';
            return;
        }
        const msg = json?.detail || json?.error || JSON.stringify(json) || `HTTP ${res.status}`;
        throw new Error(msg);
    }
    return json;
}

const API = {
    get:    (url)       => apiFetch('GET',    url),
    post:   (url, data) => apiFetch('POST',   url, data),
    put:    (url, data) => apiFetch('PUT',    url, data),
    patch:  (url, data) => apiFetch('PATCH',  url, data),
    delete: (url)       => apiFetch('DELETE', url),
};

// ─── Auth APIs ────────────────────────────────────────────────────────────────

const AuthAPI = {
    async login(email, password) {
        const res = await fetch(`${API_BASE}/users/auth/login/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password }),
        });
        const json = await res.json();
        if (!res.ok) throw new Error(json?.detail || json?.error || 'Login failed');
        Auth.setAuth(json.access, json.refresh, json.user);
        return json;
    },

    async register(data) {
        const res = await fetch(`${API_BASE}/users/auth/register/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        const json = await res.json();
        if (!res.ok) {
            const msg = Object.entries(json).map(([k,v]) => `${k}: ${v}`).join(' | ');
            throw new Error(msg);
        }
        return json;
    },

    async logout() {
        try { await API.post('/users/auth/logout/'); } catch {}
        Auth.clear();
        window.location.href = '/';
    },
};

// ─── User APIs ────────────────────────────────────────────────────────────────

const UserAPI = {
    getProfile:      ()     => API.get('/users/users/profile/'),
    updateProfile:   (data) => API.put('/users/users/profile/', data),
    changePassword:  (data) => API.post('/users/users/change_password', data),
    listUsers:       ()     => API.get('/users/users/'),
    updateUser:      (id, data) => API.patch(`/users/users/${id}/`, data),
};

// ─── Project APIs ─────────────────────────────────────────────────────────────

const ProjectAPI = {
    list:       ()          => API.get('/projects/'),
    create:     (data)      => API.post('/projects/', data),
    get:        (id)        => API.get(`/projects/${id}/`),
    update:     (id, data)  => API.put(`/projects/${id}/`, data),
    delete:     (id)        => API.delete(`/projects/${id}`),
    addMember:  (id, data)  => API.post(`/projects/${id}/add_member/`, data),
};

// ─── Conversation APIs ────────────────────────────────────────────────────────

const ConversationAPI = {
    list:         (projectId) => API.get(`/conversations/conversations/${projectId ? '?project_id='+projectId : ''}`),
    create:       (projectId, data) => API.post(`/conversations/conversations?project_id=${projectId}`, data),
    get:          (id)        => API.get(`/conversations/conversations/${id}`),
    messages:     (id)        => API.get(`/conversations/conversations/${id}/messages`),
    generateReply:(id, msg)   => API.post(`/conversations/conversations/${id}/generate_response`, { message_content: msg }),
};

// ─── Response APIs ────────────────────────────────────────────────────────────

const ResponseAPI = {
    list:   ()     => API.get('/conversations/responses/'),
    get:    (id)   => API.get(`/conversations/responses/${id}`),
    submit: (data) => API.post('/conversations/responses', data),
    delete: (id)   => API.delete(`/conversations/responses/${id}`),
};

// ─── Moderation APIs ──────────────────────────────────────────────────────────

const ModerationAPI = {
    queue:    ()           => API.get('/moderation/queue/'),
    getItem:  (id)         => API.get(`/moderation/queue/${id}`),
    approve:  (id, data)   => API.post(`/moderation/queue/${id}/approve`, { decision: 'approved', ...data }),
    reject:   (id, data)   => API.post(`/moderation/queue/${id}/reject`,  { decision: 'rejected', ...data }),
    history:  ()           => API.get('/moderation/history/'),
};

// ─── Route Guards ─────────────────────────────────────────────────────────────

function requireAuth() {
    if (!Auth.isLoggedIn()) {
        window.location.href = '/';
    }
}

function requireRole(...roles) {
    requireAuth();
    if (!roles.includes(Auth.getRole())) {
        showToast('Access denied: insufficient permissions', 'danger');
        setTimeout(() => { window.location.href = '/dashboard/'; }, 1500);
    }
}

function redirectIfLoggedIn() {
    if (Auth.isLoggedIn()) {
        const role = Auth.getRole();
        if (role === 'admin')      window.location.href = '/admin-panel/';
        else if (role === 'moderator') window.location.href = '/moderator/';
        else                           window.location.href = '/dashboard/';
    }
}

// ─── Toast Notifications ──────────────────────────────────────────────────────

function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const id = 'toast-' + Date.now();
    const icons = { success: '✓', danger: '✗', warning: '⚠', info: 'ℹ' };
    const icon = icons[type] || 'ℹ';

    const html = `
    <div id="${id}" class="toast align-items-center text-bg-${type} border-0 mb-2" role="alert" aria-live="assertive">
      <div class="d-flex">
        <div class="toast-body fw-semibold">
          <span class="me-2">${icon}</span>${message}
        </div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
      </div>
    </div>`;

    container.insertAdjacentHTML('beforeend', html);
    const toastEl = document.getElementById(id);
    const toast = new bootstrap.Toast(toastEl, { delay: 4000 });
    toast.show();
    toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
}

// ─── UI Helpers ───────────────────────────────────────────────────────────────

function setLoading(btnEl, loading, text = 'Loading…') {
    if (loading) {
        btnEl.dataset.origText = btnEl.innerHTML;
        btnEl.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span>${text}`;
        btnEl.disabled = true;
    } else {
        btnEl.innerHTML = btnEl.dataset.origText || text;
        btnEl.disabled = false;
    }
}

function statusBadge(status) {
    const map = {
        draft:     'secondary',
        submitted: 'warning',
        approved:  'success',
        rejected:  'danger',
        pending:   'warning',
        processed: 'secondary',
        active:    'success',
        inactive:  'secondary',
    };
    const color = map[status] || 'secondary';
    return `<span class="badge bg-${color} text-capitalize">${status}</span>`;
}

function roleBadge(role) {
    const map = { admin: 'danger', moderator: 'warning text-dark', user: 'primary' };
    return `<span class="badge bg-${map[role] || 'secondary'} text-capitalize">${role}</span>`;
}

function timeAgo(dateStr) {
    const now  = new Date();
    const then = new Date(dateStr);
    const sec  = Math.floor((now - then) / 1000);
    if (sec < 60)   return 'just now';
    if (sec < 3600) return `${Math.floor(sec/60)}m ago`;
    if (sec < 86400)return `${Math.floor(sec/3600)}h ago`;
    return `${Math.floor(sec/86400)}d ago`;
}

function escHtml(str) {
    return String(str)
        .replace(/&/g,'&amp;')
        .replace(/</g,'&lt;')
        .replace(/>/g,'&gt;')
        .replace(/"/g,'&quot;');
}

// ─── Fill Navbar User Info ────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    const user = Auth.getUser();
    if (!user) return;

    document.querySelectorAll('.navbar-user-name').forEach(el => {
        el.textContent = `${user.first_name || ''} ${user.last_name || ''}`.trim() || user.email;
    });
    document.querySelectorAll('.navbar-user-role').forEach(el => {
        el.textContent = user.role;
    });
    document.querySelectorAll('.navbar-user-email').forEach(el => {
        el.textContent = user.email;
    });
});
