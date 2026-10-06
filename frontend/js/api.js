const Api = (() => {
  function request(path, options) {
    return HttpClient.request(path, options);
  }

  function afterSignIn(body) {
    ProfileCache.write({
      mobile: body.mobile,
      full_name: "",
      registration_number: "",
      clinic_name: "",
      clinic_address: "",
    });
    WorkspaceCache.clear();
    return body;
  }

  return {
    startSession(mobile, company = "") {
      return request("/api/session", {
        method: "POST",
        body: JSON.stringify({ mobile, company }),
      }).then(afterSignIn);
    },
    logout() {
      ProfileCache.clear();
      WorkspaceCache.clear();
      return request("/api/session/logout", { method: "POST" });
    },
    me() {
      return request("/api/session/me");
    },
    loadWorkspace() {
      return request("/api/workspace").then((payload) => {
        WorkspaceCache.write(payload);
        return payload;
      });
    },
    loadEditor(slug) {
      return request(`/api/editor/${encodeURIComponent(slug)}`);
    },
    getProfile() {
      return request("/api/profile");
    },
    saveProfile(payload) {
      return request("/api/profile", {
        method: "PUT",
        body: JSON.stringify(payload),
      }).then((profile) => {
        ProfileCache.write(profile);
        WorkspaceCache.clear();
        return profile;
      });
    },
    listTemplates() {
      const cached = TemplateCache.read();
      if (cached) {
        return Promise.resolve(cached);
      }
      return request("/api/templates").then((list) => {
        TemplateCache.write(list);
        return list;
      });
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
      }).then((letter) => {
        WorkspaceCache.clear();
        return letter;
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
