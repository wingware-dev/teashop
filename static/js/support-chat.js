// The support chat: while the customer waits for the assistant, ask the
// server for new messages every few seconds and add them to the list.
// Without this script the page works too: the customer reloads it.
(function () {
  "use strict";
  var log = document.getElementById("chat-log");
  if (!log) return;
  var status = document.querySelector("[data-chat-status]");
  var url = log.getAttribute("data-poll-url");
  var lastId = parseInt(log.getAttribute("data-last-id") || "0", 10);
  var shopName = log.getAttribute("data-shop-name");
  var aiLabel = log.getAttribute("data-ai-label");
  var tries = 0;
  var MAX_TRIES = 60; // three minutes

  function linkify(parent, text) {
    var pattern = /https?:\/\/[^\s<>"')\]]+/g;
    var at = 0;
    var match;
    while ((match = pattern.exec(text)) !== null) {
      parent.appendChild(document.createTextNode(text.slice(at, match.index)));
      var link = document.createElement("a");
      link.href = match[0];
      link.textContent = match[0];
      parent.appendChild(link);
      at = match.index + match[0].length;
    }
    parent.appendChild(document.createTextNode(text.slice(at)));
  }

  function addBody(body, text, links) {
    text.split("\n").forEach(function (line, index) {
      if (index) body.appendChild(document.createElement("br"));
      if (links) linkify(body, line); else body.appendChild(document.createTextNode(line));
    });
  }

  function add(message) {
    if (document.getElementById("msg-" + message.id)) return;
    var item = document.createElement("li");
    item.className = "chat-msg from-" + message.sender;
    item.id = "msg-" + message.id;
    var who = document.createElement("p");
    who.className = "chat-who";
    var name = document.createElement("strong");
    name.textContent = message.sender === "customer" ? "You" : shopName;
    who.appendChild(name);
    if (message.ai) {
      who.appendChild(document.createTextNode(" "));
      var badge = document.createElement("span");
      badge.className = "ai-badge";
      badge.textContent = aiLabel;
      who.appendChild(badge);
    }
    var body = document.createElement("div");
    body.className = "chat-body";
    addBody(body, message.body, message.sender !== "customer");
    item.appendChild(who);
    item.appendChild(body);
    log.appendChild(item);
  }

  function poll() {
    tries += 1;
    fetch(url + "?after=" + lastId, { headers: { Accept: "application/json" }, credentials: "same-origin" })
      .then(function (response) { return response.ok ? response.json() : Promise.reject(response.status); })
      .then(function (data) {
        data.messages.forEach(function (message) {
          add(message);
          lastId = Math.max(lastId, message.id);
        });
        if (data.waiting && tries < MAX_TRIES) {
          window.setTimeout(poll, 3000);
        } else if (status) {
          status.hidden = !data.waiting;
        }
      })
      .catch(function () {
        if (tries < MAX_TRIES) window.setTimeout(poll, 6000);
      });
  }

  if (log.getAttribute("data-waiting") === "1") window.setTimeout(poll, 1500);
})();
