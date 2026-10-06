const ProfileCache = (() => {
  const KEY = "dl_profile";
  const AT = "dl_profile_at";
  const TTL_MS = 3 * 60 * 1000;

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

  function write(profile) {
    sessionStorage.setItem(KEY, JSON.stringify(profile));
    sessionStorage.setItem(AT, String(Date.now()));
  }

  function clear() {
    sessionStorage.removeItem(KEY);
    sessionStorage.removeItem(AT);
  }

  return { read, write, clear };
})();
