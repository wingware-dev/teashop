# Breach response checklist

Use this the moment you suspect someone got at customer data or the
server: an alert, odd activity in the audit log, a customer report, a
provider's notice.  Work down the list and **write down what you do and
when** (a dated text file outside the server is fine): the notices and any
investigation depend on it.

_This is a practical checklist, not legal advice.  Breach laws change;
check the current rules (links at the end) and talk to a lawyer before
sending notices._

## 1. Contain (first hour)

- [ ] Note the time you found out (the notification clock starts here).
- [ ] If the server may be compromised: at the VPS provider, **take a
      snapshot** (evidence), then cut it off (provider firewall: deny all
      but your own address) or power it off.  Don't delete anything.
- [ ] Change your passwords: VPS provider, GitHub, Cloudflare, Stripe,
      email, B2, password manager.  Check two-factor is on for each.
- [ ] Revoke and replace keys: SSH keys on the server, the GitHub deploy
      key and CI key, the B2 application key, API keys in `.env`
      (Stripe, shipping, email, AI), `DJANGO_SECRET_KEY` (signs everyone
      out).
- [ ] If an account on the shop was misused: disable it in the admin.
- [ ] If an AI agent misbehaved: turn it off and keep its logs.

## 2. Assess (first days)

- [ ] What happened, when, and how?  Look at the audit log (who changed
      or exported what), `docker compose logs`, `journalctl -u ssh`,
      fail2ban, Cloudflare and provider logs, Stripe dashboard.
- [ ] **Which data, for which people?**  List the affected customers and
      the states they live in.
- [ ] Was it "private information" under New York law?  A name or other
      identifier together with: Social Security number; driver's license
      or ID number; account or card number with any code that allows
      access (or without, if usable alone); biometric data; medical or
      health insurance information; **or** a username or email address
      with its password or security question answers.  Email, name and
      address alone are not, but customers may still deserve to know.
      We don't hold card numbers (Stripe does); customer account
      passwords are hashed, but a hash leak still means "reset passwords".
- [ ] Was the data encrypted and the key not taken?  Then notification
      may not be required; record why.

## 3. Recover

- [ ] Rebuild rather than clean: a fresh server from `docs/ops/README.md`,
      code from GitHub, data restored from the last backup **from before
      the intrusion** (`docs/ops/backups.md`).  Check the restored data.
- [ ] Fix how they got in before going live again.
- [ ] Force a password reset for affected customer accounts.

## 4. Notify (as fast as possible; New York: within 30 days of discovery)

New York (General Business Law § 899-aa), when private information of NY
residents was, or reasonably may have been, accessed or acquired:

- [ ] **Affected NY residents**: by letter or email (email only if they
      agreed to receive notices that way); phone is also allowed.  Say:
      what happened and when; what kinds of information; what you are
      doing; what they can do; your contact details; and the phone numbers
      and websites of the state and federal agencies that help with
      identity theft (NY Department of State, FTC at identitytheft.gov).
      For a username and password leak, an email telling them to change
      their password (here and wherever they reused it) is enough.
- [ ] **New York Attorney General, Department of State and Division of
      State Police**: about when and how residents were notified, and how
      many.  The Attorney General has an online form.
- [ ] **More than 5,000 NY residents**: also the consumer reporting
      agencies (Equifax, Experian, TransUnion).
- [ ] **Customers in other states**: each state has its own law (many
      also require notifying their attorney general).  Check each state
      on the affected list.
- [ ] Law enforcement may ask you to delay notices; get that in writing.
- [ ] Tell affected providers (Stripe, VPS host) if their systems were
      involved.  Tell your insurer if you have cyber or business coverage.
- [ ] If an employee or contractor exposed data by mistake and you decide
      in good faith it is not likely to cause harm, notices may not be
      needed: **write that decision down and keep it 5 years**; for more
      than 500 NY residents, send it to the Attorney General within 10 days.

## 5. Afterwards

- [ ] Record the incident: timeline, cause, data, people, notices, fixes.
      Keep it at least 5 years.
- [ ] Update `security-policy.md` and the code or server setup so it
      can't happen the same way again.

## Contacts (fill in now, not during an incident)

| Who | Contact |
|---|---|
| VPS provider support / abuse | |
| Lawyer | |
| Insurer (policy number) | |
| NY Attorney General, data breach reporting | ag.ny.gov (search "data breach notification") |
| NY Department of State, Division of Consumer Protection | dos.ny.gov |
| NY State Police | troopers.ny.gov |
| FTC identity theft | identitytheft.gov |
