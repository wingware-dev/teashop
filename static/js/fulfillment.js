/* The packing pages: register the service worker that makes them an
   installable app (home screen), and bring the "print the label" box into
   view after packing.  Everything works without it. */
(function () {
  "use strict";

  var script = document.currentScript || document.querySelector("script[data-sw]");
  if (script && "serviceWorker" in navigator) {
    navigator.serviceWorker.register(script.getAttribute("data-sw"), { scope: script.getAttribute("data-scope") })
      .catch(function () { /* Not installable here (http, private mode); the pages still work. */ });
  }

  var printBox = document.getElementById("print");
  if (printBox) {
    printBox.focus();
  }
})();
