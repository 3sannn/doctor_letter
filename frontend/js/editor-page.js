(function () {
  document.addEventListener("DOMContentLoaded", () => {
    const params = new URLSearchParams(window.location.search);
    const slug = params.get("template");

    let quill;
    let templateSlug = slug;
    let draftId = null;
    let autosaveTimer = null;
    let sheetTimer = null;
    let activeTab = "edit";

    function patientField() {
      return document.getElementById("patient-name");
    }

    function sheetContentNode() {
      return document.getElementById("letter-sheet-content");
    }

    function syncSheetPreview() {
      const sheet = sheetContentNode();
      if (!sheet || !quill) {
        return;
      }
      const html = quill.root.innerHTML;
      const hasText = Boolean(quill.getText().trim());
      if (!hasText) {
        sheet.innerHTML =
          '<p class="letter-preview-placeholder">Your letter text will appear here as you edit.</p>';
        return;
      }
      sheet.innerHTML = html;
    }

    function scheduleSheetPreview() {
      clearTimeout(sheetTimer);
      sheetTimer = setTimeout(syncSheetPreview, 80);
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
      scheduleSheetPreview();
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
        setAutosaveStatus("Draft not saved. Your text is still on this page—check your connection.");
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
      document.getElementById("close-preview")?.focus();
    }

    function closePreviewModal() {
      const overlay = document.getElementById("preview-modal");
      const frame = document.getElementById("preview-frame");
      overlay.hidden = true;
      frame.src = "";
      document.body.classList.remove("modal-open");
    }

    function setupEditorTabs() {
      const tabEdit = document.getElementById("tab-edit");
      const tabSheet = document.getElementById("tab-sheet");
      const panelEdit = document.getElementById("panel-edit");
      const panelSheet = document.getElementById("panel-sheet");
      const tabsBar = document.querySelector(".editor-tabs");

      function activate(which) {
        activeTab = which;
        const isEdit = which === "edit";
        tabEdit.classList.toggle("is-active", isEdit);
        tabSheet.classList.toggle("is-active", !isEdit);
        tabEdit.setAttribute("aria-selected", isEdit ? "true" : "false");
        tabSheet.setAttribute("aria-selected", !isEdit ? "true" : "false");
        panelEdit.hidden = !isEdit;
        panelSheet.hidden = isEdit;
        if (!isEdit) {
          syncSheetPreview();
        }
      }

      tabEdit.addEventListener("click", () => activate("edit"));
      tabSheet.addEventListener("click", () => activate("sheet"));

      const mq = window.matchMedia("(min-width: 900px)");

      function applyLayout() {
        if (mq.matches) {
          panelEdit.hidden = false;
          panelSheet.hidden = false;
          if (tabsBar) {
            tabsBar.setAttribute("hidden", "");
          }
          syncSheetPreview();
        } else {
          if (tabsBar) {
            tabsBar.removeAttribute("hidden");
          }
          activate(activeTab);
        }
      }

      mq.addEventListener("change", applyLayout);
      applyLayout();
    }

    async function init() {
      await Session.requireAuth();
      const alertBox = document.getElementById("alert");

      if (!templateSlug) {
        window.location.href = Paths.templates;
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

        setupEditorTabs();
        requestAnimationFrame(() => {
          syncSheetPreview();
          requestAnimationFrame(syncSheetPreview);
        });

        quill.on("text-change", () => {
          scheduleAutosave();
          scheduleSheetPreview();
        });
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

      const previewBtn = document.getElementById("preview-letter");
      previewBtn.addEventListener("click", async () => {
        Ui.clearAlert(alertBox);
        Ui.setButtonLoading(previewBtn, true, "Generating…");
        try {
          const result = await Api.previewLetter({
            template_slug: templateSlug,
            html_content: quill.root.innerHTML,
          });
          openPreviewModal(result.pdf_base64);
        } catch {
          Ui.showAlert(
            alertBox,
            "We could not build the preview. Your draft is still saved—try again or simplify formatting."
          );
        } finally {
          Ui.setButtonLoading(previewBtn, false);
        }
      });

      document.getElementById("close-preview").addEventListener("click", closePreviewModal);
      document.getElementById("preview-modal").addEventListener("click", (event) => {
        if (event.target.id === "preview-modal") {
          closePreviewModal();
        }
      });
      document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && !document.getElementById("preview-modal").hidden) {
          closePreviewModal();
        }
      });

      const saveBtn = document.getElementById("save-letter");
      saveBtn.addEventListener("click", async () => {
        Ui.clearAlert(alertBox);
        const hint = document.getElementById("finalize-hint");
        if (hint) {
          hint.hidden = false;
        }
        Ui.setButtonLoading(saveBtn, true, "Saving PDF…");
        try {
          await Api.finalizeLetter({
            template_slug: templateSlug,
            html_content: quill.root.innerHTML,
            patient_name: patientField().value.trim(),
            draft_id: draftId,
          });
          setAutosaveStatus("Letter saved. Opening your history…");
          window.location.href = Paths.history;
        } catch {
          Ui.showAlert(
            alertBox,
            "We could not finalize the letter. Your draft is still here—check storage settings or try again."
          );
          Ui.setButtonLoading(saveBtn, false);
        }
      });
    }

    init();
  });
})();
