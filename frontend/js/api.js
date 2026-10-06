const Api = (() => {
  const base = "";

  async function request(path, options = {}) {
    const response = await fetch(`${base}${path}`, {
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
      ...options,
    });

    let data = null;
    const text = await response.text();
    if (text) {
      try {
        data = JSON.parse(text);
      } catch {
        data = text;
      }
    }

    if (!response.ok) {
      let message = "Something went wrong. Please try again.";
      if (data && data.detail) {
        if (Array.isArray(data.detail)) {
          message = data.detail.map((item) => item.msg || item).join(" ");
        } else if (typeof data.detail === "string") {
          message = data.detail;
        } else {
          message = JSON.stringify(data.detail);
        }
      }
      throw new Error(message);
    }

    return data;
  }

  return {
    startSession(mobile) {
      return request("/api/session", {
        method: "POST",
        body: JSON.stringify({ mobile }),
      });
    },
    logout() {
      return request("/api/session/logout", { method: "POST" });
    },
    me() {
      return request("/api/session/me");
    },
    getProfile() {
      return request("/api/profile");
    },
    saveProfile(payload) {
      return request("/api/profile", {
        method: "PUT",
        body: JSON.stringify(payload),
      });
    },
    listTemplates() {
      return request("/api/templates");
    },
    getTemplate(slug) {
      return request(`/api/templates/${encodeURIComponent(slug)}`);
    },
    listDrafts() {
      return request("/api/drafts");
    },
    getDraftForTemplate(slug) {
      return request(`/api/drafts/by-template/${encodeURIComponent(slug)}`);
    },
    saveDraft(payload) {
      return request("/api/drafts", {
        method: "PUT",
        body: JSON.stringify(payload),
      });
    },
    deleteDraft(id) {
      return request(`/api/drafts/${encodeURIComponent(id)}`, { method: "DELETE" });
    },
    listLetters() {
      return request("/api/letters");
    },
    previewLetter(payload) {
      return request("/api/letters/preview", {
        method: "POST",
        body: JSON.stringify(payload),
      });
    },
    finalizeLetter(payload) {
      return request("/api/letters/finalize", {
        method: "POST",
        body: JSON.stringify(payload),
      });
    },
    downloadLetter(id) {
      return request(`/api/letters/${encodeURIComponent(id)}/download`);
    },
    deleteLetter(id) {
      return request(`/api/letters/${encodeURIComponent(id)}`, { method: "DELETE" });
    },
  };
})();
