# Packing and shipping orders

Phase 5 (`apps/fulfillment`): the order queue, the packing list, weighing
and packing with the legal records, package labels, box suggestions, USPS
labels through EasyPost, tracking emails, cancellations, refunds, reships,
address changes, back-orders, Mail Order Rule delay notices, USPS pickups,
and the 6pm new-order summary.  It all lives at **/owner/fulfillment/**
(Dashboard → Shortcuts → "Orders to pack and ship").

## Set up once (in the admin, under Fulfillment)

1. **Scales:** your legal-for-trade (NTEP) scale: serial number, NTEP
   certificate, county registration, the date weights and measures sealed
   it, and when the next inspection is due.  Untick "seal intact" if the
   seal is ever broken: packing on it is refused until it is resealed.
2. **Box sizes:** each box or mailer you ship in, linked to its stock
   item (Inventory → Items, kind "Shipping box"), with its *inside* size in
   inches, empty weight, and the filler used with it (a packaging item and
   how many pieces).  Using a box takes it and its filler out of stock.
3. **Package dimensions (optional):** the outside size of a packed size
   (a 100 g tin, say).  Sizes without one use a usual size for a tin,
   pouch or box (`PACKAGE_DIMENSIONS_IN` in `config/settings.py`).
4. In `.env`: `LABEL_PACKER_ADDRESS` (printed on every package label; no
   label prints without it), the `SHIP_FROM_*` address, `EASYPOST_API_KEY`
   and `OWNER_NOTIFY_EMAIL`.

## Packing an order (on the phone, at the bench)

The phone's browser can install the pages as an app: open
/owner/fulfillment/ and choose "Add to Home Screen" (Safari) or
"Install app" (Chrome).

1. **Orders** lists what is paid and waiting, soonest promised first; late
   ones in red, due today or tomorrow in yellow.  Orders with an allergen
   tea come after the others due the same day.
2. **Packing list** sums every package still to pack by tea and size, with
   the lot to weigh from, and puts allergen teas in a separate "pack last"
   table.
3. On the **order's page**, for each package: tare the scale with the empty
   pouch or tin, weigh the tea, enter what the scale shows and choose the
   scale; **Pack and print label**.  This takes the tea (from one lot, the
   oldest best-by first, or one you choose) and the packaging out of stock
   and records the measured net weight and the scale with its seal date
   (Fulfillment → Packing records).  Less than the labelled weight is
   refused.  Then **Print label** opens the package label (PDF, sized by
   `PACKAGE_LABEL_SIZE`, 4x2 inches by default) to print on the thermal
   printer.
4. A tea whose lot carries allergens shows a red warning: pack it last,
   with its own scoop, clean the bench and scale afterwards, and tick
   "Allergen handling done"; it won't pack until you do.
5. Packed the wrong thing?  **Unpack** puts its tea and packaging back on
   their lots ("returned" stock movements).

## Box, label, tracking

Below the packages, the **suggested box** is the smallest one in stock that
holds them with room for filler and takes the biggest package.  Choose
another, or "Another box" with what it is (and its size if you know it).
Weigh the sealed parcel (grams, ounces or pounds), check the service (the
one the customer paid for), and **Buy label and ship**:

- EasyPost buys the postage and sends a 4x6 label: **Print shipping
  label**.  With a test key (`EZTK...`) labels are test labels, marked
  "Test label: do not mail"; a live key is refused unless
  `EASYPOST_ALLOW_LIVE=true`.  Without EasyPost (a laptop), a stand-in
  label is made locally.
- The box and its filler come out of stock.
- The order is marked shipped and the customer gets the tracking number
  by email at once.
- **Void label** asks for the postage back, puts the box back in stock,
  and reopens the parcel.

Not everything in stock?  Tick "Ship what is packed now; back-order the
rest": the rest becomes a back-ordered parcel, and the customer is told
what follows.  Or **Back-order this parcel** with the date you expect the
stock; "Stock is in: pack it now" resumes it.

## USPS pickups

**Pickups** lists the labelled parcels and books a free carrier pickup
for a day (Monday to Saturday), with where the parcels will be.  Later
parcels can be added to a booked pickup.

## Cancelling, refunds, reships, address changes

- **Cancel the order** (before it ships): everything paid is refunded,
  anything packed goes back to stock (or is written off as damaged if you
  untick "can go back on the shelf"), and the customer is emailed.
- **Refund part or all** (any time): the amount goes back to the card
  through Stripe; the customer is emailed with your reason.  Refunds can't
  exceed what was paid.  AI agents can't refund or cancel.
- **Lost or damaged?  Send it again** starts a reship: a new parcel of the
  items you choose, packed and labelled as usual, at no charge; the
  customer gets the new tracking number.
- **Change the address** (before the label is bought): the new address is
  checked with the post office first.

## The Mail Order Rule

You must ship by the date promised (the order's "ship by"), or, before it
passes, tell the customer the new date and offer to cancel for a full
refund.  On the order's page, **Send a delay notice** with the new date and
the reason:

- A first delay of up to 30 days: saying nothing means the customer agrees,
  so the promised date moves to the new one.
- A longer delay, or a second notice: the customer must agree.  The email
  says you will cancel and refund if they haven't by a date (the old ship
  date, or three working days from now if later).  The dashboard flags the
  order when that passes: cancel and refund it.
- The email's link lets the customer choose "I'll wait" or "Cancel my
  order and refund me" (instantly refunded).

This is a careful reading of 16 CFR 435, not legal advice; check it with
your lawyer.

## Notifications

By email only.  New orders are not emailed one by one: the
`send_order_summary` job (systemd timer `teashop-order-summary`, 6pm New
York time, installed by `install-app.sh`) sends one summary of the day's
new orders, orders late or due tomorrow, and delay notices waiting for an
answer.  Set `OWNER_NEW_ORDER_EMAILS=each` for an email per order instead.

## Labels and the law (verify)

The package label carries the name, net weight in ounces and grams (ounces
rounded down), "Grown in", ingredients, "Contains:" allergens, lot code,
best-by date and the packer's name and address.  The net weight is printed
at the bottom in type sized for the label's area under 21 CFR 101.105(i),
taking the label as the principal display panel; if the label sits on the
back of the package, check the front's requirements with Ag & Markets.

## For other phases

- `apps.fulfillment.services` does everything the pages do; use it rather
  than moving stock or calling EasyPost directly.  `refund()` and
  `cancel_order()` refuse AI agents.
- `apps.catalog.services.reverse_package(sold_package, note, reusable=True)`
  undoes `pack()`; reversed packages (`SoldPackage.reversed_at`) no
  longer count in organic sales or the profit report.
- `apps.checkout.payments.provider().refund(order, amount, key)` refunds
  through Stripe (or the stand-in).
- Refunds are not yet taken off the sales-tax and nexus figures, which
  still count each order's full total.
