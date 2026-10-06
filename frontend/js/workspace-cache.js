const WorkspaceCache = (() => {
  const KEY = "dl_workspace";
  const AT = "dl_workspace_at";
  const TTL_MS = 2 * 60 * 1000;

  function read() {
    try {
      const savedAt = Number(sessionStorage.getItem(AT));
      if (!savedAt || Date.now() - savedAt > TTL_MS) {
        return null;
      }
      const raw = sessionStorage.getItem(KEY);
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  }

  function write(payload) {
    sessionStorage.setItem(KEY, JSON.stringify(payload));
    sessionStorage.setItem(AT, String(Date.now()));
    if (payload && payload.profile) {
      ProfileCache.write(payload.profile);
    }
  }

  function clear() {
    sessionStorage.removeItem(KEY);
    sessionStorage.removeItem(AT);
  }

  return { read, write, clear };
})();
