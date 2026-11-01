# Information security policy

_[Business name], [address].  Adopted [date].  Reviewed every quarter and
after any security incident.  Owner and Security Coordinator: [owner's name]._

This policy describes how the business protects the private information of
its customers, as New York's SHIELD Act (General Business Law § 899-bb)
requires.  As a small business (under 50 employees, under $3 million
revenue), the business uses safeguards suited to its size, the nature of
its work and the sensitivity of the data it holds.

**What we hold.** Customer names, email and shipping addresses, phone
numbers, order history, and (for customers who make an account) a
password stored only as a salted one-way hash.  **We never receive or
store payment card numbers**: card details go from the customer's browser
straight to Stripe through Stripe-hosted fields (PCI DSS SAQ A).  We do
not collect Social Security, driver's license or bank account numbers.
We keep only the data needed to sell, ship, support and account for
orders, and delete what we no longer need (see Physical safeguards).

## Administrative safeguards

1. **Coordinator.** The owner is responsible for this program.
2. **Risk assessment.** Each quarter the owner, helped by the security
   review agent, reviews the risks in `docs/ops/` and this policy:
   dependency vulnerability reports, server updates, access lists, backups
   and restore tests, and the audit log.  An outside vulnerability scan
   runs at least yearly and before launch.
3. **People.** Anyone given access (staff later, contractors) gets their
   own account with only the access they need, is trained on this policy,
   and loses access the day they leave.
4. **Service providers.** We use providers who state reasonable security
   in their terms and process data only for us: VPS host, Stripe,
   shipping-label service, email delivery, Backblaze (encrypted backups),
   Sentry (no personal data sent), Cloudflare.  AI agents get only the
   data and permissions their task needs; their actions are logged and
   they cannot spend money or issue refunds without the owner's approval.
5. **Changes.** Every code change is reviewed (with AI-assisted security
   review) and tested before deployment; deployments are automated and
   recorded.

## Technical safeguards

1. **Network and software design:** one hardened server with only HTTPS
   and SSH reachable; Cloudflare in front; database not reachable from
   the internet; HTTPS everywhere with HSTS.
2. **Access:** owner sign-in needs a password and a two-factor code;
   server access is by SSH key only, no root or password logins; repeated
   failed sign-ins are blocked automatically.
3. **Detect and respond:** an append-only audit log of all data changes,
   sign-ins and agent actions; uptime monitoring, error tracking and
   alerts for failed backups; logs kept and rotated.  Incidents follow
   `breach-response.md`.
4. **Keep current:** automatic operating system security updates;
   dependency vulnerability checks on every change and weekly.
5. **Test:** quarterly review of these controls; monthly automatic
   restore test of the backups.

## Physical safeguards

1. Data lives in the hosting provider's data centre and in encrypted
   off-site backups.  Devices used for the business (laptop, phone) use
   full-disk encryption, a screen lock and a password manager.
2. Paper with customer details (packing slips, labels) is kept in the
   packing room and shredded once no longer needed.
3. **Disposal:** customer data no longer needed for orders, returns,
   taxes (7 years for order and tax records) or law is deleted; backups
   expire on their retention schedule (up to 12 months).  Devices and
   drives are wiped before disposal.

_Signed: ______________________ (owner)  Date: __________ — Next review: ___________
