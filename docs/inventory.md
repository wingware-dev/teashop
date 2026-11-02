# Inventory and catalog: how to use them

Everything is in the back office (admin), under **Inventory** and
**Catalog**.  Quantities are grams for bulk items (teas, herbs,
flavourings) and pieces for everything else.

## Setting up

1. **Suppliers**: one per importer or wholesaler, with the usual lead time.
2. **Items**: every thing you keep in stock.  Bulk teas and herbs, each
   flavouring or blend ingredient, each pouch and tin size, labels,
   shipping boxes, merchandise.  Give each a short **code** (it starts
   every lot code, e.g. `ASSAM` makes lots `ASSAM-261101`), the
   **ingredient name** as it should read on a label ("black tea",
   "natural vanilla flavour"), and a **reorder level** to be warned at.
3. **Recipes** for blends, flavoured and herbal teas: the blend is an item
   too (kind tea or herbal), and the recipe says how many grams of each
   ingredient go into 1 kg; they must add up to 1000.
4. **Products** and their **size options**: a tea product names its bulk
   tea; each size option has its net grams, price and SKU, and on its
   own page the **bill of materials** besides the tea (one tin, one
   label...).  Give expensive teas smaller sizes.  The size page shows
   what one package uses, the net weight as the label prints it, and how
   many packages current stock can fill.  Tick **sold as organic** only
   for products you describe as organic: they are packed from organic
   lots only and count towards the yearly limit.

## Reordering and purchase orders

The dashboard's **Reorder** page (also under Shortcuts) lists every item
with its usable stock, daily use, days left and reorder level.

- **Reorder level** = daily use × (supplier lead time + safety days).
  Daily use counts what was packed for orders, used in blends and given
  away as samples over the last 90 days (losses don't count).  A new
  item is measured since its first delivery.  The item's own reorder
  level is the lowest level used; untick **automatic reorder level** on
  the item to use only that.
- **Suggested quantity** = enough for lead time + safety days + cover days
  (60 by default), less usable stock and what is still to come on
  approved orders, rounded up to the item's **minimum order**.  Set the
  lead time on the supplier, and safety or cover days per item if the
  defaults (`REORDER_SAFETY_DAYS`, `REORDER_COVER_DAYS`) don't suit it.
- **Draft purchase orders** makes one draft per supplier (the item's
  default supplier) with the suggested quantities and the last price
  paid.  Items with no supplier are listed for you to order by hand;
  blends made here show as "make a blend batch" instead.
- **Nothing is ordered until you approve.**  Open the draft, change
  quantities or prices, then **Save, approve and mark ordered** (or the
  list action).  That records you as approver and sets the expected
  date from the supplier's lead time.  Then send the order to the
  supplier yourself.  AI agents can draft but never approve, and a
  delivery can't be received against an unapproved draft.
- On an approved order, **Record a delivery for this order** opens a
  receipt already filled in with the supplier and order.  Late
  deliveries show on the dashboard.

## Receiving a delivery

**Receipts → Add**: choose the supplier and, if there is one, the
purchase order, then one lot per line of the delivery, with the supplier's
lot code, harvest year, best-by date, country of origin ("Grown in"),
organic status, allergens and the landed cost per kg (including shipping
and tariffs; put the tariff part in its own field).  A partial delivery is
just a receipt for what came; the purchase order shows what is still to
come and its status becomes "Partly received", then "Received".

Upload the spec sheet, allergen statement, origin and organic
certificates and lab results on the **lot's page**.  They are private:
only you, signed in, can open them.

## Changing stock by hand

**Stock adjustments → Add**: the lot, the change (negative removes) and a
reason.  Free samples and giveaways have their own reasons, so they count
as marketing, not loss.  A lot's received quantity never changes; every
change is a movement you can see on the lot's page.

## Stock counts

**Stock counts → Add**: tick what to count (or nothing, for everything).
It lists every lot with stock and what the records expect.  Weigh bulk
tea in grams and count pieces, enter what is there (save as you go), and
for anything short choose why: spoiled, damaged, sample, giveaway,
personal use, or unknown loss.  **Save and apply count** records each
difference as a stock adjustment.  Orders packed while you count don't
upset it: only the difference you found at the shelf is applied.

## Losses and profit

- **Losses and samples** (Shortcuts): the last 12 months at landed cost,
  per reason, with samples and giveaways as marketing and personal use
  apart from loss, and the items lost most.
- **Profit per tea and per size**: for any dates, sales, landed cost
  (with the tariff part shown) and margin per tea and per size.  Tea is
  valued at the cost of the very lot it was packed from; packaging at
  its average landed cost.  Shipping, payment fees and taxes are not in
  it.  Packages from lots with no landed cost are flagged.

## Making a blend

**Blend batches → Add**: the recipe, how many grams you made, and the
ingredient lots and grams you actually used, or leave those empty to use
the oldest best-by lots in the recipe's proportions.  Saving takes the
ingredients out of stock and makes a new blend lot that carries their
countries, allergens and statements, the ingredient list in order of
weight, the earliest best-by date and the weighted landed cost.

## Recalls

On a lot's page, **Trace this lot** lists the lots it was made from, the
blend lots made with it, and every customer order packed from any of
them.  The lots list's **Recall** action marks the lot and its blend lots
recalled, so nothing more is packed from them, and lists the orders to
contact.  **Put on hold** stops packing from a lot while you check it.

## Alerts on the dashboard

Items at or below their reorder level, items to reorder with no purchase
order yet, drafts waiting for your approval, late deliveries, stock
counts left unapplied for a week, lots within 60 days of their
best-by date (`INVENTORY_BEST_BY_WARNING_DAYS`), lots on hold, sizes that
can't be packed from stock, and organic sales from $4,000 a year
(`ORGANIC_SALES_ALERT`) towards the $5,000 limit for selling organic
without certification (`ORGANIC_EXEMPTION_LIMIT`).

## Labels

Each packed package's page shows its label facts: name, net weight in oz
and g (ounces rounded down), "Grown in ...", ingredients, "Contains: ..."
allergens, lot code, best-by date and the packer's address, which comes
from `LABEL_PACKER_ADDRESS` in `.env`.  Missing facts are listed as
problems.  Printing labels comes with the fulfillment dashboard.
