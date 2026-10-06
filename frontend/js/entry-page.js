document.addEventListener("DOMContentLoaded", () => {
  (async function init() {
    const cached = ProfileCache.read();
    if (cached) {
      window.location.href = "dashboard.html";
      return;
    }
    try {
      const profile = await Api.me();
      ProfileCache.write(profile);
      window.location.href = "dashboard.html";
      return;
    } catch {
      /* not signed in */
    }

    const form = document.getElementById("entry-form");
    const alertBox = document.getElementById("alert");
    const mobileInput = document.getElementById("mobile");
    const submitBtn = document.getElementById("entry-submit");
    const companyField = document.getElementById("company");

    function digitsOnly(value) {
      return value.replace(/\D/g, "");
    }

    function isValidMobile(digits) {
      if (/^[6-9]\d{9}$/.test(digits)) {
        return true;
      }
      return digits.length >= 10 && digits.length <= 15;
    }

    mobileInput.addEventListener("input", () => {
      const cleaned = digitsOnly(mobileInput.value);
      if (cleaned !== mobileInput.value) {
        mobileInput.value = cleaned;
      }
    });

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      Ui.clearAlert(alertBox);

      if (companyField && companyField.value.trim()) {
        Ui.showAlert(alertBox, "Unable to sign in. Check your number and try again.");
        return;
      }

      const mobile = digitsOnly(mobileInput.value.trim());
      if (!isValidMobile(mobile)) {
        Ui.showAlert(alertBox, "Enter a valid 10-digit mobile number.");
        return;
      }

      submitBtn.disabled = true;
      submitBtn.setAttribute("aria-busy", "true");
      try {
        await Api.startSession(mobile, companyField ? companyField.value : "");
        window.location.href = "dashboard.html";
      } catch (error) {
        Ui.showAlert(alertBox, error.message);
        submitBtn.disabled = false;
        submitBtn.removeAttribute("aria-busy");
      }
    });
  })();
});
