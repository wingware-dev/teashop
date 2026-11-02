// Stripe's Payment Element on the pay pages (checkout and subscriptions).
// The form carries the publishable key, the payment's client secret and
// where Stripe should send the customer afterwards (data- attributes, so
// the page needs no inline script under the Content-Security-Policy).
(function () {
  "use strict";
  var form = document.getElementById("payment-form");
  if (!form || typeof Stripe === "undefined") {
    if (form) {
      showMessage("The payment form could not load.  Please check your connection and reload the page.");
    }
    return;
  }
  var button = document.getElementById("pay-button");
  var stripe = Stripe(form.dataset.stripeKey);
  var dark = window.matchMedia("(prefers-color-scheme: dark)").matches &&
    document.documentElement.dataset.theme !== "light" || document.documentElement.dataset.theme === "dark";
  var elements = stripe.elements({
    clientSecret: form.dataset.clientSecret,
    appearance: { theme: dark ? "night" : "stripe" }
  });
  var payment = elements.create("payment", { layout: "tabs" });
  var mount = document.getElementById("payment-element");
  mount.textContent = "";
  payment.mount(mount);
  payment.on("ready", function () { button.disabled = false; });

  function showMessage(text) {
    var box = document.getElementById("payment-message");
    box.textContent = text;
    box.hidden = !text;
  }

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    button.disabled = true;
    showMessage("");
    // data-intent="setup": saving a card for later (a SetupIntent, on the
    // subscription card page), not paying now.
    var setup = form.dataset.intent === "setup";
    var confirm = setup ? stripe.confirmSetup : stripe.confirmPayment;
    confirm.call(stripe, {
      elements: elements,
      confirmParams: { return_url: form.dataset.returnUrl }
    }).then(function (result) {
      // Only reached when the card is refused or needs the customer again;
      // on success Stripe goes to return_url.
      if (result.error) {
        showMessage(result.error.message || (setup ? "The card could not be saved." :
          "The payment did not go through.") + "  Please try again.");
      }
      button.disabled = false;
    });
  });
})();
