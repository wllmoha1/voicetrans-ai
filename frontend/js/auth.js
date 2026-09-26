// Authentication Helpers for AI Voice Call Translator

const Auth = {
  getToken() {
    return localStorage.getItem("voice_call_token");
  },

  setToken(token) {
    localStorage.setItem("voice_call_token", token);
  },

  getUser() {
    const userStr = localStorage.getItem("voice_call_user");
    try {
      return userStr ? JSON.parse(userStr) : null;
    } catch {
      return null;
    }
  },

  setUser(user) {
    localStorage.setItem("voice_call_user", JSON.stringify(user));
  },

  logout() {
    localStorage.removeItem("voice_call_token");
    localStorage.removeItem("voice_call_user");
    window.location.href = "/login";
  },

  async checkAuth(redirect = true) {
    const token = this.getToken();
    if (!token) {
      if (redirect) window.location.href = "/login";
      return null;
    }

    try {
      const res = await fetch("/api/auth/me", {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) {
        const user = await res.json();
        this.setUser(user);
        return user;
      } else {
        if (redirect) this.logout();
        return null;
      }
    } catch (e) {
      console.warn("Auth check failed:", e);
      return this.getUser();
    }
  },

  async authFetch(url, options = {}) {
    const token = this.getToken();
    const headers = options.headers || {};
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    return fetch(url, { ...options, headers });
  }
};
