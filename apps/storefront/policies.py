"""The shop's policy pages: privacy, terms of sale, returns, shipping,
subscriptions and accessibility.

The wording is a careful starting draft, not legal advice: have it read by
a lawyer before the shop opens, and keep it true as the shop changes.
Change UPDATED whenever a policy's substance changes.

PROCESSORS is the privacy policy's list of every service that receives
customer data (California's online privacy law requires naming them).
Keep it complete: add a service here the day it starts receiving data.
"""

from datetime import date

UPDATED = date(2026, 11, 1)

POLICIES = {
    "privacy": "Privacy policy",
    "terms": "Terms of sale",
    "returns": "Returns and refunds",
    "shipping": "Shipping",
    "subscriptions": "Subscription terms",
    "accessibility": "Accessibility",
}

# (service, what it receives, why)
PROCESSORS = [
    ("Stripe (payments and fraud screening)",
     "Your name, email, shipping address, the amount, and your card or wallet details, which you give to Stripe "
     "directly; we never see or keep card numbers.  Stripe also sees your device and IP address to screen for "
     "fraud.",
     "To take payment, prevent fraud and, if used, work out sales tax."),
    ("EasyPost (shipping rates, address checking, labels and tracking)",
     "Your name, shipping address, phone if you give one, and the parcel's weight.",
     "To check the address, price the postage, buy the label and follow the parcel."),
    ("United States Postal Service",
     "The name, address and phone on the label.",
     "To deliver your parcel."),
    ("Our email service (sending our emails)",
     "Your email address and the email's content.",
     "To send order, shipping, sign-in and subscription emails."),
    ("Anthropic (the AI model behind our assistant)",
     "What you write to us by chat or email, and order details needed to answer it.",
     "To help answer questions.  Answers written by AI say so, and a person at the shop is always "
     "available."),
    ("Our hosting provider (the server the shop runs on)",
     "Everything the shop keeps, stored on a server we rent.",
     "To run the shop."),
    ("Cloudflare (network protection and bot checks)",
     "Your IP address and the pages you request.",
     "To keep the site fast and turn away attacks and bots."),
    ("Backblaze (encrypted backups)",
     "An encrypted copy of the shop's records, which Backblaze cannot read.",
     "To recover from a failure."),
    ("Plausible or Umami (visit counts, when turned on)",
     "The pages of the shop's catalog you visit, the site that sent you there and your browser and country, "
     "without cookies.  Your IP address is used only to count unique visits for a day and is not kept.",
     "To see which pages and posts bring visitors."),
    ("Sentry (error reports, when turned on)",
     "Technical details of an error on the site; we set it not to collect personal details.",
     "To find and fix faults."),
]
