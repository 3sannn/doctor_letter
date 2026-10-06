(function () {
  document.addEventListener("DOMContentLoaded", () => {
    const params = new URLSearchParams(window.location.search);
    const slug = params.get("template");

    let quill;
    let templateSlug = slug;
    let draftId = null;
    let autosaveTimer = null;

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
        setAutosaveStatus(`Draft saved · ${Ui.formatDate(saved.updated_at)}`);
      } catch {
        setAutosaveStatus("Draft not saved. Check your connection.");
      }
    }

    function scheduleAutosave() {
      clearTimeout(autosaveTimer);
      autosaveTimer = setTimeout(persistDraft, 6000);
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

      Ui.setPageBusy(true);
      try {
        const setup = await Api.loadEditor(templateSlug);
        document.getElementById("template-title").textContent = setup.label;
        document.getElementById("template-description").textContent = setup.description;
        document.title = `${setup.label} | Doctor Letter`;

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

        const existingDraft = setup.draft;
        if (existingDraft && existingDraft.html_content) {
          quill.clipboard.dangerouslyPasteHTML(existingDraft.html_content);
          patientField().value = existingDraft.patient_name || "";
          draftId = existingDraft.id;
          setAutosaveStatus(`Resumed draft · ${Ui.formatDate(existingDraft.updated_at)}`);
        } else {
          quill.clipboard.dangerouslyPasteHTML(setup.html);
          setAutosaveStatus("Changes save automatically while you edit.");
        }

        quill.on("text-change", scheduleAutosave);
        patientField().addEventListener("input", () => {
          syncPatientNameIntoEditor(patientField().value.trim());
          scheduleAutosave();
        });
      } catch (error) {
        Ui.showAlert(alertBox, error.message);
        return;
      } finally {
        Ui.setPageBusy(false);
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
        button.textContent = "Saving…";

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
