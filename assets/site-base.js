(function initSiteBase() {
  const REPO_BASE = "/AP-Learning-Web";
  const isGitHubPages =
    window.location.hostname === "arthurchen-01.github.io" ||
    window.location.hostname.endsWith(".github.io");
  const base = isGitHubPages ? REPO_BASE : "";

  window.MOKAO_SITE_BASE = base;
  window.sitePath = function sitePath(pathname) {
    if (!pathname) {
      return base || "/";
    }
    if (/^(?:[a-z]+:)?\/\//i.test(pathname)) {
      return pathname;
    }

    const normalized = pathname.startsWith("/") ? pathname : `/${pathname}`;
    return `${base}${normalized}`;
  };
})();
