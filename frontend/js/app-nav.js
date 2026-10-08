const AppNav = (() => {
  const NAV_ITEMS = [
    { id: "dashboard", label: "Workspace", short: "Home", icon: "document" },
    { id: "templates", label: "Templates", short: "New", icon: "filePlus" },
    { id: "history", label: "Past letters", short: "History", icon: "clock" },
    { id: "profile", label: "Profile", short: "You", icon: "user" },
  ];

  function hrefFor(id) {
    if (typeof Paths === "undefined") {
      return id === "dashboard" ? "/dashboard" : `/${id}`;
    }
    switch (id) {
      case "dashboard":
        return Paths.dashboard;
      case "templates":
        return Paths.templates;
      case "history":
        return Paths.history;
      case "profile":
        return Paths.profile;
      default:
        return Paths.dashboard;
    }
  }

  function currentPageId() {
    const fromBody = document.body.dataset.navPage;
    if (fromBody) {
      return fromBody;
    }
    const path = window.location.pathname.replace(/\/$/, "") || "/";
    if (path === "/dashboard") {
      return "dashboard";
    }
    if (path === "/templates" || path === "/templates.html") {
      return "templates";
    }
    if (path === "/history") {
      return "history";
    }
    if (path === "/profile") {
      return "profile";
    }
    if (path.startsWith("/editor")) {
      return "editor";
    }
    return "";
  }

  function linkMarkup(item, pageId, compact) {
    const active = pageId === item.id;
    const href = hrefFor(item.id);
    const label = compact ? item.short : item.label;
    const current = active ? ' aria-current="page"' : "";
    const iconHtml = typeof Icons !== "undefined" ? Icons.svg(item.icon, "icon app-nav-icon") : "";
    return `<a href="${href}" class="app-nav-link${active ? " is-active" : ""}" data-nav-id="${item.id}"${current}>
      ${iconHtml}
      <span class="app-nav-text">${label}</span>
    </a>`;
  }

  function renderNavbar(pageId) {
    const desktopLinks = NAV_ITEMS.map((item) => linkMarkup(item, pageId, false)).join("");
    const mobileLinks = NAV_ITEMS.map((item) => linkMarkup(item, pageId, true)).join("");
    return `
      <div class="app-navbar-wrap">
        <div class="app-navbar-glass app-navbar-top">
          <a class="app-navbar-brand brand brand-with-logo" href="${hrefFor("dashboard")}">
            <img class="brand-logo" src="/images/logo-mark.jpg" alt="" width="36" height="36" decoding="async" />
            <span class="brand-text">Doctor <span class="brand-accent">Letter</span></span>
          </a>
          <nav class="app-navbar-desktop" aria-label="Main navigation">${desktopLinks}</nav>
          <button type="button" class="app-nav-signout btn btn-ghost" id="nav-sign-out">Sign out</button>
        </div>
      </div>
      <nav class="app-navbar-mobile" aria-label="Main navigation">
        <div class="app-navbar-mobile-inner">${mobileLinks}</div>
      </nav>
    `;
  }

  function updateActiveNav(pageId) {
    document.querySelectorAll(".app-nav-link[data-nav-id]").forEach((link) => {
      const active = link.dataset.navId === pageId;
      link.classList.toggle("is-active", active);
      if (active) {
        link.setAttribute("aria-current", "page");
      } else {
        link.removeAttribute("aria-current");
      }
    });
  }

  function injectIcons(slot) {
    if (typeof Icons === "undefined") {
      return;
    }
    slot.querySelectorAll(".app-nav-link[data-nav-id]").forEach((link) => {
      if (link.querySelector(".app-nav-icon")) {
        return;
      }
      const item = NAV_ITEMS.find((entry) => entry.id === link.dataset.navId);
      if (!item) {
        return;
      }
      link.insertAdjacentHTML("afterbegin", Icons.svg(item.icon, "icon app-nav-icon"));
    });
  }

  async function logoutAndRedirect() {
    if (typeof Api !== "undefined") {
      try {
        await Api.logout();
      } catch {
        /* still leave the app */
      }
    }
    window.location.href = typeof Paths !== "undefined" ? Paths.home : "/";
  }

  function wireSignOutButton(buttonId) {
    const btn = document.getElementById(buttonId);
    if (!btn || btn.dataset.wired === "true") {
      return;
    }
    btn.dataset.wired = "true";
    btn.addEventListener("click", async () => {
      btn.disabled = true;
      await logoutAndRedirect();
    });
  }

  function wireSignOut() {
    wireSignOutButton("nav-sign-out");
    wireSignOutButton("profile-sign-out");
  }

  function mount() {
    const slot = document.getElementById("app-navbar");
    if (!slot) {
      return;
    }

    const pageId = currentPageId();
    const hasShell = Boolean(slot.querySelector(".app-navbar-glass"));

    if (!hasShell) {
      slot.className = "app-navbar";
      slot.innerHTML = renderNavbar(pageId);
    } else {
      slot.classList.add("app-navbar");
      injectIcons(slot);
      updateActiveNav(pageId);
    }

    slot.dataset.mounted = "true";
    wireSignOut();

    slot.classList.add("app-navbar-enter");
    syncMobileNavClass();
    window.addEventListener("resize", syncMobileNavClass, { passive: true });
    window.addEventListener("orientationchange", syncMobileNavClass, { passive: true });
    setupScrollEffect(slot);
    applyMotionStagger();
  }

  function setupScrollEffect(slot) {
    const desktop = window.matchMedia("(min-width: 768px)");
    let ticking = false;

    function update() {
      if (!desktop.matches) {
        slot.classList.remove("is-scrolled");
        return;
      }
      slot.classList.toggle("is-scrolled", window.scrollY > 12);
      ticking = false;
    }

    function onScroll() {
      if (!ticking) {
        ticking = true;
        requestAnimationFrame(update);
      }
    }

    window.addEventListener("scroll", onScroll, { passive: true });
    desktop.addEventListener("change", update);
    update();
  }

  function syncMobileNavClass() {
    document.body.classList.toggle("has-mobile-nav", window.matchMedia("(max-width: 767px)").matches);
  }

  function setUserLabel(_profile) {
    /* reserved */
  }

  function applyMotionStagger() {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      return;
    }
    document.querySelectorAll(".motion-stagger").forEach((container) => {
      const children = container.children;
      for (let i = 0; i < children.length; i += 1) {
        children[i].style.setProperty("--motion-i", String(i));
        children[i].classList.add("motion-rise");
      }
    });
  }

  function init() {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", mount);
    } else {
      mount();
    }
    window.addEventListener("load", mount);
  }

  init();

  return { mount, setUserLabel, applyMotionStagger, wireSignOutButton };
})();
