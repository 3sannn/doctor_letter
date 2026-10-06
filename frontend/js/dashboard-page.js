document.addEventListener("DOMContentLoaded", () => {
  (async function initDashboard() {
    const cachedWorkspace = WorkspaceCache.read();
    if (cachedWorkspace) {
      Ui.setMobileLabel(cachedWorkspace.profile);
      Ui.renderDraftList(document.getElementById("draft-list"), cachedWorkspace.drafts || []);
    }

    const profile = await Session.requireAuth();
    if (!profile) {
      return;
    }

    Ui.setMobileLabel(profile);

    try {
      const workspace = await Api.loadWorkspace();
      Ui.renderDraftList(document.getElementById("draft-list"), workspace.drafts || []);
    } catch {
      if (!cachedWorkspace) {
        document.getElementById("draft-list").innerHTML =
          '<li class="empty-state">Could not load drafts.</li>';
      }
    }

    document.getElementById("sign-out").addEventListener("click", async () => {
      await Api.logout();
      window.location.href = "index.html";
    });
  })();
});
