document.addEventListener("DOMContentLoaded", () => {
  (async function initHistory() {
    await Session.requireAuth();
    const list = document.getElementById("history-list");
    const alertBox = document.getElementById("alert");
    const searchInput = document.getElementById("history-search");
    const countNode = document.getElementById("history-count");

    let letters = [];

    function renderList(items) {
      list.innerHTML = "";
      const query = (searchInput?.value || "").trim().toLowerCase();

      const filtered = query
        ? items.filter((letter) => {
            const hay = `${letter.template_label} ${letter.patient_name || ""}`.toLowerCase();
            return hay.includes(query);
          })
        : items;

      if (countNode) {
        countNode.textContent = filtered.length
          ? `${filtered.length} letter${filtered.length === 1 ? "" : "s"}`
          : items.length
            ? "No matches"
            : "";
      }

      if (!items.length) {
        list.appendChild(
          Ui.emptyStateElement({
            title: "No letters yet",
            body: "Your finalized letters will appear here with the date and patient label.",
            actionLabel: "Create a letter",
            actionHref: Paths.templates,
            icon: "document",
          })
        );
        return;
      }

      if (!filtered.length) {
        list.appendChild(
          Ui.emptyStateElement({
            title: "No matches",
            body: "Try a different search term or clear the filter.",
            icon: "search",
          })
        );
        return;
      }

      filtered.forEach((letter) => {
        const item = document.createElement("li");
        item.className = "history-item";
        const patient = Ui.escapeHtml(letter.patient_name || "Patient");
        const label = Ui.escapeHtml(letter.template_label);
        item.innerHTML = `
          <div class="history-item-main">
            <span class="history-item-icon">${Icons.svg("document", "icon icon-muted")}</span>
            <div>
              <h3>${label}</h3>
              <div class="history-meta">${patient} · ${Ui.formatDate(letter.created_at)}</div>
            </div>
          </div>
        `;
        const actions = document.createElement("div");
        actions.className = "btn-row history-item-actions btn-row--grid";

        const download = document.createElement("button");
        download.type = "button";
        download.className = "btn btn-secondary";
        download.innerHTML = `${Icons.svg("download", "icon icon-inline")}<span>Download</span>`;
        download.addEventListener("click", async () => {
          Ui.clearAlert(alertBox);
          Ui.setButtonLoading(download, true, "Preparing…");
          try {
            const link = await Api.downloadLetter(letter.id);
            window.open(link.url, "_blank", "noopener,noreferrer");
          } catch (error) {
            Ui.showAlert(
              alertBox,
              "We could not prepare the download link. Please try again in a moment."
            );
          } finally {
            Ui.setButtonLoading(download, false);
          }
        });

        const remove = document.createElement("button");
        remove.type = "button";
        remove.className = "btn btn-ghost btn-danger-text";
        remove.innerHTML = `${Icons.svg("trash", "icon icon-inline")}<span>Delete</span>`;
        remove.addEventListener("click", async () => {
          if (!window.confirm("Remove this letter from your history and from storage?")) {
            return;
          }
          Ui.clearAlert(alertBox);
          Ui.setButtonLoading(remove, true);
          try {
            await Api.deleteLetter(letter.id);
            letters = letters.filter((row) => row.id !== letter.id);
            renderList(letters);
          } catch {
            Ui.showAlert(alertBox, "We could not delete this letter. Please try again.");
            Ui.setButtonLoading(remove, false);
          }
        });

        actions.appendChild(download);
        actions.appendChild(remove);
        item.appendChild(actions);
        list.appendChild(item);
      });
    }

    list.innerHTML = '<li class="list-loading" aria-busy="true">Loading letters…</li>';

    try {
      letters = await Api.listLetters();
      renderList(letters);
    } catch {
      list.innerHTML = "";
      Ui.showAlert(
        alertBox,
        "We could not load your letter history. Your finalized letters are still safe—please refresh the page."
      );
    }

    if (searchInput) {
      searchInput.addEventListener("input", () => renderList(letters));
    }
  })();
});
