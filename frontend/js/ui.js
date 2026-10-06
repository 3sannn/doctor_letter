const Ui = (() => {
  function showAlert(container, message, type = "error") {
    if (!container) {
      return;
    }
    container.innerHTML = "";
    const box = document.createElement("div");
    box.className = `alert alert-${type}`;
    box.setAttribute("role", "alert");
    box.textContent = message;
    container.appendChild(box);
  }

  function clearAlert(container) {
    if (container) {
      container.innerHTML = "";
    }
  }

  function formatDate(iso) {
    try {
      return new Intl.DateTimeFormat(undefined, {
        dateStyle: "medium",
        timeStyle: "short",
      }).format(new Date(iso));
    } catch {
      return iso;
    }
  }

  function setMobileLabel(profile) {
    const node = document.getElementById("mobile-label");
    if (node && profile) {
      node.textContent = Session.maskMobile(profile.mobile);
    }
  }

  function renderDraftList(container, drafts) {
    if (!container) {
      return;
    }
    if (!drafts.length) {
      container.innerHTML = '<li class="empty-state">No drafts yet.</li>';
      return;
    }
    container.innerHTML = "";
    drafts.forEach((draft) => {
      const item = document.createElement("li");
      item.className = "history-item";
      const title = draft.template_slug.replace(/-/g, " ");
      item.innerHTML = `
        <div>
          <h3>${title}</h3>
          <div class="history-meta">${draft.patient_name || "Patient"} · ${formatDate(draft.updated_at)}</div>
        </div>
      `;
      const resume = document.createElement("a");
      resume.className = "btn btn-secondary";
      resume.href = `editor.html?template=${encodeURIComponent(draft.template_slug)}`;
      resume.textContent = "Continue";
      item.appendChild(resume);
      container.appendChild(item);
    });
  }

  function setPageBusy(isBusy) {
    document.body.classList.toggle("page-busy", isBusy);
  }

  return {
    showAlert,
    clearAlert,
    formatDate,
    setMobileLabel,
    renderDraftList,
    setPageBusy,
  };
})();
