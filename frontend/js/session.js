const Session = (() => {
  function maskMobile(mobile) {
    if (!mobile || mobile.length < 4) {
      return mobile || "";
    }
    const visible = mobile.slice(-4);
    return `Ending in ${visible}`;
  }

  async function requireAuth(redirectTo = "index.html") {
    try {
      const profile = await Api.me();
      return profile;
    } catch {
      window.location.href = redirectTo;
      return null;
    }
  }

  return { maskMobile, requireAuth };
})();
