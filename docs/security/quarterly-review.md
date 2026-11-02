# The quarterly security review

Once a quarter, about an hour.  The checklist is at **owner/ops/review/**
(dashboard Shortcuts: "Server health and security", then "Quarterly
security review"); what the shop already knows is filled in under each
item.  Tick each item, write what you found, fixed or skipped in the
notes, and **Record the review**.  It goes in the audit log and on the
Operations card; from the second month of a quarter, an unfinished review
is on the attention list.

This review is the "risk assessment" of the security policy
([security-policy.md](security-policy.md)), so it also keeps the shop in
line with New York's SHIELD Act.

## The checklist

1. **The server is up to date.**  The server page shows no security
   updates waiting, no restart pending and no failed services, and the
   daily upkeep ran this week.  Carry out or decline the open proposals.
2. **Backups restore.**  A monthly restore test succeeded this quarter
   (Operations card).  Once a year, restore a backup on a spare server
   yourself ([../ops/backups.md](../ops/backups.md)).
3. **No known vulnerable packages.**  On GitHub: the latest CI run's
   "Known vulnerabilities in dependencies" step passed; no Dependabot
   alerts (Security tab) or pull requests are waiting.  To upgrade
   Python packages see docs/ops/README.md ("Server upkeep").
4. **Changes had their security review.**  GitHub > Actions > CI: each
   change's "Security review" job passed.  If you turned the AI review on,
   read its job summaries: anything marked medium or high was fixed or has
   a good reason not to be.
5. **The outside scan is clean.**  GitHub > Actions > "Outside
   vulnerability scan" > Run workflow (needs the variable
   `OUTSIDE_SCAN=on`).  Read the summary: "FAIL" or "WARN" lines need a
   look; ask someone you trust about any you don't understand.  Also check
   the site at ssllabs.com/ssltest (expect grade A) and
   securityheaders.com (expect A or better).
6. **Only the right people can sign in.**  Every staff account listed is
   someone who still needs it, with two-factor on.  Remove the rest in the
   admin (Users).
7. **Only your keys open the server.**  As your admin account:
   `sudo cat /home/*/.ssh/authorized_keys`.  You should see your own
   key(s), GitHub Actions' deploy key (`command=".../ssh-deploy-command.sh"`)
   and the ops agent's (`command="/usr/local/sbin/teashop-ops-command"`).
   Remove any other line, then follow
   [breach-response.md](breach-response.md).
8. **The AI agents did only what they should.**  owner/agents/: this
   quarter's spending, and what each agent did.  Each support category
   answered alone should still deserve to be.
9. **No sign-in attacks got through.**  The failed sign-in count is
   shown; many is normal (the lockout stops them).  A successful sign-in
   you don't recognise in the audit log means: breach-response.md.
10. **Secrets are where they belong.**  `ls -l /srv/teashop/.env` shows
    `-rw------- deploy deploy`; your password manager has
    `RESTIC_PASSWORD` and the two-factor backup codes; replace any key or
    password that may have leaked (an old laptop, a shared screen).
11. **The breach plan still works.**  Re-read
    [breach-response.md](breach-response.md): the contacts and accounts
    are still right.
12. **Ubuntu is supported.**  More than a year of security support left
    (shown), or a move to a newer release planned (the agent proposes it a
    year ahead).

## The security checks that run by themselves

| What | When | Where you see it |
|---|---|---|
| pip-audit on every pinned Python package | every push, and weekly | CI's "Known vulnerabilities in dependencies" |
| Dependabot: Docker base images and GitHub Actions | weekly pull requests | GitHub > Pull requests |
| Dependabot alerts on the locked packages | as advisories appear (turn on: Settings > Code security > Dependabot alerts) | GitHub > Security |
| bandit (Python security checks) and Django's production security checks | every push | CI's "Security review" job |
| AI security review of each change (optional, costs money) | every push and pull request once turned on | the "Security review" job's summary |
| Outside scan (OWASP ZAP baseline, passive) | monthly once turned on, or by hand | Actions > "Outside vulnerability scan" |
| Server health and updates | hourly and daily | owner/ops/ |
