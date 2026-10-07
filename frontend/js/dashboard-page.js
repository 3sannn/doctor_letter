document.addEventListener("DOMContentLoaded", () => {
  (async function initDashboard() {
    const draftList = document.getElementById("draft-list");
    const draftAlert = document.getElementById("draft-alert");

    const cachedWorkspace = WorkspaceCache.read();
    if (cachedWorkspace) {
      Ui.setMobileLabel(cachedWorkspace.profile);
      Ui.setWorkspaceGreeting(cachedWorkspace.profile);
      Ui.renderDraftList(draftList, cachedWorkspace.drafts || [], draftAlert);
    }

    const profile = await Session.requireAuth();
    if (!profile) {
      return;
    }

    Ui.setMobileLabel(profile);
    Ui.setWorkspaceGreeting(profile);

    try {
      const workspace = await Api.loadWorkspace();
      Ui.setWorkspaceGreeting(workspace.profile);
      Ui.renderDraftList(draftList, workspace.drafts || [], draftAlert);
    } catch {
      if (!cachedWorkspace) {
        draftList.innerHTML = "";
        Ui.showAlert(draftAlert, "Could not load drafts. Refresh the page to try again.");
      }
    }

    document.getElementById("sign-out").addEventListener("click", async () => {
      await Api.logout();
      window.location.href = "index.html";
    });
  })();
});
