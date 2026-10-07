const Paths = (() => {
  function editor(templateSlug) {
    const params = new URLSearchParams({ template: templateSlug });
    return `/editor?${params.toString()}`;
  }

  return {
    home: "/",
    dashboard: "/dashboard",
    workspace: "/dashboard",
    templates: "/templates",
    editor,
    history: "/history",
    letters: "/history",
    profile: "/profile",
    privacy: "/privacy",
  };
})();
