let csrf = '';
let user = null;
let receiveState = () => {};
export const apiClient = {
  enabled: () => typeof window !== 'undefined' && window.LUIGI_API === true,
  user: () => user,
  onState(callback) {
    receiveState = callback;
  },
  async request(path, { method = 'GET', body } = {}) {
    const response = await fetch('/api' + path, {
      method,
      credentials: 'same-origin',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Protection': '1',
        ...(csrf ? { 'X-CSRF-Token': csrf } : {}),
      },
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      const detail = Array.isArray(error.detail)
        ? error.detail.map((e) => e.msg).join(' ')
        : error.detail;
      const failure = new Error(
        detail || `The server returned ${response.status}. Please try again.`,
      );
      failure.status = response.status;
      throw failure;
    }
    return response.status === 204 ? null : response.json();
  },
  async restore() {
    try {
      const session = await this.request('/auth/me');
      user = session.user;
      csrf = session.csrf_token;
      await this.refresh();
    } catch (error) {
      if (error.status !== 401) throw error;
      user = null;
      csrf = '';
    }
  },
  async login(username, password) {
    const aliases = {
      Luigi: 'luigi@example.test',
      Sam: 'sam@example.test',
      Robin: 'robin@example.test',
    };
    const session = await this.request('/auth/login', {
      method: 'POST',
      body: { email: aliases[username.trim()] || username.trim(), password },
    });
    user = session.user;
    csrf = session.csrf_token;
    if (user.must_change_password)
      throw new Error(
        'This account needs a password change. Use the team account-management tools before signing in.',
      );
    await this.refresh();
    return user;
  },
  async logout() {
    if (user) await this.request('/auth/logout', { method: 'POST' });
    user = null;
    csrf = '';
  },
  async register(body) {
    return this.request('/auth/register', { method: 'POST', body });
  },
  async refresh() {
    if (!user) return;
    const result = await this.request('/bridge/state');
    receiveState(result.state);
  },
  async command(action, data) {
    if (!user) throw new Error('Please sign in before continuing.');
    const result = await this.request('/bridge/command', {
      method: 'POST',
      body: { action, data },
    });
    receiveState(result.state);
    return result.result;
  },
};
