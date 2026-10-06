const Session = (() => {
  function maskMobile(mobile) {
    if (!mobile || mobile.length < 4) {
      return mobile || "";
    }
    const visible = mobile.slice(-4);
    return `Signed in · ···${visible}`;
  }

  function refreshProfileInBackground() {
    Api.me()
      .then((profile) => {
        ProfileCache.write(profile);
      })
      .catch(() => {
        ProfileCache.clear();
        WorkspaceCache.clear();
      });
  }

  async function requireAuth(redirectTo = "index.html") {
    const cached = ProfileCache.read();
    if (cached) {
      refreshProfileInBackground();
      return cached;
    }
    try {
      const profile = await Api.me();
      ProfileCache.write(profile);
      return profile;
    } catch {
      ProfileCache.clear();
      WorkspaceCache.clear();
      window.location.href = redirectTo;
      return null;
    }
  }

  return { maskMobile, requireAuth };
})();
