/* The packing app's service worker.  It makes the app installable and
   shows an offline page when there is no connection.  Owner pages are
   never cached (they hold customer data and change stock): only the
   offline page and the static files it needs. */
"use strict";

var CACHE = "packing-v1";
var OFFLINE = "{% url 'fulfillment:offline' %}";

self.addEventListener("install", function (event) {
  event.waitUntil(caches.open(CACHE).then(function (cache) {
    return cache.addAll([OFFLINE]);
  }).then(function () { return self.skipWaiting(); }));
});

self.addEventListener("activate", function (event) {
  event.waitUntil(caches.keys().then(function (keys) {
    return Promise.all(keys.filter(function (key) { return key !== CACHE; }).map(function (key) {
      return caches.delete(key);
    }));
  }).then(function () { return self.clients.claim(); }));
});

self.addEventListener("fetch", function (event) {
  if (event.request.mode !== "navigate") {
    return;
  }
  event.respondWith(fetch(event.request).catch(function () {
    return caches.match(OFFLINE);
  }));
});
