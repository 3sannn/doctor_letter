const Ui = (() => {
  function escapeHtml(value) {
    const node = document.createElement("span");
    node.textContent = value == null ? "" : String(value);
    return node.innerHTML;
  }

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

  function setWorkspaceGreeting(profile) {
    const node = document.getElementById("workspace-greeting");
    if (!node || !profile) {
      return;
    }
    const name = (profile.full_name || "").trim();
    if (name) {
      const first = name.split(/\s+/)[0];
      node.textContent = `Good day, ${first}`;
      node.hidden = false;
    } else {
      node.hidden = true;
    }
  }

  function emptyStateElement({ title, body, actionLabel, actionHref, icon = "document" }) {
    const li = document.createElement("li");
    li.className = "empty-state-block";
    const iconHtml = typeof Icons !== "undefined" ? Icons.svg(icon, "icon icon-empty") : "";
    let action = "";
    if (actionLabel && actionHref) {
      action = `<p class="empty-state-action"><a class="btn btn-primary" href="${escapeHtml(actionHref)}">${escapeHtml(actionLabel)}</a></p>`;
    }
    li.innerHTML = `
      ${iconHtml}
      <p class="empty-state-title">${escapeHtml(title)}</p>
      <p class="empty-state-body">${escapeHtml(body)}</p>
      ${action}
    `;
    return li;
  }

  function renderDraftList(container, drafts, alertBox) {
    if (!container) {
      return;
    }
    if (!drafts.length) {
      container.innerHTML = "";
      container.appendChild(
        emptyStateElement({
          title: "No drafts in progress",
          body: "When you start a letter, it will appear here until you finalize it.",
          actionLabel: "Create new letter",
          actionHref: Paths.templates,
          icon: "pen",
        })
      );
      return;
    }
    container.innerHTML = "";
    drafts.forEach((draft) => {
      const item = document.createElement("li");
      item.className = "history-item";
      const title = escapeHtml(draft.template_slug.replace(/-/g, " "));
      const patient = escapeHtml(draft.patient_name || "Patient");
      item.innerHTML = `
        <div class="history-item-main">
          <span class="history-item-icon">${Icons.svg("pen", "icon icon-muted")}</span>
          <div>
            <h3>${title}</h3>
            <div class="history-meta">${patient} · ${formatDate(draft.updated_at)}</div>
          </div>
        </div>
      `;
      const actions = document.createElement("div");
      actions.className = "btn-row history-item-actions btn-row--grid";

      const resume = document.createElement("a");
      resume.className = "btn btn-secondary";
      resume.href = Paths.editor(draft.template_slug);
      resume.innerHTML = `${Icons.svg("chevronRight", "icon icon-inline")}<span>Continue</span>`;

      const remove = document.createElement("button");
      remove.type = "button";
      remove.className = "btn btn-ghost btn-danger-text";
      remove.innerHTML = `${Icons.svg("trash", "icon icon-inline")}<span>Remove</span>`;
      remove.addEventListener("click", async () => {
        if (!window.confirm("Remove this draft? You will lose the unsaved letter text for this template.")) {
          return;
        }
        clearAlert(alertBox);
        setButtonLoading(remove, true);
        try {
          await Api.deleteDraft(draft.id);
          WorkspaceCache.clear();
          const remaining = drafts.filter((row) => row.id !== draft.id);
          renderDraftList(container, remaining, alertBox);
        } catch {
          showAlert(alertBox, "We could not remove this draft. Please try again.");
          setButtonLoading(remove, false);
        }
      });

      actions.appendChild(resume);
      actions.appendChild(remove);
      item.appendChild(actions);
      container.appendChild(item);
    });
  }

  function setButtonLoading(button, isLoading, loadingLabel) {
    if (!button) {
      return;
    }
    if (isLoading) {
      if (!button.dataset.defaultLabel) {
        button.dataset.defaultLabel = button.innerHTML;
      }
      button.disabled = true;
      button.setAttribute("aria-busy", "true");
      if (loadingLabel) {
        button.textContent = loadingLabel;
      }
    } else {
      button.disabled = false;
      button.removeAttribute("aria-busy");
      if (button.dataset.defaultLabel) {
        button.innerHTML = button.dataset.defaultLabel;
      }
    }
  }

  function setPageBusy(isBusy) {
    document.body.classList.toggle("page-busy", isBusy);
  }

  return {
    escapeHtml,
    showAlert,
    clearAlert,
    formatDate,
    setMobileLabel,
    setWorkspaceGreeting,
    emptyStateElement,
    renderDraftList,
    setButtonLoading,
    setPageBusy,
  };
})();
