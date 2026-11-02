/* Small enhancements; every page works without them.
   - The theme button: Automatic (the device's setting) -> Dark -> Light.
   - Menus (<details class="menu">) close on Escape and on a click elsewhere.
   - The filter panel starts open on wide screens. */
(function () {
  "use strict";

  var THEMES = ["auto", "dark", "light"];
  var NAMES = { auto: "Automatic", dark: "Dark", light: "Light" };
  var root = document.documentElement;

  function savedTheme() {
    try {
      var theme = localStorage.getItem("theme");
      return theme === "light" || theme === "dark" ? theme : "auto";
    } catch (e) {
      return "auto";
    }
  }

  function applyTheme(theme) {
    if (theme === "auto") {
      root.removeAttribute("data-theme");
    } else {
      root.setAttribute("data-theme", theme);
    }
    try {
      if (theme === "auto") {
        localStorage.removeItem("theme");
      } else {
        localStorage.setItem("theme", theme);
      }
    } catch (e) {
      /* Not saved; it still applies to this page. */
    }
  }

  function setUpThemeButton(button) {
    var label = button.querySelector("[data-theme-name]");
    function show(theme) {
      label.textContent = NAMES[theme];
      button.setAttribute("data-current", theme);
    }
    show(savedTheme());
    button.hidden = false;
    button.addEventListener("click", function () {
      var next = THEMES[(THEMES.indexOf(savedTheme()) + 1) % THEMES.length];
      applyTheme(next);
      show(next);
    });
  }

  function setUpMenus() {
    var menus = Array.prototype.slice.call(document.querySelectorAll("details.menu"));
    document.addEventListener("click", function (event) {
      menus.forEach(function (menu) {
        if (menu.open && !menu.contains(event.target)) {
          menu.open = false;
        }
      });
    });
    document.addEventListener("keydown", function (event) {
      if (event.key !== "Escape") {
        return;
      }
      menus.forEach(function (menu) {
        if (menu.open) {
          menu.open = false;
          menu.querySelector("summary").focus();
        }
      });
    });
  }

  function openFiltersWhenWide() {
    var filters = document.querySelector("details.filters");
    if (filters && window.matchMedia("(min-width: 60rem)").matches) {
      filters.open = true;
    }
  }

  document.querySelectorAll("[data-theme-toggle]").forEach(setUpThemeButton);
  setUpMenus();
  openFiltersWhenWide();
})();
