/* Loaded in <head>, before the page draws, so a visitor who chose light or
   dark (site.js) never sees a flash of the other theme.  With no choice
   saved, the CSS follows the device's setting. */
(function () {
  try {
    var theme = localStorage.getItem("theme");
    if (theme === "light" || theme === "dark") {
      document.documentElement.setAttribute("data-theme", theme);
    }
  } catch (e) {
    /* Storage blocked (private mode, settings): follow the device. */
  }
})();
