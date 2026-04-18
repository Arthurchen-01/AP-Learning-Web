(function initSiteBase() {
  const REPO_NAMES = ['AP-Learning-Web-01', 'AP-Learning-Web-02', 'AP-Learning-Web-03', 'AP-Learning-Web-04'];
  const isGitHubPages = window.location.hostname.endsWith('.github.io');

  let base = '';
  if (isGitHubPages) {
    const pathParts = window.location.pathname.split('/').filter(Boolean);
    base = '/' + (REPO_NAMES.includes(pathParts[0]) ? pathParts[0] : 'AP-Learning-Web');
  }

  window.MOKAO_SITE_BASE = base;
  window.sitePath = function sitePath(pathname) {
    if (!pathname) return base || '/';
    if (/^(?:[a-z]+:)?\/\//i.test(pathname)) return pathname;
    const normalized = pathname.startsWith('/') ? pathname : '/' + pathname;
    return base + normalized;
  };
})();
