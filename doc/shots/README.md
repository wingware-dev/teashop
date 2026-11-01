# Milestone screenshots

A record of how the site looked at each stage of development.  Each
folder is one milestone, named `<date>-<milestone>`, and holds a
full-page screenshot of every page the browser tests visit, named
`<page>-<phone|desktop>-<light|dark>.png`.

Record a milestone (all browser tests must pass, including the WCAG 2.2
AA checks) with:

```sh
.venv/bin/python manage.py milestone_shots phase2-inventory
```

Then add the new folder to version control.  Everyday test runs put
their screenshots in `var/shots/` instead, which is not kept.

The pages and checks come from the browser tests (`apps/*/tests/test_ui.py`,
built on `apps/core/uitesting.py`); add a test there for each new page so
it shows up in the next milestone.
