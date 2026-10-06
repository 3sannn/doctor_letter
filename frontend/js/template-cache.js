const TemplateCache = (() => {
  const KEY = "dl_templates_v2";
  const AT = "dl_templates_at_v2";
  const TTL_MS = 30 * 60 * 1000;

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

  function write(list) {
    sessionStorage.setItem(KEY, JSON.stringify(list));
    sessionStorage.setItem(AT, String(Date.now()));
  }

  return { read, write };
})();
