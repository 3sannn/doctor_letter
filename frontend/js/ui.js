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

  return { showAlert, clearAlert, formatDate };
})();
