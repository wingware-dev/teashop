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

Items at or below their reorder level, lots within 60 days of their
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
