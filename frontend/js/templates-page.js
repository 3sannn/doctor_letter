document.addEventListener("DOMContentLoaded", () => {
  (async function initTemplatesPage() {
    await Session.requireAuth();
    const root = document.getElementById("template-sections");
    const alertBox = document.getElementById("alert");

    const groupLabels = {
      clinical: "Clinical letters",
      certificates: "Certificates and leave",
      administrative: "Administrative",
      general: "General",
      custom: "Custom",
    };

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
        grid.className = "grid templates";

        items.forEach((item) => {
          const button = document.createElement("button");
          button.type = "button";
          button.className = "template-tile";
          button.innerHTML = `<strong>${item.label}</strong><span>${item.description}</span>`;
          button.addEventListener("click", () => {
            window.location.href = `editor.html?template=${encodeURIComponent(item.slug)}`;
          });
          grid.appendChild(button);
        });

        section.appendChild(grid);
        root.appendChild(section);
      });
    } catch (error) {
      Ui.showAlert(alertBox, error.message);
    }
  })();
});
