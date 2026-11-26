/* Shared light/dark theme toggle for all RudyMap web pages. */
(function () {
  var root = document.documentElement;
  var themeBtn = document.getElementById("theme-toggle");
  if (!themeBtn) return;
  var saved = null;
  try { saved = localStorage.getItem("rudymap-theme"); } catch (e) {}
  if (saved === "dark" || saved === "light") {
    root.setAttribute("data-theme", saved);
  }
  function isDark() {
    var t = root.getAttribute("data-theme");
    if (t === "dark") return true;
    if (t === "light") return false;
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  }
  function syncThemeIcon() {
    themeBtn.textContent = isDark() ? "☀" : "☾";
    themeBtn.setAttribute("aria-label", isDark() ? "Switch to light theme" : "Switch to dark theme");
  }
  syncThemeIcon();
  themeBtn.addEventListener("click", function () {
    var next = isDark() ? "light" : "dark";
    root.setAttribute("data-theme", next);
    try { localStorage.setItem("rudymap-theme", next); } catch (e) {}
    syncThemeIcon();
  });
})();
