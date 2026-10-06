(function () {
  document.addEventListener("DOMContentLoaded", () => {
  const params = new URLSearchParams(window.location.search);
  const slug = params.get("template");

  let quill;
  let templateSlug = slug;
  let templateLabel = "";
  let draftId = null;
  let autosaveTimer = null;
  let lastSavedHint = "";

  function patientField() {
    return document.getElementById("patient-name");
  }

  function syncPatientNameIntoEditor(name) {
    if (!quill || !name) {
      return;
    }
    const html = quill.root.innerHTML;
    const updated = html
      .replace(/Patient Name/g, name)
      .replace(/Dear Patient Name/g, `Dear ${name}`)
      .replace(/<strong>Patient Name<\/strong>/g, `<strong>${name}</strong>`);
    if (updated !== html) {
      quill.clipboard.dangerouslyPasteHTML(updated);
    }
  }

  function setAutosaveStatus(text) {
    const node = document.getElementById("autosave-status");
    if (node) {
      node.textContent = text;
    }
  }

  async function persistDraft() {
    if (!quill || !templateSlug) {
      return;
    }
    const payload = {
      template_slug: templateSlug,
      html_content: quill.root.innerHTML,
      patient_name: patientField().value.trim(),
    };
    try {
      const saved = await Api.saveDraft(payload);
      draftId = saved.id;
      lastSavedHint = Ui.formatDate(saved.updated_at);
      setAutosaveStatus(`Draft saved locally at ${lastSavedHint}`);
    } catch {
      setAutosaveStatus("Could not save draft. Check your connection.");
    }
  }

  function scheduleAutosave() {
    clearTimeout(autosaveTimer);
    autosaveTimer = setTimeout(persistDraft, 4500);
  }

  function openPreviewModal(base64Pdf) {
    const overlay = document.getElementById("preview-modal");
    const frame = document.getElementById("preview-frame");
    frame.src = `data:application/pdf;base64,${base64Pdf}`;
    overlay.hidden = false;
    document.body.classList.add("modal-open");
  }

  function closePreviewModal() {
    const overlay = document.getElementById("preview-modal");
    const frame = document.getElementById("preview-frame");
    overlay.hidden = true;
    frame.src = "";
    document.body.classList.remove("modal-open");
  }

  async function init() {
    await Session.requireAuth();
    const alertBox = document.getElementById("alert");

    if (!templateSlug) {
      window.location.href = "templates.html";
      return;
    }

    try {
      const template = await Api.getTemplate(templateSlug);
      templateLabel = template.label;
      document.getElementById("template-title").textContent = template.label;
      document.getElementById("template-description").textContent = template.description;
      document.title = `${template.label} | Doctor Letter`;

      quill = new Quill("#editor", {
        theme: "snow",
        modules: {
          toolbar: [
            [{ header: [2, 3, false] }],
            ["bold", "italic", "underline"],
            [{ list: "ordered" }, { list: "bullet" }],
            ["clean"],
          ],
        },
      });

      const existingDraft = await Api.getDraftForTemplate(templateSlug);
      if (existingDraft && existingDraft.html_content) {
        quill.clipboard.dangerouslyPasteHTML(existingDraft.html_content);
        patientField().value = existingDraft.patient_name || "";
        draftId = existingDraft.id;
        setAutosaveStatus(`Resumed local draft from ${Ui.formatDate(existingDraft.updated_at)}`);
      } else {
        quill.clipboard.dangerouslyPasteHTML(template.html);
        setAutosaveStatus("Draft will save locally as you edit.");
      }

      quill.on("text-change", scheduleAutosave);
      patientField().addEventListener("input", () => {
        syncPatientNameIntoEditor(patientField().value.trim());
        scheduleAutosave();
      });
    } catch (error) {
      Ui.showAlert(alertBox, error.message);
      return;
    }

    document.getElementById("preview-letter").addEventListener("click", async () => {
      Ui.clearAlert(alertBox);
      const button = document.getElementById("preview-letter");
      button.disabled = true;
      try {
        const result = await Api.previewLetter({
          template_slug: templateSlug,
          html_content: quill.root.innerHTML,
        });
        openPreviewModal(result.pdf_base64);
      } catch (error) {
        Ui.showAlert(alertBox, error.message);
      } finally {
        button.disabled = false;
      }
    });

    document.getElementById("close-preview").addEventListener("click", closePreviewModal);
    document.getElementById("preview-modal").addEventListener("click", (event) => {
      if (event.target.id === "preview-modal") {
        closePreviewModal();
      }
    });

    document.getElementById("save-letter").addEventListener("click", async () => {
      Ui.clearAlert(alertBox);
      const button = document.getElementById("save-letter");
      button.disabled = true;
      button.textContent = "Saving to secure storage…";

      try {
        await Api.finalizeLetter({
          template_slug: templateSlug,
          html_content: quill.root.innerHTML,
          patient_name: patientField().value.trim(),
          draft_id: draftId,
        });
        window.location.href = "history.html";
      } catch (error) {
        Ui.showAlert(alertBox, error.message);
        button.disabled = false;
        button.textContent = "Generate and save PDF";
      }
    });
  }

  init();
  });
})();
