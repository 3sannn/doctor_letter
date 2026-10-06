const Session = (() => {
  function maskMobile(mobile) {
    if (!mobile || mobile.length < 4) {
      return mobile || "";
    }
    const visible = mobile.slice(-4);
    return `Ending in ${visible}`;
  }

  async function requireAuth(redirectTo = "index.html") {
    const cached = ProfileCache.read();
    if (cached) {
      return cached;
    }
    try {
      const profile = await Api.me();
      ProfileCache.write(profile);
      return profile;
    } catch {
      ProfileCache.clear();
      window.location.href = redirectTo;
      return null;
    }
  }

  async function refreshAuth() {
    try {
      const profile = await Api.me();
      ProfileCache.write(profile);
      return profile;
    } catch {
      ProfileCache.clear();
      return null;
    }
  }

  return { maskMobile, requireAuth, refreshAuth };
})();
