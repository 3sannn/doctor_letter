function escapeTemplateText(value) {
  const node = document.createElement("span");
  node.textContent = value == null ? "" : String(value);
  return node.innerHTML;
}

document.addEventListener("DOMContentLoaded", () => {
  (async function initTemplatesPage() {
    const sessionProfile = await Session.requireAuth();
    if (sessionProfile) {
      Ui.setMobileLabel(sessionProfile);
    }
    const root = document.getElementById("template-sections");
    const alertBox = document.getElementById("alert");

    const groupLabels = {
      clinical: "Clinical letters",
      certificates: "Certificates and leave",
      administrative: "Administrative",
      general: "General",
      custom: "Custom",
    };

    root.innerHTML = '<p class="list-loading" aria-busy="true">Loading templates…</p>';

    try {
      const templates = await Api.listTemplates();
      TemplateCache.write(templates);

      const byGroup = {};
      templates.forEach((item) => {
        if (item.slug === "blank-letter") {
          return;
        }
        const group = item.group || "clinical";
        if (!byGroup[group]) {
          byGroup[group] = [];
        }
        byGroup[group].push(item);
      });

      root.innerHTML = "";
      Object.keys(groupLabels).forEach((groupKey) => {
        const items = byGroup[groupKey];
        if (!items || !items.length) {
          return;
        }

        const section = document.createElement("section");
        section.className = "template-group";
        section.innerHTML = `<h2 class="section-title">${groupLabels[groupKey]}</h2>`;

        const grid = document.createElement("div");
        grid.className = "grid templates motion-stagger";

        items.forEach((item) => {
          const button = document.createElement("button");
          button.type = "button";
          button.className = "template-tile";
          button.innerHTML = `
            <span class="template-tile-icon">${Icons.svg("document", "icon icon-muted")}</span>
            <strong>${escapeTemplateText(item.label)}</strong>
            <span>${escapeTemplateText(item.description)}</span>
          `;
          button.addEventListener("click", () => {
            window.location.href = Paths.editor(item.slug);
          });
          grid.appendChild(button);
        });

        section.appendChild(grid);
        root.appendChild(section);
      });
      if (typeof AppNav !== "undefined") {
        AppNav.applyMotionStagger();
      }
    } catch (error) {
      Ui.showAlert(alertBox, error.message);
    }
  })();
});
