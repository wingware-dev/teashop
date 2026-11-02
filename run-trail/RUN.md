# Run trail

Generated 2026-11-01 23:56 from Wing's task store, the Tasks Manager's log, the agents' transcripts and the repository.  Times are local (-05:00).

## Totals

| | Time | Input | Output | Cache read | Cache write |
|---|---|---|---|---|---|
| Workers (53 tasks) | 7h 09m task time | 494k | 2.10M | 284.22M | 4.68M |
| Tasks Manager (its sessions over the run) |  | 2,998 | 160k | 99.73M | 513k |
| **Total** | 6h 25m elapsed | 497k | 2.26M | 383.95M | 5.20M |

- Questions from workers: 1 (answered by the user 0, by the Tasks Manager 0, unanswered 1)
- Questions the Tasks Manager passed to the user, Wing's included: 0
- Questions from the Tasks Manager to the user: 4
- Judgement calls: 204
- Findings filed: 14
- Commits: 37
- Tasks Manager decisions: 160

## Use of Wing's MCP tools

Wing gives the agents its IDE's features as tools on its MCP servers.  These are the calls the agents' transcripts record, their subagents' included; an error is a call its tool answered with one, refusals included.

| | Tool calls | To Wing's MCP tools | Errors |
|---|---|---|---|
| Workers (the 51 of 53 tasks with a transcript) | 2,829 | 885 (31%) | 2 |
| Tasks Manager | 720 | 669 (93%) | 34 |
| **Total** | 3,549 | 1,554 (44%) | 36 |

### By server

| Server | What it gives the agents | Calls by workers | Tasks using it | Calls by the Tasks Manager |
|---|---|---|---|---|
| wing-review | tasks, review, version control and project files | 746 | 51 | 669 |
| wing-analysis | Python code navigation and editing by scope | 9 | 5 | 0 |
| wing-testing | running tests and reading their results | 130 | 44 | 0 |
| wing-debug | the debugger: breakpoints, stack and values | 0 | 0 | 0 |

### Wing's tools

| Tool | Server | Calls by workers | Tasks using it | Calls by the Tasks Manager | Errors |
|---|---|---|---|---|---|
| create_tracked_file | wing-review | 548 | 21 | 0 | 0 |
| tasks_events | wing-review | 0 | 0 | 165 | 0 |
| test_run | wing-testing | 100 | 44 | 0 | 0 |
| wing_guide | wing-review | 82 | 39 | 1 | 0 |
| task_detail | wing-review | 0 | 0 | 76 | 0 |
| status_note | wing-review | 0 | 0 | 71 | 0 |
| task_note | wing-review | 0 | 0 | 65 | 0 |
| queue_assign | wing-review | 0 | 0 | 59 | 6 |
| task_report | wing-review | 58 | 51 | 0 | 1 |
| commit_queue | wing-review | 0 | 0 | 46 | 10 |
| annotate_task | wing-review | 0 | 0 | 42 | 6 |
| vcs_commit | wing-review | 36 | 36 | 0 | 0 |
| propose_tasks | wing-review | 0 | 0 | 32 | 1 |
| queue_start | wing-review | 0 | 0 | 30 | 0 |
| mark_ready | wing-review | 0 | 0 | 24 | 1 |
| test_get_details | wing-testing | 19 | 9 | 0 | 0 |
| queue_create | wing-review | 0 | 0 | 15 | 0 |
| tell_worker | wing-review | 0 | 0 | 15 | 2 |
| report_finding | wing-review | 14 | 11 | 0 | 0 |
| edit_scope | wing-analysis | 7 | 5 | 0 | 0 |
| ask_user | wing-review | 0 | 0 | 7 | 3 |
| test_list | wing-testing | 6 | 3 | 0 | 0 |
| vcs_status | wing-review | 1 | 1 | 4 | 0 |
| project_set | wing-review | 4 | 1 | 0 | 0 |
| resolve_review_comment | wing-review | 1 | 1 | 3 | 2 |
| move_task | wing-review | 0 | 0 | 3 | 0 |
| queue_remove | wing-review | 0 | 0 | 3 | 2 |
| debug_test | wing-testing | 3 | 1 | 0 | 0 |
| get_scope_code | wing-analysis | 2 | 2 | 0 | 0 |
| queue_unassign | wing-review | 0 | 0 | 2 | 1 |
| tasks_overview | wing-review | 0 | 0 | 2 | 0 |
| test_stale | wing-testing | 2 | 2 | 0 | 0 |
| answer_task | wing-review | 0 | 0 | 1 | 0 |
| edit_scope | wing-review | 1 | 1 | 0 | 1 |
| project_get | wing-review | 1 | 1 | 0 | 0 |
| send_review_comment | wing-review | 0 | 0 | 1 | 0 |
| tests_estimate | wing-review | 0 | 0 | 1 | 0 |
| vcs_diff | wing-review | 0 | 0 | 1 | 0 |

### Same job, Wing's tools or the agents' own

| Job | Wing's tools | Calls | The agents' own | Calls |
|---|---|---|---|---|
| Running tests | test_run, debug_test, debug_run_tests | 103 | pytest, unittest and the like in the shell | 29 |
| Finding code | find_definition, find_usages, find_symbols, get_scope_at_line | 0 | Grep and Glob tools; grep, rg and find in the shell | 483 |
| Looking at changes | vcs_status, vcs_diff, vcs_log | 6 | git and hg status, diff and log in the shell | 152 |
| Committing | vcs_commit, commit_queue | 82 | git and hg commit in the shell | 6 |

### The agents' own tools

- Workers: Bash 1,008, Edit 631, Read 164, ToolSearch 77, WebSearch 22, Write 21, WebFetch 18, Agent 1, SubagentHandback 1, TaskStop 1
- Tasks Manager: Bash 22, Read 18, ToolSearch 9, Write 2

## Timeline

| Time | Event |
|---|---|
| 2026-11-01 17:18 | Committed 30853735de93: Initial prompt updates |
| 2026-11-01 17:19 | T1 see-file-teashop-txt started |
| 2026-11-01 17:50 | T1 see-file-teashop-txt finished: done |
| 2026-11-01 17:50 | T2 phase1-infrastructure-skeleton started |
| 2026-11-01 18:18 | T2 phase1-infrastructure-skeleton finished: done |
| 2026-11-01 18:19 | Committed cb0bc831e434 for T2 phase1-infrastructure-skeleton: Phase 1 infrastructure skeleton: Django project, two-factor owner login, audit log, Docker deploy, server hardening, backups |
| 2026-11-01 18:19 | T3 ui-test-harness started |
| 2026-11-01 18:19 | The Tasks Manager asked the user: T2 phase1-infrastructure-skeleton (edd0e993) set the project's main entry point to 'Run dev server' (manage.py runser... |
| 2026-11-01 18:19 | The Tasks Manager asked the user: Do you approve creating the hosting accounts so the real server can be set up? T14 provision-server (cbcf7761) needs ... |
| 2026-11-01 18:20 | T4 phase2-catalog-inventory-core started |
| 2026-11-01 18:25 | T3 ui-test-harness finished: done |
| 2026-11-01 18:25 | Committed df693dc59fe2 for T3 ui-test-harness: Browser test harness with WCAG 2.2 AA checks and milestone screenshots |
| 2026-11-01 18:25 | T15 record-ops-events started |
| 2026-11-01 18:37 | T4 phase2-catalog-inventory-core finished: done |
| 2026-11-01 18:37 | T15 record-ops-events finished: done |
| 2026-11-01 18:37 | Committed 318916ede212 for T4 phase2-catalog-inventory-core and T15 record-ops-events: Phase 2 catalog and inventory core; ops events in the audit log and dashboard |
| 2026-11-01 18:38 | T19 regression-tests-foundation-inventory started |
| 2026-11-01 18:38 | T9 phase7-purchasing-loss-tracking started |
| 2026-11-01 18:38 | T5 phase3-storefront-design started |
| 2026-11-01 18:38 | T17 pin-ui-test-packages started |
| 2026-11-01 18:39 | T19 regression-tests-foundation-inventory finished: done |
| 2026-11-01 18:40 | T17 pin-ui-test-packages finished: done |
| 2026-11-01 18:40 | Committed 344e372f8c83 for T17 pin-ui-test-packages: Pin browser-test packages with hashes in requirements-ui.lock |
| 2026-11-01 18:40 | T20 pin-pip-audit-ci started |
| 2026-11-01 18:41 | T20 pin-pip-audit-ci filed T21 pillow-vulnerable-pin |
| 2026-11-01 18:41 | T20 pin-pip-audit-ci finished: done |
| 2026-11-01 18:41 | Committed da14a53eb443 for T20 pin-pip-audit-ci: Pin pip-audit with hashes in requirements-ci.lock |
| 2026-11-01 19:05 | T24 pass-label-settings-to-container started |
| 2026-11-01 19:14 | T21 pillow-vulnerable-pin finished: obsolete |
| 2026-11-01 19:15 | T9 phase7-purchasing-loss-tracking finished: done |
| 2026-11-01 19:15 | T5 phase3-storefront-design filed T24 pass-label-settings-to-container |
| 2026-11-01 19:15 | T5 phase3-storefront-design finished: done |
| 2026-11-01 19:15 | T24 pass-label-settings-to-container finished: done |
| 2026-11-01 19:15 | Committed 11ce69d83be5 for T9 phase7-purchasing-loss-tracking, T5 phase3-storefront-design and T24 pass-label-settings-to-container: Phase 3 storefront and phase 7 purchasing and loss tracking |
| 2026-11-01 19:15 | T6 phase4-cart-checkout started |
| 2026-11-01 19:15 | T26 shrink-milestone-screenshots started |
| 2026-11-01 19:20 | T26 shrink-milestone-screenshots finished: done |
| 2026-11-01 19:20 | Committed da7c1baf5f61 for T26 shrink-milestone-screenshots: Shrink milestone screenshots: 1x phone shots and lossless oxipng compression |
| 2026-11-01 19:50 | T33 regression-tests-after-checkout started |
| 2026-11-01 19:50 | T6 phase4-cart-checkout finished: done |
| 2026-11-01 19:50 | Committed 776b8825b26c for T6 phase4-cart-checkout: Phase 4 cart and checkout |
| 2026-11-01 19:54 | T33 regression-tests-after-checkout filed T35 checkout-deploy-checks-break-settings |
| 2026-11-01 19:54 | T33 regression-tests-after-checkout filed T34 compose-checkout-env-vars |
| 2026-11-01 19:54 | T33 regression-tests-after-checkout finished: done |
| 2026-11-01 19:55 | T34 compose-checkout-env-vars started |
| 2026-11-01 19:55 | T25 organic-wording-product-pages started |
| 2026-11-01 19:55 | T7 phase5-fulfillment-dashboard started |
| 2026-11-01 19:56 | T35 checkout-deploy-checks-break-settings started |
| 2026-11-01 19:58 | T34 compose-checkout-env-vars finished: done |
| 2026-11-01 19:58 | T35 checkout-deploy-checks-break-settings finished: done |
| 2026-11-01 19:58 | Committed 81616b891cb5 for T34 compose-checkout-env-vars and T35 checkout-deploy-checks-break-settings: Pass checkout settings to the web container; fix checkout deploy-check tests |
| 2026-11-01 19:58 | T30 shared-rate-limit-cache started |
| 2026-11-01 19:58 | T25 organic-wording-product-pages finished: done |
| 2026-11-01 19:58 | Committed 25c4f5a9a41c for T25 organic-wording-product-pages: Organic wording on product pages under the USDA small-business exemption |
| 2026-11-01 19:59 | T31 subscription-card-update started |
| 2026-11-01 20:27 | T7 phase5-fulfillment-dashboard finished: done |
| 2026-11-01 20:27 | T30 shared-rate-limit-cache finished: done |
| 2026-11-01 20:27 | T31 subscription-card-update finished: done |
| 2026-11-01 20:27 | Committed ddec0b27c225 for T7 phase5-fulfillment-dashboard, T30 shared-rate-limit-cache and T31 subscription-card-update: Phase 5 fulfillment dashboard, subscription card updates, shared rate-limit cache |
| 2026-11-01 20:27 | T29 background-job-queue started |
| 2026-11-01 20:27 | T41 net-refunds-from-tax-reports started |
| 2026-11-01 20:31 | T41 net-refunds-from-tax-reports finished: done |
| 2026-11-01 20:31 | Committed 97b350bafc60 for T41 net-refunds-from-tax-reports: Net refunds out of NY sales-tax and nexus figures |
| 2026-11-01 20:31 | T44 refund-records-tax started |
| 2026-11-01 20:43 | T29 background-job-queue finished: done |
| 2026-11-01 20:43 | T44 refund-records-tax finished: done |
| 2026-11-01 20:43 | Committed 8371a0532c29 for T29 background-job-queue and T44 refund-records-tax: Background job queue for emails and daily jobs; refunds record their sales tax |
| 2026-11-01 20:43 | The Tasks Manager asked the user: After the first deploy that includes T29 background-job-queue, run install-app.sh on the server again. That removes t... |
| 2026-11-01 20:43 | T42 net-returns-from-reorder-use started |
| 2026-11-01 20:43 | T10 phase8-email-list started |
| 2026-11-01 20:43 | T8 phase6-owner-dashboard-reporting started |
| 2026-11-01 20:44 | T42 net-returns-from-reorder-use finished: done |
| 2026-11-01 20:45 | Committed 97da9953f218 for T42 net-returns-from-reorder-use: Net returned stock out of reorder daily use |
| 2026-11-01 21:06 | T10 phase8-email-list finished: done |
| 2026-11-01 21:06 | T8 phase6-owner-dashboard-reporting filed T51 ny-tax-table-calendar-quarters |
| 2026-11-01 21:06 | T8 phase6-owner-dashboard-reporting finished: done |
| 2026-11-01 21:06 | Committed ccc52ca8f8f1 for T10 phase8-email-list and T8 phase6-owner-dashboard-reporting: Owner dashboard deadlines, reports and Wave summary (phase 6); marketing email list (phase 8) |
| 2026-11-01 21:07 | T51 ny-tax-table-calendar-quarters started |
| 2026-11-01 21:07 | T11 phase9-support-agent started |
| 2026-11-01 21:08 | T51 ny-tax-table-calendar-quarters finished: done |
| 2026-11-01 21:08 | Committed 10287803ff84 for T51 ny-tax-table-calendar-quarters: Group checkout's NY sales tax table by New York's filing quarters |
| 2026-11-01 21:29 | T11 phase9-support-agent asked: The support agent for the tea shop runs on an offline stand-in until it is given a Claude API key. My understanding i... |
| 2026-11-01 21:29 | The Tasks Manager asked the user: The AI agents (support now; marketing and ops next) run on a free offline stand-in until they get a Claude API key. W... |
| 2026-11-01 21:31 | T11 phase9-support-agent finished: done |
| 2026-11-01 21:31 | Committed 1adcd0719e2a for T11 phase9-support-agent: Customer support agent (phase 9) and shared AI-agent framework |
| 2026-11-01 21:31 | T55 regression-sweep-shop-pages started |
| 2026-11-01 21:35 | T55 regression-sweep-shop-pages finished: done |
| 2026-11-01 21:35 | T56 regression-sweep-backend started |
| 2026-11-01 21:38 | T56 regression-sweep-backend filed T60 compose-missing-phase6-env-vars |
| 2026-11-01 21:38 | T56 regression-sweep-backend finished: done |
| 2026-11-01 21:38 | T60 compose-missing-phase6-env-vars started |
| 2026-11-01 21:38 | T60 compose-missing-phase6-env-vars finished: done |
| 2026-11-01 21:38 | Committed cd96d7b1a2be for T60 compose-missing-phase6-env-vars: Pass phase-6 dashboard, Wave and estimated-tax settings to the containers |
| 2026-11-01 21:39 | T12 phase10-marketing-agent started |
| 2026-11-01 21:39 | T13 phase11-ops-security-agent started |
| 2026-11-01 22:03 | T12 phase10-marketing-agent filed T62 site-css-leaves-date |
| 2026-11-01 22:03 | T12 phase10-marketing-agent finished: done |
| 2026-11-01 22:03 | T13 phase11-ops-security-agent filed T61 fix-shellcheck-sc2164-deploy-scripts |
| 2026-11-01 22:03 | T13 phase11-ops-security-agent finished: done |
| 2026-11-01 22:03 | Committed 18ca28bc59d5 for T12 phase10-marketing-agent and T13 phase11-ops-security-agent: Marketing agent and calendar (phase 10); ops and security agent with CI security reviews (phase 11) |
| 2026-11-01 22:03 | T61 fix-shellcheck-sc2164-deploy-scripts started |
| 2026-11-01 22:03 | T62 site-css-leaves-date started |
| 2026-11-01 22:04 | T64 posts-attention-kind started |
| 2026-11-01 22:05 | T62 site-css-leaves-date finished: done |
| 2026-11-01 22:05 | Committed 91d3ea2713de for T62 site-css-leaves-date: Style url, date and datetime-local inputs like other form fields |
| 2026-11-01 22:05 | T61 fix-shellcheck-sc2164-deploy-scripts finished: done |
| 2026-11-01 22:05 | Committed 6c3df87654b3 for T61 fix-shellcheck-sc2164-deploy-scripts: Fix shellcheck SC2164 in deploy backup and ops-event scripts |
| 2026-11-01 22:05 | T64 posts-attention-kind finished: done |
| 2026-11-01 22:05 | Committed 4a4988908292 for T64 posts-attention-kind: Remind an hour after a by-hand post is due ("posts" attention kind) |
| 2026-11-01 22:05 | T65 milestone-shots-phase9-10 started |
| 2026-11-01 22:05 | T67 regression-sweep-phases-9-11 started |
| 2026-11-01 22:10 | T65 milestone-shots-phase9-10 filed T69 health-claim-label-overlap |
| 2026-11-01 22:10 | T65 milestone-shots-phase9-10 filed T68 calendar-empty-day-style |
| 2026-11-01 22:10 | T65 milestone-shots-phase9-10 filed T70 agent-audit-attribution |
| 2026-11-01 22:10 | T65 milestone-shots-phase9-10 finished: done |
| 2026-11-01 22:10 | Committed 6a6a8760b422 for T65 milestone-shots-phase9-10: Milestone screenshots for phase 10 (marketing) and refreshed phase 9 (support) |
| 2026-11-01 22:13 | T67 regression-sweep-phases-9-11 finished: done |
| 2026-11-01 22:14 | T70 agent-audit-attribution started |
| 2026-11-01 22:14 | T68 calendar-empty-day-style started |
| 2026-11-01 22:14 | T69 health-claim-label-overlap started |
| 2026-11-01 22:15 | T68 calendar-empty-day-style finished: done |
| 2026-11-01 22:15 | Committed be1a8845497c for T68 calendar-empty-day-style: Give marketing calendar days without posts the same style as the rest |
| 2026-11-01 22:16 | T69 health-claim-label-overlap finished: done |
| 2026-11-01 22:16 | Committed 6dd2fd5b9101 for T69 health-claim-label-overlap: Health-claim warnings: relabel "boosts ..." pattern and report overlapping matches once |
| 2026-11-01 22:18 | T70 agent-audit-attribution finished: done |
| 2026-11-01 22:18 | Committed 597bcda585fb for T70 agent-audit-attribution: Credit AI agents only with what they do on purpose |
| 2026-11-01 22:18 | T71 agent-guards-cover-queued-jobs started |
| 2026-11-01 22:23 | T71 agent-guards-cover-queued-jobs finished: done |
| 2026-11-01 22:23 | Committed c015e896a99d for T71 agent-guards-cover-queued-jobs: Make agent guards also refuse jobs an agent queued |
| 2026-11-01 22:24 | Committed 2cd941955edd: Main entry point for server |
| 2026-11-01 22:40 | T72 don-see-dashboard-set started |
| 2026-11-01 22:45 | T73 shipped-tab-late-badge started |
| 2026-11-01 22:46 | T72 don-see-dashboard-set filed T73 shipped-tab-late-badge |
| 2026-11-01 22:46 | T72 don-see-dashboard-set finished: done |
| 2026-11-01 22:46 | Committed 4acb92edff11 for T72 don-see-dashboard-set: Group back-office setup shortcuts on the dashboard; add load_demo_shop sample data |
| 2026-11-01 22:47 | T73 shipped-tab-late-badge finished: done |
| 2026-11-01 22:47 | Committed 418808b616df for T73 shipped-tab-late-badge: Shipped tab: judge lateness by the ship date, not today |
| 2026-11-01 22:47 | T74 demo-package-dimensions started |
| 2026-11-01 22:49 | T75 box-suggest-ignores-thick-package started |
| 2026-11-01 22:49 | T74 demo-package-dimensions filed T75 box-suggest-ignores-thick-package |
| 2026-11-01 22:49 | T74 demo-package-dimensions finished: done |
| 2026-11-01 22:49 | Committed 2eac01edd623 for T74 demo-package-dimensions: Add package dimensions for the demo tea sizes in load_demo_shop |
| 2026-11-01 22:52 | T75 box-suggest-ignores-thick-package finished: done |
| 2026-11-01 22:52 | Committed 5dca5dd57597 for T75 box-suggest-ignores-thick-package: Box suggestion: check every package's sides, not only the longest one's |
| 2026-11-01 22:54 | T76 graphic-design-site-bit started |
| 2026-11-01 23:08 | T76 graphic-design-site-bit finished: done |
| 2026-11-01 23:08 | Committed c6ecec10c58c for T76 graphic-design-site-bit: Add vine-and-leaf storefront design mockup |
| 2026-11-01 23:10 | T77 apply-vine-style-storefront started |
| 2026-11-01 23:29 | T77 apply-vine-style-storefront finished: done |
| 2026-11-01 23:29 | Committed 8941ec08c835 for T77 apply-vine-style-storefront: Apply the vine-and-leaf style to the customer pages |
| 2026-11-01 23:29 | T80 regression-sweep-vine-style finished: obsolete |
| 2026-11-01 23:29 | T81 regression-sweep-vine-style started |
| 2026-11-01 23:38 | T82 fix-shipped-tab-test-dst started |
| 2026-11-01 23:38 | T81 regression-sweep-vine-style filed T82 fix-shipped-tab-test-dst |
| 2026-11-01 23:38 | T81 regression-sweep-vine-style finished: done |
| 2026-11-01 23:40 | T82 fix-shipped-tab-test-dst finished: done |
| 2026-11-01 23:40 | Committed 2427b2c83ffd for T82 fix-shipped-tab-test-dst: Shipped-tab lateness test: build ship times from local calendar days |
| 2026-11-01 23:40 | T83 fulfillment-tests-localdate started |
| 2026-11-01 23:43 | T83 fulfillment-tests-localdate finished: done |
| 2026-11-01 23:43 | Committed 5eacc2cfb9d9 for T83 fulfillment-tests-localdate: Fulfillment tests: use the shop's date, not the machine's |

## Tasks

### T1 see-file-teashop-txt

- **Origin:** Written by the user
- **Goal:** Planning
- **Ran:** 2026-11-01 17:19 to 2026-11-01 17:50 (10m 02s)
- **Outcome:** done
- **Usage:** 227k input, 78k output, 920k cache read, 125k cache write (claude-haiku-5-5, claude-opus-5-5)
- **Tools:** 28 calls, 6 to Wing's MCP tools (wing-review 6)

**Prompt**

> See the file teashop.txt for a description of the project I want to start.
>
> [Tasks Manager, 2026-11-01 17:19] Manager: This is a read-only assessment and report, not code yet. Read teashop.txt in the project root. Report back with:
> (a) a fuller version of the requirements, including things the user may have forgotten;
> (b) feasibility per capability (1)-(6) and for the agent automation, with build-vs-buy recommendations (payments, USPS rates and labels, accounting and payroll, email list, hosting);
> (c) a rough time estimate per phase, with a suggested phase order (MVP first);
> (d) the open questions for the user as a list.
> Report it as a plan the user reads (plan_kind report). Taking screenshots into doc/shots starts once there is UI.
>
> See \<project>/.TASKS/notes/see-the-file-teashop-txt-for-a-description-of-the-project.md

**Judgement calls**

1. **Recommended a Python/Django + PostgreSQL stack** (report 1)
   The project is already set up for Python (.venv, Wing). Django's admin, security defaults and ORM speed up the inventory back office.
   Alternatives: Node/Next.js; Saleor (open-source Python commerce); Shopify plus custom apps
2. **Advised buying accounting, payroll, payments, tax and shipping labels instead of building them** (report 1)
   These carry legal or financial liability and are cheap to buy. Building them would push launch back by months.
3. **Treated a Shopify-style buy-everything platform as a fallback, not the plan** (report 1)
   The user explicitly wants custom software, but it was worth stating the trade-off honestly given limited capital.
4. **Reported this as read-only with open questions in notes** (report 1)
   The task asked only for a report; per the research guide, the choices go in notes for Review.
5. **Rated packing at home as feasible only with a 20-C license, not under the home-processor exemption** (report 2)
   State sources say home-processed food may be sold only within New York, and the official state licensing form names repacking tea as needing a license. I could not open the state's official approved-foods list (FSI-898D) to check tea itself, so this needs confirming with the Division of Food Safety.
   Alternatives: Treat the home-processor exemption as possibly enough until the state answers
6. **Advised buying tea from US importers at first rather than importing directly** (report 2)
   Importing yourself adds FDA prior notice, customs entries now that the de minimis exemption is gone, possible China tariffs and origin-marking duties, all on top of the launch work.
7. **Flagged that the Claude Code subscription may not cover the production AI agents** (report 2)
   The user plans to rely on the $100 a month subscription. Running support and marketing bots around the clock is a different use, so the plan budgets API usage until the terms are checked.
8. **Kept the earlier feasibility report and the user's answers unchanged as Part 1** (report 2)
   Each report replaces the previous notes, so leaving Part 1 out would lose it.
9. **Recommended launching without 'organic' claims, with tracking against the $5k threshold** (report 3)
   The user said 'possibly'. Certification costs $500-1,500 a year and takes paperwork, so it's best decided once demand is known.
   Alternatives: Certify before launch; Sell organic up to $5k a year uncertified
10. **Recommended US importers for at least the first \~6 months** (report 3)
   The user is undecided. Importing directly adds FDA prior notice, customs entries and tariff exposure during launch.

**Summary**

> Applied the user's answers to the legal review's new questions:
> - Living upstate removes NYC's business tax. The MTA commuter tax applies only in Dutchess, Orange or Putnam, and only above $150k of self-employment earnings.
> - A dedicated home room makes the 20-C home-annex license the plan.
> - Flavoured teas, blends and herbal teas add ingredient and allergen labels, checks on herbal ingredients and allergen-safe packing. All of them stay exempt from NY sales tax.
> - Organic is "possibly": launch without organic claims and track organic sales against the $5k certification threshold.
> - Sourcing is "not sure": start with US importers and revisit after about 6 months of sales.


### T2 phase1-infrastructure-skeleton

- **Origin:** Filed by the Tasks Manager from the plan of T1 see-file-teashop-txt, at the user's request
- **Goal:** Planning
- **Ran:** 2026-11-01 17:50 to 2026-11-01 18:18 (28m 18s)
- **Outcome:** done; committed [`cb0bc831e434`](https://github.com/wingware-dev/teashop/commit/cb0bc831e434d1dbf2dca2afe8bda17693600e99)
- **Usage:** 2,312 input, 143k output, 16.65M cache read, 225k cache write (claude-haiku-5-5, claude-opus-5-5)
- **Tools:** 186 calls, 81 to Wing's MCP tools (wing-review 79, wing-analysis 1, wing-testing 1)

**Prompt**

> Phase 1: infrastructure skeleton (Django project, VPS hardening, deploy, backups)
>
> From the report of T1 see-file-teashop-txt (6f896717), section (c) Phase 1 and sections '(5) Deployment, operations, security' and 'Recommended stack'. Full report: .TASKS/notes/see-the-file-teashop-txt-for-a-description-of-the-project.md
>
> Stack: Python + Django + PostgreSQL, HTMX for dashboards, Docker Compose, Caddy (automatic HTTPS), Cloudflare free tier, background jobs on Postgres or Redis. The user chose a self-run VPS (Hetzner, DigitalOcean, Linode or Vultr; about $10-30/month).
>
> Scope (1-2 weeks): Django project layout with one app per feature, so later phases can run side by side; owner login with two-factor; an audit log of admin and agent actions; Docker setup; CI deploy from git (GitHub Actions on push to a release branch) with a database backup before each deploy and a way to roll back; scripts and docs for Ubuntu LTS hardening (automatic security updates, firewall, SSH keys only, brute-force blocking); encrypted off-site backups (restic to Backblaze B2) with a restore test; uptime monitoring, error tracking and log rotation. Card data never touches the server (Stripe-hosted fields, PCI SAQ A). Write the one-page NY SHIELD security policy and the breach-response checklist.
>
> When this makes the project runnable, set the project's main entry point (wing_guide topic coding-practices, 'Using what you build').
>
> No real server, paid account or outside service is created or used without the user's approval. Prepare everything so it runs locally first.
>
> See \<project>/.TASKS/notes/phase-1-infrastructure-skeleton-django-project-vps-har.md

**Judgement calls**

1. **Django 5.2 LTS instead of Django 6.x**
   django-two-factor-auth 1.18 supports Django only up to 5.2; 5.2 gets security fixes until April 2028. Upgrade to 6.2 LTS once the library supports it.
   Alternatives: Django 6.1 with a self-written TOTP login on django-otp; Django 6.1 with django-two-factor-auth untested
2. **Admin server account gets passwordless sudo**
   It has no password (SSH keys only), so sudo couldn't ask for one; a lost sudo password is a real risk for a non-ops owner.
   Alternatives: Set a sudo password during hardening
3. **Automatic reboots at 04:30 UTC; Docker repo included in unattended upgrades**
   Keeps kernel and Docker patched without the owner doing anything; containers restart on their own (about a minute of downtime).
   Alternatives: Security updates without automatic reboots; Leave Docker updates manual
4. **Every model is audited by default via signals; exclusions listed in settings**
   Later feature apps (and agents) are audited without extra work; audit rows store a plain actor id so deleting a user never touches the log.
   Alternatives: Opt-in audit per model; Mirror only Django admin LogEntry
5. **Images built on the server from the git checkout, no image registry**
   Fewer accounts and secrets; builds are fast and the last 5 builds are kept for rollback.
   Alternatives: Build in GitHub Actions and push to GHCR
6. **Rollback swaps only the app image, never checks out older code**
   Checking out an older commit also brought back older deploy scripts (seen in testing); --restore-db now refuses a backup that wasn't taken before the running build unless --dump is given.
   Alternatives: Check out the target commit on rollback
7. **HSTS starts at one day; subdomain/preload deploy-check warnings silenced**
   Long HSTS, subdomains and preload are hard to undo before HTTPS is proven on the real domain; docs say when to raise it.
   Alternatives: One-year HSTS with subdomains from day one
8. **Hashed requirements.lock via uv; Dependabot for Actions and Docker only, weekly pip-audit in CI**
   Every deploy installs identical, verified packages; Dependabot does not maintain uv lock files.
   Alternatives: Unpinned ranges; pip-tools requirements.in/.txt so Dependabot can update Python packages
9. **Production admin at a random path (office-xxxx/), set by install-app.sh**
   Cuts scanner noise; still behind two-factor.
   Alternatives: Keep /admin/
10. **No stub apps for later phases; conventions in docs/architecture.md**
   Later phases pick their own app names; adding one is a one-line settings change.
   Alternatives: Pre-create empty inventory/catalog/storefront/checkout/fulfillment apps
11. **Dev server entry point uses --noreload**
   Plays well with Wing's debugger; template and code changes need a server restart.
   Alternatives: Use Django's autoreloader with child-process debugging
12. **Security policy runs about 1.5 pages**
   Covers each SHIELD Act safeguard category (administrative, technical, physical) concretely; has placeholders for business name, address and signature.
   Alternatives: Trim to strictly one page

**Summary**

> Phase 1 infrastructure skeleton, verified end to end in a local Docker stack (no real server or paid account used):
> - Django 5.2 LTS project (config/, apps/ with one app per feature), owner login with two-factor (django-two-factor-auth), admin behind it at a configurable path, login lockout (django-axes), health check, placeholder home and owner dashboard with light/dark styling
> - apps/audit: append-only audit log of all model changes, logins and agent actions (acting_as_agent/record API), secrets masked, PostgreSQL trigger blocks UPDATE/DELETE
> - Dockerfile, compose.yaml (PostgreSQL 17, gunicorn, Caddy auto-HTTPS, restic backup service), hashed requirements.lock, log rotation
> - deploy/deploy.sh (pre-deploy DB backup, migrate, health-checked start, automatic recovery) and deploy/rollback.sh (with guarded --restore-db); GitHub Actions CI (Postgres tests, pip-audit, shellcheck, image build) and deploy on push to release via a forced-command SSH key
> - deploy/server/harden.sh (Ubuntu 24.04: unattended upgrades with reboots, SSH keys only, ufw, fail2ban, Docker, journald caps) and install-app.sh with daily backup and monthly restore-test systemd timers
> - docs: README, docs/architecture.md, docs/ops (setup, deploy/rollback, backups to B2, monitoring), docs/security (NY SHIELD security policy, breach-response checklist)
> - Wing: test framework djangotest; main entry point "Run dev server" (manage.py runserver --noreload), plus "Migrate dev database"


### T3 ui-test-harness

- **Origin:** Filed by the Tasks Manager from the plan of T1 see-file-teashop-txt, at the user's request
- **Goal:** Planning
- **Ran:** 2026-11-01 18:19 to 2026-11-01 18:25 (5m 25s)
- **Outcome:** done; committed [`df693dc59fe2`](https://github.com/wingware-dev/teashop/commit/df693dc59fe2e04d52caadaec75329c44536198f)
- **Usage:** 1,980 input, 26k output, 2.26M cache read, 75k cache write (claude-haiku-5-5, claude-opus-5-5)
- **Tools:** 53 calls, 17 to Wing's MCP tools (wing-review 13, wing-testing 4)

**Prompt**

> Harness for driving the website as a user would, with milestone screenshots
>
> Needed by every UI phase from the report of T1 see-file-teashop-txt (6f896717) (invariant 12). Build a headless-browser harness (for example Playwright with pytest) that starts the Django dev server against a test database, drives pages in light and dark mode at phone and desktop widths, runs WCAG 2.2 AA checks (for example axe-core), and saves screenshots. Milestone screenshots go in doc/shots, as the user asked in teashop.txt, to keep a record of each stage of development. Runs after phase1-infrastructure-skeleton.
>
> [Tasks Manager, 2026-11-01 18:19] From T2 phase1-infrastructure-skeleton (edd0e993): build on apps/core/testing.py for signed-in pages (an owner with a TOTP device, verified login, current_token). Headless Chrome screenshots of the light theme (--blink-settings=preferredColorScheme=1) and the dark theme already work against the dev server. The project test framework is djangotest, and the 'Run dev server' entry point is manage.py runserver --noreload. Follow docs/architecture.md.
>
> See \<project>/.TASKS/notes/harness-for-driving-the-website-as-a-user-would-with-mil.md

**Judgement calls**

1. **Fixed the owner dashboard's activity table so it scrolls on its own instead of the whole page**
   The new sideways-scrolling check failed on it at 320px wide. The fix is two lines: a scroll wrapper with a label and keyboard focus, which the axe rule for scrollable regions needs. Without it, the first milestone could not be recorded.
   Alternatives: Report it as a finding and leave the test failing; Leave tables out of the sideways-scrolling check
2. **Browser tests are tagged `ui` and skipped, with install instructions, when Playwright is missing; CI installs Playwright so they run there**
   The lock file is runtime-only, and contributors can still run the rest of the tests without a browser. Installing it in CI means the WCAG checks still guard every push.
   Alternatives: Make Playwright a hard requirement; Leave browser tests out of CI
3. **Everyday runs write screenshots to var/shots/ (ignored by git); only `milestone_shots` writes to doc/shots/\<date>-\<name>/**
   If every test run wrote to doc/shots, it would keep changing the committed milestone record.
   Alternatives: Always write to doc/shots/latest
4. **Used axe-core from the axe-playwright-python package, run directly with the WCAG 2.x A/AA rule tags**
   It bundles axe-core 4.12, so there is no npm step and no copy of axe-core to keep in the repo.
   Alternatives: Use npm @axe-core/playwright; Keep a copy of axe.min.js in the repo
5. **Left the Django admin out of the browser tests**
   Its pages are Django's own design, not the site's, so they would fail on things this project does not control.
   Alternatives: Check admin pages too

**Screenshots**

![account-security-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/df693dc59fe2e04d52caadaec75329c44536198f/doc/shots/2026-11-01-phase1-skeleton/account-security-desktop-dark.png)

![account-security-desktop-light.png](https://github.com/wingware-dev/teashop/raw/df693dc59fe2e04d52caadaec75329c44536198f/doc/shots/2026-11-01-phase1-skeleton/account-security-desktop-light.png)

![account-security-phone-dark.png](https://github.com/wingware-dev/teashop/raw/df693dc59fe2e04d52caadaec75329c44536198f/doc/shots/2026-11-01-phase1-skeleton/account-security-phone-dark.png)

![account-security-phone-light.png](https://github.com/wingware-dev/teashop/raw/df693dc59fe2e04d52caadaec75329c44536198f/doc/shots/2026-11-01-phase1-skeleton/account-security-phone-light.png)

![home-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/df693dc59fe2e04d52caadaec75329c44536198f/doc/shots/2026-11-01-phase1-skeleton/home-desktop-dark.png)

![home-desktop-light.png](https://github.com/wingware-dev/teashop/raw/df693dc59fe2e04d52caadaec75329c44536198f/doc/shots/2026-11-01-phase1-skeleton/home-desktop-light.png)

![home-phone-dark.png](https://github.com/wingware-dev/teashop/raw/df693dc59fe2e04d52caadaec75329c44536198f/doc/shots/2026-11-01-phase1-skeleton/home-phone-dark.png)

![home-phone-light.png](https://github.com/wingware-dev/teashop/raw/df693dc59fe2e04d52caadaec75329c44536198f/doc/shots/2026-11-01-phase1-skeleton/home-phone-light.png)

![login-code-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/df693dc59fe2e04d52caadaec75329c44536198f/doc/shots/2026-11-01-phase1-skeleton/login-code-desktop-dark.png)

![login-code-desktop-light.png](https://github.com/wingware-dev/teashop/raw/df693dc59fe2e04d52caadaec75329c44536198f/doc/shots/2026-11-01-phase1-skeleton/login-code-desktop-light.png)

![login-code-phone-dark.png](https://github.com/wingware-dev/teashop/raw/df693dc59fe2e04d52caadaec75329c44536198f/doc/shots/2026-11-01-phase1-skeleton/login-code-phone-dark.png)

![login-code-phone-light.png](https://github.com/wingware-dev/teashop/raw/df693dc59fe2e04d52caadaec75329c44536198f/doc/shots/2026-11-01-phase1-skeleton/login-code-phone-light.png)

![login-password-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/df693dc59fe2e04d52caadaec75329c44536198f/doc/shots/2026-11-01-phase1-skeleton/login-password-desktop-dark.png)

![login-password-desktop-light.png](https://github.com/wingware-dev/teashop/raw/df693dc59fe2e04d52caadaec75329c44536198f/doc/shots/2026-11-01-phase1-skeleton/login-password-desktop-light.png)

![login-password-phone-dark.png](https://github.com/wingware-dev/teashop/raw/df693dc59fe2e04d52caadaec75329c44536198f/doc/shots/2026-11-01-phase1-skeleton/login-password-phone-dark.png)

![login-password-phone-light.png](https://github.com/wingware-dev/teashop/raw/df693dc59fe2e04d52caadaec75329c44536198f/doc/shots/2026-11-01-phase1-skeleton/login-password-phone-light.png)

![login-wrong-code-desktop-light.png](https://github.com/wingware-dev/teashop/raw/df693dc59fe2e04d52caadaec75329c44536198f/doc/shots/2026-11-01-phase1-skeleton/login-wrong-code-desktop-light.png)

![owner-dashboard-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/df693dc59fe2e04d52caadaec75329c44536198f/doc/shots/2026-11-01-phase1-skeleton/owner-dashboard-desktop-dark.png)

![owner-dashboard-desktop-light.png](https://github.com/wingware-dev/teashop/raw/df693dc59fe2e04d52caadaec75329c44536198f/doc/shots/2026-11-01-phase1-skeleton/owner-dashboard-desktop-light.png)

![owner-dashboard-phone-dark.png](https://github.com/wingware-dev/teashop/raw/df693dc59fe2e04d52caadaec75329c44536198f/doc/shots/2026-11-01-phase1-skeleton/owner-dashboard-phone-dark.png)

![owner-dashboard-phone-light.png](https://github.com/wingware-dev/teashop/raw/df693dc59fe2e04d52caadaec75329c44536198f/doc/shots/2026-11-01-phase1-skeleton/owner-dashboard-phone-light.png)

**Summary**

> Added a headless-browser test harness that checks every page for accessibility and records milestone screenshots in doc/shots.
> - `apps/core/uitesting.py`: `BrowserTestCase` (Django live server on the test database plus headless Chromium through Playwright). `check_page(path, name, signed_in=)` opens a page at phone and desktop widths in the light and dark themes. It fails on WCAG 2.2 A/AA violations found by axe-core, on JavaScript or HTTP errors, and on sideways scrolling at 320px, then saves full-page screenshots to `var/shots/`. Sign-in helpers build on `apps/core/testing.py`.
> - `apps/core/tests/test_ui.py`: browser tests for the home page, the two-step owner login (including a wrong code), the owner dashboard and the account security page. `test_uitesting.py` tests the harness's own helpers.
> - `manage.py milestone_shots <name>` runs the browser tests and writes their screenshots to `doc/shots/<date>-<name>/`. The first milestone, `2026-11-01-phase1-skeleton` (21 PNGs, 1.2 MB), is recorded and added to git.
> - The harness found that the dashboard's activity table made the page scroll sideways on phones. The table now scrolls inside its own labelled region.
> - Added `requirements-ui.txt` (also pulled in by requirements-dev). CI now installs Playwright and Chromium and keeps the screenshots as a CI download. README, `docs/architecture.md` and `doc/shots/README.md` explain how to use it.


### T4 phase2-catalog-inventory-core

- **Origin:** Filed by the Tasks Manager from the plan of T1 see-file-teashop-txt, at the user's request
- **Goal:** Planning
- **Ran:** 2026-11-01 18:20 to 2026-11-01 18:37 (16m 58s)
- **Outcome:** done; committed [`318916ede212`](https://github.com/wingware-dev/teashop/commit/318916ede2121a578d0511b11d440aa5845d93d6) (shared with T15 record-ops-events)
- **Usage:** 132 input, 102k output, 7.26M cache read, 164k cache write (claude-opus-5-5)
- **Tools:** 91 calls, 35 to Wing's MCP tools (wing-review 32, wing-testing 3)

**Prompt**

> Phase 2: catalog and inventory core
>
> From the report of T1 see-file-teashop-txt (6f896717), section (c) Phase 2 and section '(1) Inventory'. Full report: .TASKS/notes/see-the-file-teashop-txt-for-a-description-of-the-project.md
>
> Scope (3-4 weeks): item types (bulk tea tracked by weight to the gram; packaging, merch, accessories and shipping boxes tracked by unit); products and size options (pouch and tin sizes, set per tea in inventory, with smaller sizes for expensive teas); bills of materials (for example 'Assam 50 g tin' = 50 g Assam + 1 tin + 1 label); recipes with ingredient lots for blends and flavoured or herbal teas, so a blend lot traces back to each component lot; lots (supplier, harvest year, date received, landed cost per kg including tariffs, best-by date, country of origin, organic status, allergen statement and spec-sheet documents); receiving, including partial deliveries; stock adjustments; low-stock alerts. Start in the Django admin.
>
> The user's answers: the tea stays in bulk and is weighed and packed when each order arrives, not ahead. Expect about 30-40 teas at launch, in plastic pouches and tins (sizes TBD).
>
> Legal requirements from Part 2: lot traceability from supplier lot to customer order (for recalls); organic sales tracked against the $5k/year certification threshold, with an alert at about $4k; data for the per-package label (name, net weight in oz and g, 'Grown in \<country>', ingredients and allergens, lot code, best-by date, packer address).
>
> [Tasks Manager, 2026-11-01 18:19] From T2 phase1-infrastructure-skeleton (edd0e993): follow docs/architecture.md. Put new apps under apps/ and add them to LOCAL_APPS in config/settings.py. Back-office views use apps.core.decorators.owner_required, and tests use apps.core.testing (make_owner, login_verified). Model changes are audited automatically.
>
> See \<project>/.TASKS/notes/phase-2-catalog-and-inventory-core.md

**Judgement calls**

1. **No packing runs ahead of orders; catalog.services.pack() packs one package per order instead**
   The user said tea is weighed and packed when each order arrives. pack() records a SoldPackage tying the order reference to the tea lot, for recalls and organic totals. Fulfillment (phase 5) calls it.
   Alternatives: Keep packing runs that build finished-package stock
2. **Each package's tea comes from one lot; remnants too small for a package are skipped**
   The label names a single lot code and best-by date. Packaging pieces can be spread across lots.
   Alternatives: Split a package across two lots and print both codes
3. **Organic sales count only products ticked 'sold as organic', and those pack from organic lots only**
   The $5k exemption is about sales made as organic. A certified lot sold without an organic claim shouldn't count, which matches the advice to launch without organic claims.
   Alternatives: Count every sale from an organic lot
4. **Supplier documents go in a private storage that Caddy refuses (/media/private/), downloaded through an owner-only view**
   Public media is served straight from the volume. Spec sheets, invoices and packing slips shouldn't be public. They stay in the media volume, so backups still cover them. Downloads are sandboxed, and only PDFs, images and text open in the browser.
   Alternatives: Keep them in public media with random names
5. **Added a small attention-provider registry to core and a list on the dashboard**
   core can't import feature apps (docs/architecture.md), and low-stock and organic alerts need a place to show. Another task was editing the same dashboard view and template (ops status) at the same time. I added my list next to its lines without changing them.
   Alternatives: Show the alerts only as admin list filters
6. **Allergens are stored per lot (the 9 major US allergens, seeded), not per item**
   The supplier's statement for each lot is the source of truth, and blends combine the allergens of their actual ingredient lots.
   Alternatives: Item-level defaults copied to new lots
7. **Included simple purchase orders now, though reorder suggestions and draft POs are phase 7**
   Partial deliveries only make sense measured against an order. Receipts work with or without a PO.
   Alternatives: Receipts only; add POs in phase 7
8. **A lot's received quantity is fixed once saved; corrections go through adjustments**
   It keeps on-hand stock equal to the sum of the lot's movements, which recalls and loss tracking rely on.
   Alternatives: Let the received quantity be edited, with a correcting movement posted automatically

**Summary**

> Phase 2 catalog and inventory core: two new apps, `apps/inventory` and `apps/catalog`, worked through the Django admin.
> - Inventory: suppliers; items tracked by weight (tea, herbs, flavourings) or by piece (packaging, shipping boxes, merch, accessories); lots carrying supplier, supplier lot code, harvest year, received date, landed cost per kg with the tariff part, best-by, country of origin, organic status, the nine major allergens plus the supplier's allergen statement, and private spec-sheet and certificate documents; append-only stock movements; purchase orders and receipts, with partial deliveries; stock adjustments with reasons (samples and giveaways count as marketing, not loss).
> - Blends: recipes (grams per kg, adding up to 1000) and blend batches that use specific ingredient lots (picked by oldest best-by when none are given) and make a blend lot. The blend lot inherits countries, allergens, ingredients in order of weight, the earliest best-by and the weighted cost.
> - Traceability and recalls: a trace page and a Recall admin action follow a supplier lot through every blend made from it to the customer order references; Put on hold stops packing from a lot.
> - Catalog: products, size options per tea (net grams and price), and a bill of materials per size. `pack()` takes one package's materials from stock for an order, with the tea from a single lot, oldest best-by first. `label_for()` gives the label facts: name, net weight in oz (rounded down) and g, "Grown in …", ingredients, "Contains: …", lot code, best-by, packer address. Organic sales are totalled per calendar year.
> - Dashboard alerts through a new `apps.core.attention` registry: low stock, lots near or past best-by, lots on hold, sizes that can't be packed, organic sales from $4k toward the $5k limit. Docs: `docs/inventory.md` (owner how-to) and a section in `docs/architecture.md`.


### T15 record-ops-events

- **Origin:** Filed by the Tasks Manager from the plan of T2 phase1-infrastructure-skeleton
- **Goal:** Planning
- **Ran:** 2026-11-01 18:25 to 2026-11-01 18:37 (5m 47s)
- **Outcome:** done; committed [`318916ede212`](https://github.com/wingware-dev/teashop/commit/318916ede2121a578d0511b11d440aa5845d93d6) (shared with T4 phase2-catalog-inventory-core)
- **Usage:** 1,718 input, 29k output, 2.31M cache read, 76k cache write (claude-haiku-5-5, claude-opus-5-5)
- **Tools:** 44 calls, 11 to Wing's MCP tools (wing-review 9, wing-testing 2)

**Prompt**

> Record ops events in the audit log and owner dashboard
>
> Follow-up from T2 phase1-infrastructure-skeleton (edd0e993). Have deploy/deploy.sh, deploy/rollback.sh, the backup job and the restore test call a small management command (for example `manage.py record_ops_event`), so deploys, rollbacks and backup or restore results show in the audit log (apps/audit) and on the owner dashboard, not only in the journal.
>
> See \<project>/.TASKS/notes/record-ops-events-in-the-audit-log-and-owner-dashboard.md

**Judgement calls**

1. **Backup and restore results are recorded by a host-side wrapper, not from inside the backup container**
   The backup image (postgres + restic) has no Django. The wrapper runs the container, then runs the command in the web image, so the backup image is unchanged.
   Alternatives: Install Django/app code in the backup image; systemd ExecStopPost hooks
2. **Recording is best effort and never changes a script's exit status**
   If the database is down or the first deploy fails, there is nowhere to record. Recording must not turn a good deploy into a failed one or hide a backup failure from systemd.
   Alternatives: Fail the deploy if recording fails
3. **Failed or overdue jobs are listed under 'Needs your attention' in the dashboard template itself, not through apps/core/attention.py**
   attention.py is new, uncommitted work from another task and the dashboard doesn't call collect() yet. Building on it would tie this commit to that one.
   Alternatives: Register an attention provider in apps/core/attention.py
4. **'Overdue' thresholds: backup 2 days, restore test 33 days; a job that has never run is shown as 'Never', not as an alarm**
   These match the daily and monthly timers with slack for one late run. Not alarming before a job's first run keeps new servers and dev machines quiet.
   Alternatives: Flag 'no backup ever recorded' as urgent
5. **A rollback that is refused or cancelled at the prompt is not recorded; only one that has started is**
   Records only real changes to what is running.
   Alternatives: Record every invocation
6. **Added a --danger colour (red, bold text) for failed or overdue statuses, and sample ops events to the dashboard browser test, so milestone screenshots will show them**
   Failures need to stand out; the word 'Failed' or 'Overdue' is also shown, so it doesn't rely on colour alone. axe contrast checks passed in light and dark.

**Summary**

> Deploys, rollbacks, backups and restore tests now record their result in the audit log, and the owner dashboard shows it.
> - New `manage.py record_ops_event <deploy|rollback|backup|restore_test> <succeeded|failed>` command (`apps/audit/ops.py`). It records a system audit event `ops.<kind>_<outcome>` with the commit, the message and extra details.
> - `deploy/record-ops-event.sh` runs the command in the running build. It is best effort: if it can't record, it logs a note and never fails the deploy. `deploy.sh` and `rollback.sh` record success, and record failure through an EXIT trap.
> - New `deploy/backup-job.sh backup|restore-test` wrapper runs the job in the backup container. It records the result with the snapshot id, the restored counts or the first error, and exits with the job's own status. The systemd units and the backup docs now use it.
> - Owner dashboard: a new "Operations" card shows the last run of each job. "Needs your attention" lists a failed run, or an overdue one: no successful backup for 2 days, or restore test for 33 days.


### T19 regression-tests-foundation-inventory

- **Origin:** Filed by the Tasks Manager
- **Goal:** Planning
- **Ran:** 2026-11-01 18:38 to 2026-11-01 18:39 (1m 08s)
- **Outcome:** done
- **Usage:** 1,818 input, 1,907 output, 165k cache read, 19k cache write (claude-haiku-5-5, claude-opus-5-5)
- **Tools:** 6 calls, 5 to Wing's MCP tools (wing-review 3, wing-testing 2)

**Prompt**

> Regression tests for the foundation and inventory work
>
> Covers T2 phase1-infrastructure-skeleton (edd0e993), T3 ui-test-harness (0223cfbe), T15 record-ops-events (29373a71) and T4 phase2-catalog-inventory-core (4d8a1a2b). T15 and T4 were built side by side and both edited apps/core/views.py and owner_dashboard.html; T4 also added new apps and a STORAGES entry. This is a sweep under wing_guide topic 'research': one test_run of the whole 'apps' directory, including the browser tests in apps/core/tests/test_ui.py. File each failure with report_finding (next_step fix); don't fix anything.
>
> See \<project>/.TASKS/notes/regression-tests-for-the-foundation-and-inventory-work.md

**Summary**

> Ran one test_run of the whole `apps` directory, browser tests in apps/core/tests/test_ui.py included. It covers T2 phase1-infrastructure-skeleton (edd0e993), T3 ui-test-harness (0223cfbe), T15 record-ops-events (29373a71) and T4 phase2-catalog-inventory-core (4d8a1a2b).
> - 138 tests: 137 passed, 0 failed, 1 skipped (run ID 1793576309570).
> - The skip is intentional ("trigger exists on PostgreSQL only"), since the run uses the non-PostgreSQL test database.
> - No findings filed, nothing fixed in place.


### T9 phase7-purchasing-loss-tracking

- **Origin:** Filed by the Tasks Manager from the plan of T1 see-file-teashop-txt, at the user's request
- **Goal:** Planning
- **Ran:** 2026-11-01 18:38 to 2026-11-01 19:15 (13m 50s)
- **Outcome:** done; committed [`11ce69d83be5`](https://github.com/wingware-dev/teashop/commit/11ce69d83be51a2b6083b6675037bc52ea868582) (shared with T5 phase3-storefront-design and T24 pass-label-settings-to-container)
- **Usage:** 2,325 input, 75k output, 14.09M cache read, 111k cache write (claude-haiku-5-5, claude-opus-5-5)
- **Tools:** 101 calls, 25 to Wing's MCP tools (wing-review 19, wing-testing 6)

**Prompt**

> Phase 7: purchasing and loss tracking
>
> From the report of T1 see-file-teashop-txt (6f896717), section (c) Phase 7 and section '(1) Inventory'. Full report: .TASKS/notes/see-the-file-teashop-txt-for-a-description-of-the-project.md
>
> Scope (2 weeks): supplier list and lead times; reorder points worked out from how fast each item sells plus lead time; draft purchase orders that the user approves (nothing that costs money happens without approval); receiving against purchase orders; regular stock counts with discrepancies recorded by reason (spoiled, damaged, sample, personal use, unknown); loss trends; free samples and giveaways recorded as marketing expense, not loss; profitability per tea and per item, using landed cost per lot (including tariffs).
>
> [Tasks Manager, 2026-11-01 18:37] From T4 phase2-catalog-inventory-core (4d8a1a2b): suppliers, simple purchase orders with receipts (including partial deliveries) and stock adjustments with reasons already exist in apps/inventory. Samples and giveaways already count as marketing, not loss. Build reorder points, draft POs for approval, stock counts, loss trends and profitability on top of them. Dashboard alerts go through apps/core/attention.py. See docs/inventory.md.
>
> See \<project>/.TASKS/notes/phase-7-purchasing-and-loss-tracking.md

**Judgement calls**

1. **Profit is worked out at report time from lot costs; no cost snapshot on SoldPackage**
   The storefront task (T5) was rewriting apps/catalog/models.py and adding catalog migrations at the same time; the Manager asked to keep catalog changes minimal and avoid two migration leaves. Each package records its tea lot and grams, so the tea cost is exact. Packaging uses the item's average landed cost, so a cost corrected later on a lot changes past reports.
   Alternatives: Add tea, tariff and packaging cost fields to SoldPackage, filled in by pack()
2. **Reorder math lives in apps/inventory/reorder.py, the rest in a new apps/purchasing app**
   Inventory's existing low-stock alert needs the computed levels, and inventory can't import purchasing. Purchase orders stay in inventory, where phase 2 put them.
   Alternatives: Everything in apps/purchasing, with inventory's alert keeping fixed levels only
3. **Automatic reorder levels are on by default for every item, with the item's own level as a floor**
   The task asks for reorder points worked out from usage plus lead time. Keeping the manual level as a floor means no existing alert gets quieter; untick 'automatic reorder level' to use only the fixed one.
   Alternatives: Off by default, opt in per item
4. **Demand counts orders, blend use and samples or giveaways; losses and count corrections don't count**
   Losses are irregular and would push reorder levels up. Samples are regular marketing use that still needs restocking.
   Alternatives: Count every outgoing movement
5. **Approval means 'approve and mark ordered'; the owner still sends the order to the supplier**
   The app has no supplier ordering integration, and nothing that costs money should happen automatically. The order's status is no longer editable by hand: drafts move on only through approval.
   Alternatives: Email the purchase order to the supplier on approval
6. **Deliveries can't be received against draft or cancelled purchase orders**
   This makes approval meaningful. A delivery without an order can still be received with no purchase order.
   Alternatives: Allow it and warn
7. **Personal use is reported separately from loss and from marketing**
   It's the owner's own use (a draw), not shrinkage. The task lists it among the discrepancy reasons, and it is still recorded and shown.
   Alternatives: Count personal use as loss
8. **Added a small no-wrap style for report figures in static/css/site.css**
   The screenshots showed months and amounts wrapping across lines on phones.
   Alternatives: Inline styles in the purchasing templates

**Screenshots**

![account-security-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/account-security-desktop-dark.png)

![account-security-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/account-security-desktop-light.png)

![account-security-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/account-security-phone-dark.png)

![account-security-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/account-security-phone-light.png)

![collection-this-weeks-picks-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/collection-this-weeks-picks-desktop-dark.png)

![collection-this-weeks-picks-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/collection-this-weeks-picks-desktop-light.png)

![collection-this-weeks-picks-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/collection-this-weeks-picks-phone-dark.png)

![collection-this-weeks-picks-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/collection-this-weeks-picks-phone-light.png)

![coming-soon-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/coming-soon-desktop-dark.png)

![coming-soon-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/coming-soon-desktop-light.png)

![coming-soon-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/coming-soon-phone-dark.png)

![coming-soon-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/coming-soon-phone-light.png)

![login-code-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/login-code-desktop-dark.png)

![login-code-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/login-code-desktop-light.png)

![login-code-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/login-code-phone-dark.png)

![login-code-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/login-code-phone-light.png)

![login-password-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/login-password-desktop-dark.png)

![login-password-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/login-password-desktop-light.png)

![login-password-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/login-password-phone-dark.png)

![login-password-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/login-password-phone-light.png)

![login-wrong-code-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/login-wrong-code-desktop-light.png)

![menu-teas-open-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/menu-teas-open-desktop-light.png)

![merch-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/merch-desktop-dark.png)

![merch-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/merch-desktop-light.png)

![merch-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/merch-phone-dark.png)

![merch-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/merch-phone-light.png)

![merch-product-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/merch-product-desktop-dark.png)

![merch-product-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/merch-product-desktop-light.png)

![merch-product-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/merch-product-phone-dark.png)

![merch-product-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/merch-product-phone-light.png)

![owner-dashboard-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/owner-dashboard-desktop-dark.png)

![owner-dashboard-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/owner-dashboard-desktop-light.png)

![owner-dashboard-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/owner-dashboard-phone-dark.png)

![owner-dashboard-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/owner-dashboard-phone-light.png)

![owner-page-design-preview-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/owner-page-design-preview-desktop-dark.png)

![owner-page-design-preview-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/owner-page-design-preview-desktop-light.png)

![owner-page-design-preview-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/owner-page-design-preview-phone-dark.png)

![owner-page-design-preview-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/owner-page-design-preview-phone-light.png)

![owner-page-designs-after-approve-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/owner-page-designs-after-approve-desktop-light.png)

![owner-page-designs-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/owner-page-designs-desktop-dark.png)

![owner-page-designs-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/owner-page-designs-desktop-light.png)

![owner-page-designs-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/owner-page-designs-phone-dark.png)

![owner-page-designs-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/owner-page-designs-phone-light.png)

![product-allergens-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/product-allergens-desktop-dark.png)

![product-allergens-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/product-allergens-desktop-light.png)

![product-allergens-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/product-allergens-phone-dark.png)

![product-allergens-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/product-allergens-phone-light.png)

![product-design-story-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/product-design-story-phone-light.png)

![product-design-wide-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/product-design-wide-desktop-dark.png)

![product-design-wide-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/product-design-wide-desktop-light.png)

![product-design-wide-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/product-design-wide-phone-dark.png)

![product-design-wide-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/product-design-wide-phone-light.png)

![product-herbal-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/product-herbal-desktop-dark.png)

![product-herbal-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/product-herbal-desktop-light.png)

![product-herbal-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/product-herbal-phone-dark.png)

![product-herbal-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/product-herbal-phone-light.png)

![product-photos-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/product-photos-desktop-dark.png)

![product-photos-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/product-photos-desktop-light.png)

![product-photos-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/product-photos-phone-dark.png)

![product-photos-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/product-photos-phone-light.png)

![purchasing-losses-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/purchasing-losses-desktop-dark.png)

![purchasing-losses-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/purchasing-losses-desktop-light.png)

![purchasing-losses-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/purchasing-losses-phone-dark.png)

![purchasing-losses-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/purchasing-losses-phone-light.png)

![purchasing-profit-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/purchasing-profit-desktop-dark.png)

![purchasing-profit-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/purchasing-profit-desktop-light.png)

![purchasing-profit-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/purchasing-profit-phone-dark.png)

![purchasing-profit-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/purchasing-profit-phone-light.png)

![purchasing-reorder-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/purchasing-reorder-desktop-dark.png)

![purchasing-reorder-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/purchasing-reorder-desktop-light.png)

![purchasing-reorder-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/purchasing-reorder-phone-dark.png)

![purchasing-reorder-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/purchasing-reorder-phone-light.png)

![region-darjeeling-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/region-darjeeling-desktop-dark.png)

![region-darjeeling-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/region-darjeeling-desktop-light.png)

![region-darjeeling-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/region-darjeeling-phone-dark.png)

![region-darjeeling-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/region-darjeeling-phone-light.png)

![regions-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/regions-desktop-dark.png)

![regions-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/regions-desktop-light.png)

![regions-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/regions-phone-dark.png)

![regions-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/regions-phone-light.png)

![search-no-results-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/search-no-results-phone-dark.png)

![search-no-results-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/search-no-results-phone-light.png)

![search-results-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/search-results-desktop-dark.png)

![search-results-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/search-results-desktop-light.png)

![search-results-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/search-results-phone-dark.png)

![search-results-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/search-results-phone-light.png)

![shop-home-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/shop-home-desktop-dark.png)

![shop-home-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/shop-home-desktop-light.png)

![shop-home-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/shop-home-phone-dark.png)

![shop-home-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/shop-home-phone-light.png)

![tea-note-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/tea-note-desktop-dark.png)

![tea-note-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/tea-note-desktop-light.png)

![tea-note-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/tea-note-phone-dark.png)

![tea-note-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/tea-note-phone-light.png)

![tea-notes-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/tea-notes-desktop-dark.png)

![tea-notes-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/tea-notes-desktop-light.png)

![tea-notes-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/tea-notes-phone-dark.png)

![tea-notes-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/tea-notes-phone-light.png)

![teas-all-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/teas-all-desktop-dark.png)

![teas-all-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/teas-all-desktop-light.png)

![teas-all-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/teas-all-phone-dark.png)

![teas-all-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/teas-all-phone-light.png)

![teas-category-black-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/teas-category-black-desktop-dark.png)

![teas-category-black-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/teas-category-black-desktop-light.png)

![teas-category-black-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/teas-category-black-phone-dark.png)

![teas-category-black-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/teas-category-black-phone-light.png)

![teas-category-herbal-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/teas-category-herbal-desktop-dark.png)

![teas-category-herbal-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/teas-category-herbal-desktop-light.png)

![teas-category-herbal-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/teas-category-herbal-phone-dark.png)

![teas-category-herbal-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/teas-category-herbal-phone-light.png)

![teas-filtered-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/teas-filtered-desktop-dark.png)

![teas-filtered-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/teas-filtered-desktop-light.png)

![teas-filtered-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/teas-filtered-phone-dark.png)

![teas-filtered-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/teas-filtered-phone-light.png)

![teas-filtered-phone-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/teas-filtered-phone-phone-light.png)

![theme-chosen-dark-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/theme-chosen-dark-desktop-dark.png)

![theme-chosen-light-on-dark-device-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/theme-chosen-light-on-dark-device-phone-light.png)

**Summary**

> Phase 7 purchasing and loss tracking: reorder points from usage and lead time, draft purchase orders that only the owner can approve, stock counts, loss trends and profit per tea and per size at landed cost.
> - Reorder levels (`apps/inventory/reorder.py`): daily use over 90 days (orders, blends and samples, not losses; new items measured since first delivery) × (supplier lead time + safety days), never below the item's own level. The suggested quantity covers lead, safety and cover days, less stock and open orders, rounded to a minimum order. Per-item settings, shop defaults in settings. The existing low-stock alert and the item admin now use these levels.
> - Purchase orders: "Draft purchase orders" on the new Reorder page makes one draft per default supplier with the last price paid. Drafts need the owner's approval (a "Save, approve and mark ordered" button or a list action), which records who approved and when and sets the expected date. AI agents can't approve, nothing can be received against a draft, and an approved order gets a "Record a delivery for this order" link.
> - Stock counts (new `apps/purchasing` app): pick the item kinds, enter counted quantities per lot, give a reason for each shortage, then apply. Differences become stock adjustments, all or nothing. Orders packed while counting aren't counted as differences.
> - Reports: "Losses and samples" (12 months at landed cost by reason; samples and giveaways as marketing, personal use separate; the items lost most). "Profit per tea and per size" for any dates: tea at its own lot's landed cost with the tariff part shown, packaging at average landed cost, plus the value of stock on hand.
> - Dashboard: alerts for items to reorder, blends to make, drafts waiting for approval, late deliveries and stock counts left open; `apps.core.attention.register_shortcut()` adds the three new pages to the Shortcuts card. Docs updated in `docs/inventory.md` and `docs/architecture.md`.


### T5 phase3-storefront-design

- **Origin:** Filed by the Tasks Manager from the plan of T1 see-file-teashop-txt, at the user's request
- **Goal:** Planning
- **Ran:** 2026-11-01 18:38 to 2026-11-01 19:15 (35m 27s)
- **Outcome:** done; committed [`11ce69d83be5`](https://github.com/wingware-dev/teashop/commit/11ce69d83be51a2b6083b6675037bc52ea868582) (shared with T9 phase7-purchasing-loss-tracking and T24 pass-label-settings-to-container)
- **Usage:** 2,347 input, 175k output, 26.40M cache read, 318k cache write (claude-haiku-5-5, claude-opus-5-5)
- **Tools:** 207 calls, 76 to Wing's MCP tools (wing-review 57, wing-testing 19)

**Prompt**

> Phase 3: storefront design system and catalog pages
>
> From the report of T1 see-file-teashop-txt (6f896717), section (c) Phase 3 and section '(2) Storefront'. Full report: .TASKS/notes/see-the-file-teashop-txt-for-a-description-of-the-project.md. Design brief from teashop.txt: natural motifs (leaves, flowers, birds, pollinator insects), browns and greens with some primary colours, unique design that reuses no existing branding or trademarks.
>
> Scope (3-5 weeks): brand palette and motifs; light and dark themes that follow the visitor's system setting, with a manual toggle; layouts for category pages (black, oolong, green, flavoured, herbal and so on), region pages, collections (specials, this week's picks, new arrivals), search and filters, product pages (origin, tasting notes, brewing guide, caffeine level, ingredients and allergens, size and price options, the user's own photos), the merch and accessories section, and a tea info and history section; AI-made per-tea page variants within the common theme, which the user approves before they go live. Fast on phones, search-engine friendly (structured product data, sitemap).
>
> Legal requirements from Part 2: WCAG 2.2 AA from the start (New York has the most ADA website lawsuits); no health or disease claims in product copy; 'Herbal tea' or 'tisane' in herbal product names; protected origin names (for example Darjeeling) only for certified product. The logo and key brand marks must be substantially made or modified by a human so they can be protected; AI art is fine for decoration.
>
> Take milestone screenshots into doc/shots using the ui-test-harness.
>
> See \<project>/.TASKS/notes/phase-3-storefront-design-system-and-catalog-pages.md

**Judgement calls**

1. **Moved the home page from core to storefront and deleted core/home.html** (report 1)
   The shop's home is the storefront. Logout now redirects to storefront:home, and base.html no longer links core:home, which fixes the NoReverseMatch reported by T9.
   Alternatives: Keep a core home view that the storefront overrides
2. **Shop stays closed (coming soon) in production until STOREFRONT_OPEN=true** (report 1)
   Going public is the owner's decision, and checkout doesn't exist until phase 4. While closed, the signed-in owner can still try the whole shop on the live server.
   Alternatives: Open the shop as soon as it is deployed
3. **No logo made: the header shows SHOP_NAME as plain text** (report 1)
   The logo and key brand marks must be substantially human-made to be protectable, and the shop name is still undecided. The AI-made motifs are decoration only.
   Alternatives: Draw a placeholder logo mark
4. **Product pages show allergens from every usable lot of the tea** (report 1)
   Any of those lots may be packed for an order, so the page never lists less than a package could contain. The page also says the package label is the definitive list.
   Alternatives: Show only the oldest lot, the one packed next
5. **Default protected origin list: Darjeeling, Nilgiri, Kangra, Assam Orthodox, Longjing, Dragon Well, Uji** (report 1)
   A conservative list of names protected as geographical indications or certification marks. The owner can replace it with CATALOG_PROTECTED_ORIGINS. Plain "Assam" is not on it.
   Alternatives: Leave the list empty until the owner fills it in
6. **Products without photos show decorative motif art plus "Photos of this tea are coming soon"** (report 1)
   AI-made art must never stand in for the actual product.
   Alternatives: Show an empty placeholder box
7. **Seeded the standard categories and collections in a data migration** (report 1)
   The navigation needs sections from day one. The owner can rename or hide them in the admin.
   Alternatives: Seed them only through the demo command
8. **Footer and home page say the teas are weighed and packed by hand when you order** (report 1)
   This matches the owner's stated plan (pack when ordered). Change the copy if that plan changes.
   Alternatives: Leave out any packing claim
9. **Committed 117 full-page milestone screenshots (39 MB)** (report 1)
   The milestone command captures every page at both widths and in both themes, and phone shots are taken at 2x.
   Alternatives: Compress the PNGs or keep a subset
10. **Pillow added at >=13,<14 and the locks rebuilt without --upgrade** (report 1)
   Pillow is needed for product photos. Version 13 follows the Manager's T21 finding about vulnerabilities in 12.x. Rebuilding without --upgrade left every other package pin unchanged. requirements-ui.lock and requirements-ci.lock came out unchanged.

**Findings filed**

- T24 pass-label-settings-to-container: LABEL_PACKER_ADDRESS and the inventory/organic settings never reach the app container

**Screenshots**

![account-security-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/account-security-desktop-dark.png)

![account-security-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/account-security-desktop-light.png)

![account-security-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/account-security-phone-dark.png)

![account-security-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/account-security-phone-light.png)

![collection-this-weeks-picks-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/collection-this-weeks-picks-desktop-dark.png)

![collection-this-weeks-picks-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/collection-this-weeks-picks-desktop-light.png)

![collection-this-weeks-picks-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/collection-this-weeks-picks-phone-dark.png)

![collection-this-weeks-picks-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/collection-this-weeks-picks-phone-light.png)

![coming-soon-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/coming-soon-desktop-dark.png)

![coming-soon-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/coming-soon-desktop-light.png)

![coming-soon-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/coming-soon-phone-dark.png)

![coming-soon-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/coming-soon-phone-light.png)

![login-code-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/login-code-desktop-dark.png)

![login-code-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/login-code-desktop-light.png)

![login-code-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/login-code-phone-dark.png)

![login-code-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/login-code-phone-light.png)

![login-password-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/login-password-desktop-dark.png)

![login-password-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/login-password-desktop-light.png)

![login-password-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/login-password-phone-dark.png)

![login-password-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/login-password-phone-light.png)

![login-wrong-code-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/login-wrong-code-desktop-light.png)

![menu-teas-open-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/menu-teas-open-desktop-light.png)

![merch-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/merch-desktop-dark.png)

![merch-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/merch-desktop-light.png)

![merch-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/merch-phone-dark.png)

![merch-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/merch-phone-light.png)

![merch-product-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/merch-product-desktop-dark.png)

![merch-product-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/merch-product-desktop-light.png)

![merch-product-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/merch-product-phone-dark.png)

![merch-product-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/merch-product-phone-light.png)

![owner-dashboard-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/owner-dashboard-desktop-dark.png)

![owner-dashboard-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/owner-dashboard-desktop-light.png)

![owner-dashboard-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/owner-dashboard-phone-dark.png)

![owner-dashboard-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/owner-dashboard-phone-light.png)

![owner-page-design-preview-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/owner-page-design-preview-desktop-dark.png)

![owner-page-design-preview-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/owner-page-design-preview-desktop-light.png)

![owner-page-design-preview-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/owner-page-design-preview-phone-dark.png)

![owner-page-design-preview-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/owner-page-design-preview-phone-light.png)

![owner-page-designs-after-approve-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/owner-page-designs-after-approve-desktop-light.png)

![owner-page-designs-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/owner-page-designs-desktop-dark.png)

![owner-page-designs-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/owner-page-designs-desktop-light.png)

![owner-page-designs-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/owner-page-designs-phone-dark.png)

![owner-page-designs-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/owner-page-designs-phone-light.png)

![product-allergens-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/product-allergens-desktop-dark.png)

![product-allergens-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/product-allergens-desktop-light.png)

![product-allergens-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/product-allergens-phone-dark.png)

![product-allergens-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/product-allergens-phone-light.png)

![product-design-story-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/product-design-story-phone-light.png)

![product-design-wide-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/product-design-wide-desktop-dark.png)

![product-design-wide-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/product-design-wide-desktop-light.png)

![product-design-wide-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/product-design-wide-phone-dark.png)

![product-design-wide-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/product-design-wide-phone-light.png)

![product-herbal-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/product-herbal-desktop-dark.png)

![product-herbal-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/product-herbal-desktop-light.png)

![product-herbal-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/product-herbal-phone-dark.png)

![product-herbal-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/product-herbal-phone-light.png)

![product-photos-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/product-photos-desktop-dark.png)

![product-photos-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/product-photos-desktop-light.png)

![product-photos-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/product-photos-phone-dark.png)

![product-photos-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/product-photos-phone-light.png)

![purchasing-losses-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/purchasing-losses-desktop-dark.png)

![purchasing-losses-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/purchasing-losses-desktop-light.png)

![purchasing-losses-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/purchasing-losses-phone-dark.png)

![purchasing-losses-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/purchasing-losses-phone-light.png)

![purchasing-profit-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/purchasing-profit-desktop-dark.png)

![purchasing-profit-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/purchasing-profit-desktop-light.png)

![purchasing-profit-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/purchasing-profit-phone-dark.png)

![purchasing-profit-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/purchasing-profit-phone-light.png)

![purchasing-reorder-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/purchasing-reorder-desktop-dark.png)

![purchasing-reorder-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/purchasing-reorder-desktop-light.png)

![purchasing-reorder-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/purchasing-reorder-phone-dark.png)

![purchasing-reorder-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/purchasing-reorder-phone-light.png)

![region-darjeeling-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/region-darjeeling-desktop-dark.png)

![region-darjeeling-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/region-darjeeling-desktop-light.png)

![region-darjeeling-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/region-darjeeling-phone-dark.png)

![region-darjeeling-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/region-darjeeling-phone-light.png)

![regions-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/regions-desktop-dark.png)

![regions-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/regions-desktop-light.png)

![regions-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/regions-phone-dark.png)

![regions-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/regions-phone-light.png)

![search-no-results-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/search-no-results-phone-dark.png)

![search-no-results-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/search-no-results-phone-light.png)

![search-results-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/search-results-desktop-dark.png)

![search-results-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/search-results-desktop-light.png)

![search-results-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/search-results-phone-dark.png)

![search-results-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/search-results-phone-light.png)

![shop-home-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/shop-home-desktop-dark.png)

![shop-home-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/shop-home-desktop-light.png)

![shop-home-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/shop-home-phone-dark.png)

![shop-home-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/shop-home-phone-light.png)

![tea-note-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/tea-note-desktop-dark.png)

![tea-note-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/tea-note-desktop-light.png)

![tea-note-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/tea-note-phone-dark.png)

![tea-note-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/tea-note-phone-light.png)

![tea-notes-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/tea-notes-desktop-dark.png)

![tea-notes-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/tea-notes-desktop-light.png)

![tea-notes-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/tea-notes-phone-dark.png)

![tea-notes-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/tea-notes-phone-light.png)

![teas-all-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/teas-all-desktop-dark.png)

![teas-all-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/teas-all-desktop-light.png)

![teas-all-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/teas-all-phone-dark.png)

![teas-all-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/teas-all-phone-light.png)

![teas-category-black-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/teas-category-black-desktop-dark.png)

![teas-category-black-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/teas-category-black-desktop-light.png)

![teas-category-black-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/teas-category-black-phone-dark.png)

![teas-category-black-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/teas-category-black-phone-light.png)

![teas-category-herbal-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/teas-category-herbal-desktop-dark.png)

![teas-category-herbal-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/teas-category-herbal-desktop-light.png)

![teas-category-herbal-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/teas-category-herbal-phone-dark.png)

![teas-category-herbal-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/teas-category-herbal-phone-light.png)

![teas-filtered-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/teas-filtered-desktop-dark.png)

![teas-filtered-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/teas-filtered-desktop-light.png)

![teas-filtered-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/teas-filtered-phone-dark.png)

![teas-filtered-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/teas-filtered-phone-light.png)

![teas-filtered-phone-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/teas-filtered-phone-phone-light.png)

![theme-chosen-dark-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/theme-chosen-dark-desktop-dark.png)

![theme-chosen-light-on-dark-device-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/theme-chosen-light-on-dark-device-phone-light.png)

**Summary**

> Phase 3 storefront: design system, catalog pages, approved AI page designs, SEO and copy compliance, with milestone screenshots.
> - Design system (static/css/site.css, static/img/motifs.svg, apps/core/design.py): browns and greens with poppy, cornflower, buttercup and plum accents; leaf, sprig, blossom, bee, butterfly, songbird, fern and teapot motifs; light and dark themes that follow the device, plus a Theme button (Automatic, Dark, Light) that is remembered without a flash of the wrong theme. System fonts only. The header shows a plain text wordmark until the owner's human-made logo replaces it.
> - New storefront app with these pages: home, all teas, categories (black, green, oolong, white, dark, flavoured, herbal), regions, collections (specials, this week's picks, new arrivals), search with filters (kind, region, flavour notes, caffeine, package, price, sort), product pages (origin, tasting notes, brewing guide in °F and °C, caffeine meter, ingredients and allergens from the lots being packed, sizes, prices and stock, the owner's photos), merch and accessories, and tea notes articles. Until STOREFRONT_OPEN=true, visitors see "coming soon" and only the signed-in owner sees the shop.
> - Catalog additions: Category, Region, Collection (with dates), FlavourNote, ProductPhoto, plus storefront fields on Product and a package type on SizeOption. A data migration seeds the standard sections. On upload, photos are turned upright, stripped of location and other metadata, and resized to WebP versions for phones. Pillow 13 added; requirements.lock rebuilt.
> - Copy rules (apps/catalog/copy_rules.py), enforced in the admin and flagged on the dashboard: no health or disease claims; "herbal tea" or "tisane" in herbal names; "caffeine-free" only when the caffeine level is None; protected origin names (Darjeeling and others) only on products marked origin-certified.
> - AI page designs: PageVariant picks a palette, motif and layout from the design system plus a headline and story. Agents submit designs with `manage.py submit_page_variant` (audited as the agent). The owner previews each design on the real page and approves, rejects or takes it down. Nothing goes live without approval.
> - SEO: schema.org Product, Breadcrumb, WebSite and Article data; sitemap.xml and robots.txt that keep search engines out while the shop is closed; canonical URLs and descriptions.
> - `load_demo_catalog` command with invented demo data (refused in production). New docs/storefront.md. All 243 tests across purchasing, inventory, catalog, core and storefront pass, including the WCAG 2.2 AA browser checks. 117 milestone screenshots are in doc/shots/2026-11-01-phase3-storefront.


### T17 pin-ui-test-packages

- **Origin:** Filed by the Tasks Manager from the plan of T3 ui-test-harness
- **Goal:** Planning
- **Ran:** 2026-11-01 18:38 to 2026-11-01 18:40 (1m 22s)
- **Outcome:** done; committed [`344e372f8c83`](https://github.com/wingware-dev/teashop/commit/344e372f8c833e9ff92bba60608079f86a0a51f1)
- **Usage:** 38 input, 6,297 output, 548k cache read, 30k cache write (claude-opus-5-5)
- **Tools:** 17 calls, 4 to Wing's MCP tools (wing-review 4)

**Prompt**

> Pin the browser-test packages with hashes
>
> Follow-up from T3 ui-test-harness (0223cfbe). Add playwright and axe-playwright-python to a hashed lock (for example a requirements-ui.lock built with uv), so CI installs them with --require-hashes like the runtime packages in requirements.lock.
>
> See \<project>/.TASKS/notes/pin-the-browser-test-packages-with-hashes.md

**Judgement calls**

1. **Compiled the UI lock with requirements.lock as a constraint (-c)**
   Any package the two locks share stays at the same version, so CI can install both in one pip --require-hashes call without conflicts. Right now they share no packages.
   Alternatives: One combined dev lock built from requirements-dev.txt; Compile the UI lock on its own with no constraint
2. **Changed the README's local setup to install from requirements-ui.lock with --require-hashes**
   Local runs then use the same pinned versions as CI. The lock includes hashes for the macOS wheels too, and I checked that it installs locally.

**Summary**

> Pinned the browser-test packages with hashes in a new requirements-ui.lock, which CI now installs with --require-hashes and checks with pip-audit.
> - New `requirements-ui.lock` (built with `uv pip compile requirements-ui.txt -c requirements.lock --generate-hashes`): playwright 1.64.1, axe-playwright-python 0.1.8, greenlet, pyee, typing-extensions, with hashes for every platform's wheels.
> - `ci.yml`: installs both locks in one `--require-hashes` pip call (replacing the unhashed `pip install -r requirements-ui.txt`), adds the new lock to the pip cache key, and runs pip-audit on both locks.
> - README, docs/ops/README.md (upgrade commands), requirements-ui.txt and dependabot.yml comments now mention the new lock.


### T20 pin-pip-audit-ci

- **Origin:** Filed by the Tasks Manager from the plan of T17 pin-ui-test-packages
- **Goal:** Planning
- **Ran:** 2026-11-01 18:40 to 2026-11-01 18:41 (1m 22s)
- **Outcome:** done; committed [`da14a53eb443`](https://github.com/wingware-dev/teashop/commit/da14a53eb443871b2c849f243c52558b72a2b5d5)
- **Usage:** 1,634 input, 6,387 output, 647k cache read, 11k cache write (claude-haiku-5-5, claude-opus-5-5)
- **Tools:** 12 calls, 4 to Wing's MCP tools (wing-review 4)

**Prompt**

> Pin pip-audit with hashes in CI
>
> Follow-up from T17 pin-ui-test-packages (a454368b). CI still runs a plain `pip install pip-audit`, with no version or hashes. Add it to a hashed lock (for example a requirements-ci.lock) to close the last unhashed install in the CI job.

**Judgement calls**

1. **Made a separate requirements-ci.txt/.lock rather than adding pip-audit to requirements-ui.lock**
   pip-audit isn't a browser-test package, and the task suggested a separate CI lock. requirements-dev.txt now pulls it in with -r, so pip-audit is listed in one place only.
   Alternatives: Add pip-audit to requirements-ui.txt and its lock
2. **Left pip itself in the lock (uv includes it as pip-api's dependency)**
   Every package stays hashed, including pip. The cost is that CI upgrades pip to the locked version during the install.
   Alternatives: Leave pip out with --no-emit-package pip and rely on the pip that setup-python provides
3. **Compiled against the working-copy requirements.lock, which includes another task's uncommitted Pillow addition**
   That is the lock that will be committed. Pillow isn't in the CI lock, and the only shared package, certifi, is the same version either way, so requirements-ci.lock is valid with or without that change.

**Findings filed**

- T21 pillow-vulnerable-pin: Pillow pin <13 locks a version with known vulnerabilities; CI pip-audit will fail

**Summary**

> CI now installs pip-audit from a hashed lock instead of an unpinned `pip install pip-audit`, so every package CI installs is hash-checked.
> - New `requirements-ci.txt` (pip-audit>=2.7,<3) and `requirements-ci.lock` (pip-audit 2.10.1 and its dependencies, including pip, with hashes), compiled with requirements.lock and requirements-ui.lock as constraints.
> - `ci.yml`: one `--require-hashes` install of all three locks, the new lock added to the pip cache key, and pip-audit checks it too.
> - `requirements-dev.txt` now includes requirements-ci.txt instead of listing pip-audit itself; docs/ops/README.md gives the rebuild command and order, and the dependabot.yml comment names the new lock.


### T24 pass-label-settings-to-container

- **Origin:** Found by T5 phase3-storefront-design
- **Goal:** Planning
- **Ran:** 2026-11-01 19:05 to 2026-11-01 19:15 (3m 01s)
- **Outcome:** done; committed [`11ce69d83be5`](https://github.com/wingware-dev/teashop/commit/11ce69d83be51a2b6083b6675037bc52ea868582) (shared with T9 phase7-purchasing-loss-tracking and T5 phase3-storefront-design)
- **Usage:** 2,013 input, 5,756 output, 299k cache read, 26k cache write (claude-haiku-5-5, claude-opus-5-5)
- **Tools:** 11 calls, 2 to Wing's MCP tools (wing-review 1, wing-testing 1)

**Prompt**

> LABEL_PACKER_ADDRESS and the inventory/organic settings never reach the app container
>
> .env.example tells the owner to set LABEL_PACKER_ADDRESS (the packer's name and address required on every package label), but compose.yaml's web service lists its environment variables explicitly and does not pass LABEL_PACKER_ADDRESS (nor INVENTORY_BEST_BY_WARNING_DAYS, ORGANIC_EXEMPTION_LIMIT, ORGANIC_SALES_ALERT). On the server the setting is always empty, so every label gets the problem "The packer's name and address (LABEL_PACKER_ADDRESS) is not set" and can't be printed legally. Fix: add `LABEL_PACKER_ADDRESS: ${LABEL_PACKER_ADDRESS:-}` (and the others with their defaults) to the web service's environment, and a test in apps/core/tests/test_deploy_scripts.py that every variable in .env.example meant for Django appears in compose.yaml.
>
> Evidence: .env.example line 26 (LABEL_PACKER_ADDRESS=); compose.yaml web service `environment:` block (around lines 47-62) has no LABEL_PACKER_ADDRESS; config/settings.py reads it with env_str("LABEL_PACKER_ADDRESS"); apps/catalog/services.py label_data() adds the problem when it is empty.
>
> Suggested next step: fix

**Judgement calls**

1. **Listed the three tuning settings in .env.example, commented out**
   The task only asked to pass them through compose. Listing them lets the owner find them, and puts them under the new test's check.
   Alternatives: Leave .env.example unchanged
2. **The test reads compose.yaml as plain text instead of parsing it as YAML**
   PyYAML is not installed in the project environment. The web service's environment block has a simple, fixed indentation.

**Screenshots**

![account-security-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/account-security-desktop-dark.png)

![account-security-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/account-security-desktop-light.png)

![account-security-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/account-security-phone-dark.png)

![account-security-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/account-security-phone-light.png)

![collection-this-weeks-picks-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/collection-this-weeks-picks-desktop-dark.png)

![collection-this-weeks-picks-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/collection-this-weeks-picks-desktop-light.png)

![collection-this-weeks-picks-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/collection-this-weeks-picks-phone-dark.png)

![collection-this-weeks-picks-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/collection-this-weeks-picks-phone-light.png)

![coming-soon-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/coming-soon-desktop-dark.png)

![coming-soon-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/coming-soon-desktop-light.png)

![coming-soon-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/coming-soon-phone-dark.png)

![coming-soon-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/coming-soon-phone-light.png)

![login-code-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/login-code-desktop-dark.png)

![login-code-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/login-code-desktop-light.png)

![login-code-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/login-code-phone-dark.png)

![login-code-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/login-code-phone-light.png)

![login-password-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/login-password-desktop-dark.png)

![login-password-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/login-password-desktop-light.png)

![login-password-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/login-password-phone-dark.png)

![login-password-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/login-password-phone-light.png)

![login-wrong-code-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/login-wrong-code-desktop-light.png)

![menu-teas-open-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/menu-teas-open-desktop-light.png)

![merch-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/merch-desktop-dark.png)

![merch-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/merch-desktop-light.png)

![merch-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/merch-phone-dark.png)

![merch-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/merch-phone-light.png)

![merch-product-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/merch-product-desktop-dark.png)

![merch-product-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/merch-product-desktop-light.png)

![merch-product-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/merch-product-phone-dark.png)

![merch-product-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/merch-product-phone-light.png)

![owner-dashboard-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/owner-dashboard-desktop-dark.png)

![owner-dashboard-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/owner-dashboard-desktop-light.png)

![owner-dashboard-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/owner-dashboard-phone-dark.png)

![owner-dashboard-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/owner-dashboard-phone-light.png)

![owner-page-design-preview-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/owner-page-design-preview-desktop-dark.png)

![owner-page-design-preview-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/owner-page-design-preview-desktop-light.png)

![owner-page-design-preview-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/owner-page-design-preview-phone-dark.png)

![owner-page-design-preview-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/owner-page-design-preview-phone-light.png)

![owner-page-designs-after-approve-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/owner-page-designs-after-approve-desktop-light.png)

![owner-page-designs-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/owner-page-designs-desktop-dark.png)

![owner-page-designs-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/owner-page-designs-desktop-light.png)

![owner-page-designs-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/owner-page-designs-phone-dark.png)

![owner-page-designs-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/owner-page-designs-phone-light.png)

![product-allergens-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/product-allergens-desktop-dark.png)

![product-allergens-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/product-allergens-desktop-light.png)

![product-allergens-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/product-allergens-phone-dark.png)

![product-allergens-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/product-allergens-phone-light.png)

![product-design-story-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/product-design-story-phone-light.png)

![product-design-wide-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/product-design-wide-desktop-dark.png)

![product-design-wide-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/product-design-wide-desktop-light.png)

![product-design-wide-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/product-design-wide-phone-dark.png)

![product-design-wide-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/product-design-wide-phone-light.png)

![product-herbal-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/product-herbal-desktop-dark.png)

![product-herbal-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/product-herbal-desktop-light.png)

![product-herbal-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/product-herbal-phone-dark.png)

![product-herbal-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/product-herbal-phone-light.png)

![product-photos-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/product-photos-desktop-dark.png)

![product-photos-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/product-photos-desktop-light.png)

![product-photos-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/product-photos-phone-dark.png)

![product-photos-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/product-photos-phone-light.png)

![purchasing-losses-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/purchasing-losses-desktop-dark.png)

![purchasing-losses-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/purchasing-losses-desktop-light.png)

![purchasing-losses-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/purchasing-losses-phone-dark.png)

![purchasing-losses-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/purchasing-losses-phone-light.png)

![purchasing-profit-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/purchasing-profit-desktop-dark.png)

![purchasing-profit-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/purchasing-profit-desktop-light.png)

![purchasing-profit-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/purchasing-profit-phone-dark.png)

![purchasing-profit-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/purchasing-profit-phone-light.png)

![purchasing-reorder-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/purchasing-reorder-desktop-dark.png)

![purchasing-reorder-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/purchasing-reorder-desktop-light.png)

![purchasing-reorder-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/purchasing-reorder-phone-dark.png)

![purchasing-reorder-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/purchasing-reorder-phone-light.png)

![region-darjeeling-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/region-darjeeling-desktop-dark.png)

![region-darjeeling-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/region-darjeeling-desktop-light.png)

![region-darjeeling-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/region-darjeeling-phone-dark.png)

![region-darjeeling-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/region-darjeeling-phone-light.png)

![regions-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/regions-desktop-dark.png)

![regions-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/regions-desktop-light.png)

![regions-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/regions-phone-dark.png)

![regions-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/regions-phone-light.png)

![search-no-results-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/search-no-results-phone-dark.png)

![search-no-results-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/search-no-results-phone-light.png)

![search-results-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/search-results-desktop-dark.png)

![search-results-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/search-results-desktop-light.png)

![search-results-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/search-results-phone-dark.png)

![search-results-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/search-results-phone-light.png)

![shop-home-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/shop-home-desktop-dark.png)

![shop-home-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/shop-home-desktop-light.png)

![shop-home-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/shop-home-phone-dark.png)

![shop-home-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/shop-home-phone-light.png)

![tea-note-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/tea-note-desktop-dark.png)

![tea-note-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/tea-note-desktop-light.png)

![tea-note-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/tea-note-phone-dark.png)

![tea-note-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/tea-note-phone-light.png)

![tea-notes-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/tea-notes-desktop-dark.png)

![tea-notes-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/tea-notes-desktop-light.png)

![tea-notes-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/tea-notes-phone-dark.png)

![tea-notes-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/tea-notes-phone-light.png)

![teas-all-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/teas-all-desktop-dark.png)

![teas-all-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/teas-all-desktop-light.png)

![teas-all-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/teas-all-phone-dark.png)

![teas-all-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/teas-all-phone-light.png)

![teas-category-black-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/teas-category-black-desktop-dark.png)

![teas-category-black-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/teas-category-black-desktop-light.png)

![teas-category-black-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/teas-category-black-phone-dark.png)

![teas-category-black-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/teas-category-black-phone-light.png)

![teas-category-herbal-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/teas-category-herbal-desktop-dark.png)

![teas-category-herbal-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/teas-category-herbal-desktop-light.png)

![teas-category-herbal-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/teas-category-herbal-phone-dark.png)

![teas-category-herbal-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/teas-category-herbal-phone-light.png)

![teas-filtered-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/teas-filtered-desktop-dark.png)

![teas-filtered-desktop-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/teas-filtered-desktop-light.png)

![teas-filtered-phone-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/teas-filtered-phone-dark.png)

![teas-filtered-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/teas-filtered-phone-light.png)

![teas-filtered-phone-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/teas-filtered-phone-phone-light.png)

![theme-chosen-dark-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/theme-chosen-dark-desktop-dark.png)

![theme-chosen-light-on-dark-device-phone-light.png](https://github.com/wingware-dev/teashop/raw/11ce69d83be51a2b6083b6675037bc52ea868582/doc/shots/2026-11-01-phase3-storefront/theme-chosen-light-on-dark-device-phone-light.png)

**Summary**

> The web container now receives the label and inventory/organic settings from .env, and a new test fails if a Django setting from .env.example is not passed through compose.yaml.
> - compose.yaml: the web service now gets LABEL_PACKER_ADDRESS (default empty), INVENTORY_BEST_BY_WARNING_DAYS (60), ORGANIC_EXEMPTION_LIMIT (5000) and ORGANIC_SALES_ALERT (4000). The defaults match config/settings.py.
> - .env.example: the three tuning settings are listed, commented out with their defaults, so the owner can find them.
> - apps/core/tests/test_deploy_scripts.py: new ComposeEnvironmentTests. One test checks that every .env.example variable read by config/settings.py is in the web service's environment. The other checks that every .env.example variable is used somewhere in compose.yaml.


### T21 pillow-vulnerable-pin

- **Origin:** Found by T20 pin-pip-audit-ci
- **Goal:** Bug Fixes
- **Ran:**  to 2026-11-01 19:14 ()
- **Outcome:** obsolete
- **Usage:** not recorded
- **Tools:** not recorded (no transcript)

**Prompt**

> Pillow pin <13 locks a version with known vulnerabilities; CI pip-audit will fail
>
> The uncommitted change to requirements.txt (adding Pillow for product photos) pins `Pillow>=12,<13`, and requirements.lock resolves it to pillow 12.3.0. pip-audit reports three vulnerabilities in that version, all fixed in 13.0.0, so CI's `pip-audit --strict` step will fail once this lands. Fix: allow Pillow 13 (for example `Pillow>=13,<14`, after checking that the photo code works with it), then rebuild requirements.lock, requirements-ui.lock and requirements-ci.lock in that order, using the commands in docs/ops/README.md.
>
> Evidence: `pip-audit --strict --no-deps --disable-pip -r requirements.lock` prints: pillow 12.3.0 CVE-2026-96640 (fix 13.0.0), CVE-2026-96778 (fix 13.0.0), GHSA-78g4-xqwv-q3g8 (fix 13.0.0). Source: requirements.txt, line "Pillow>=12,<13" (uncommitted working-copy change, made by another task).
>
> Suggested next step: fix


### T6 phase4-cart-checkout

- **Origin:** Filed by the Tasks Manager from the plan of T1 see-file-teashop-txt, at the user's request
- **Goal:** Planning
- **Ran:** 2026-11-01 19:15 to 2026-11-01 19:50 (34m 01s)
- **Outcome:** done; committed [`776b8825b26c`](https://github.com/wingware-dev/teashop/commit/776b8825b26c68e7fbb2cb0de2f1f04613623254)
- **Usage:** 2,748 input, 206k output, 27.76M cache read, 345k cache write (claude-haiku-5-5, claude-opus-5-5)
- **Tools:** 211 calls, 101 to Wing's MCP tools (wing-review 95, wing-testing 6)

**Prompt**

> Phase 4: cart and checkout
>
> From the report of T1 see-file-teashop-txt (6f896717), section (c) Phase 4 and section '(2) Storefront'. Full report: .TASKS/notes/see-the-file-teashop-txt-for-a-description-of-the-project.md
>
> Scope (2-3 weeks): cart; guest checkout plus optional customer accounts with order history and 'buy again' (the user's choice); Stripe Payment Element or Checkout (cards, Apple Pay, Google Pay and more); live USPS rates through EasyPost or Shippo, shipping to the 48 contiguous states only; address checking; discount codes; a free-shipping threshold (amount TBD by the user); order emails (confirmation, shipped with tracking); policy pages (privacy listing every service that receives customer data, including the AI provider; terms; returns; shipping; accessibility); bot and fraud protection; vacation mode.
>
> Sales tax (Part 2): tea is exempt in NY; merch and accessories are taxed at the NY destination rate; on mixed orders shipping is split in proportion and only the taxable share is taxed (check whether Stripe Tax does this, or compute it); sales tracked per state against economic-nexus thresholds.
>
> Subscriptions are in the MVP (the user's answer) and must follow NY GBL 527-a and California's auto-renewal law: renewal terms next to the sign-up button, an explicit consent checkbox, an acknowledgment email, renewal reminders, and one-click online cancellation. Prices are the same for everyone, never personalised.
>
> Use Stripe and EasyPost or Shippo test modes only; no live accounts without the user's approval. Screenshots into doc/shots; WCAG 2.2 AA checks.
>
> [Tasks Manager, 2026-11-01 18:19] From T2 phase1-infrastructure-skeleton (edd0e993)'s follow-ups: add a Content-Security-Policy header, using django-csp since the project stays on Django 5.2 LTS. Cover the storefront's assets, and allow Stripe's script and frame domains.
>
> [Tasks Manager, 2026-11-01 19:15] From T5 phase3-storefront-design (ea7f0526):
> - Product pages show sizes and prices, with an 'Online ordering opens soon' notice in the buy box (apps/storefront/templates/storefront/product.html). Replace that notice with the add-to-cart form.
> - The pages now have no inline scripts or styles except the JSON-LD data, so a strict CSP (in the Caddyfile or with django-csp) is straightforward.
> - The shop stays closed until STOREFRONT_OPEN=true.
> - See docs/storefront.md.
> No Stripe or EasyPost/Shippo account exists yet, and none may be created. Build against their documented APIs with stand-ins (mocked clients or stripe-mock) in tests, behind settings that take test keys later.
>
> See \<project>/.TASKS/notes/phase-4-cart-and-checkout.md

**Judgement calls**

1. **Shop computes the tax split itself; rates from an owner-entered ZIP table by default, Stripe Tax optional**
   I could not check online whether Stripe Tax splits mixed-order shipping the way the plan requires, so the split is always computed in apps/checkout/tax.py. Stripe Tax (TAX_PROVIDER=stripe) only supplies the rate.
   Alternatives: Rely on Stripe Tax entirely; Use a single NY rate table only
2. **A NY ZIP with no entered rate is charged the highest NY rate (8.875%) and flagged on the dashboard**
   Under-collecting is the shop's liability. Over-collected tax must be sent to the state, and the dashboard prompts the owner to add the ZIP's rate.
   Alternatives: Refuse checkout for that ZIP; Charge the 4% state rate only
3. **Customer accounts sign in by an emailed one-time link, with no passwords**
   There are no customer passwords to store or leak (SHIELD Act). An account is just a proven email, so guest orders placed with that email show up after signing in.
   Alternatives: Django User accounts with passwords
4. **Returns policy: no returns of tea (food); merch within 30 days; damaged or lost items replaced or refunded**
   A common food-retail policy. It is the owner's call; docs/checkout.md says to change it, and all policies need a lawyer's read.
   Alternatives: A satisfaction guarantee on tea too
5. **Subscriptions: tea only, shipping included in the price, renewal reminders only for yearly terms, no free trials**
   Tea-only means no sales tax on subscriptions. The law requires the 15-45 day reminder for terms of a year or more; no trials means no trial-end notice is needed.
   Alternatives: Reminders before every renewal
6. **Cancelling a Stripe subscription stops renewals at the end of the period already paid for**
   Stops all future charges at once, and the delivery already paid for still ships.
   Alternatives: Cancel immediately with a prorated refund
7. **Added SizeOption.shipping_grams to the catalog (optional), with the weight estimated from the tea and its package when empty**
   Rates need parcel weight, and merchandise had no weight field.
   Alternatives: A separate weight model in checkout
8. **Live Stripe and EasyPost keys are refused unless STRIPE_ALLOW_LIVE or EASYPOST_ALLOW_LIVE is set**
   Going live has to be the owner's deliberate step, as the task requires.
   Alternatives: No guard
9. **Policy pages are reachable even while the shop is closed; the subscription cancel page needs no sign-in**
   The law requires one-step online cancellation, and the legal pages must always be reachable.
10. **Strict CSP has no 'unsafe-inline' for styles, including Stripe's**
   Pages have no inline styles. Not verifiable against live Stripe.js without keys; docs say to check the browser console and offer CSP_REPORT_URI.
   Alternatives: Allow style-src 'unsafe-inline' up front

**Screenshots**

![account-confirm-sign-in-phone-light.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/account-confirm-sign-in-phone-light.png)

![account-home-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/account-home-desktop-dark.png)

![account-home-phone-light.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/account-home-phone-light.png)

![account-link-sent-phone-light.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/account-link-sent-phone-light.png)

![account-sign-in-phone-light.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/account-sign-in-phone-light.png)

![checkout-1-cart-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/checkout-1-cart-desktop-dark.png)

![checkout-1-cart-phone-light.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/checkout-1-cart-phone-light.png)

![checkout-2-address-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/checkout-2-address-desktop-dark.png)

![checkout-2-address-errors-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/checkout-2-address-errors-desktop-dark.png)

![checkout-2-address-errors-phone-light.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/checkout-2-address-errors-phone-light.png)

![checkout-2-address-phone-light.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/checkout-2-address-phone-light.png)

![checkout-3-shipping-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/checkout-3-shipping-desktop-dark.png)

![checkout-3-shipping-phone-light.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/checkout-3-shipping-phone-light.png)

![checkout-4-pay-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/checkout-4-pay-desktop-dark.png)

![checkout-4-pay-phone-light.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/checkout-4-pay-phone-light.png)

![checkout-5-done-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/checkout-5-done-desktop-dark.png)

![checkout-5-done-phone-light.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/checkout-5-done-phone-light.png)

![checkout-address-not-shipped-desktop-light.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/checkout-address-not-shipped-desktop-light.png)

![checkout-cart-empty-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/checkout-cart-empty-desktop-dark.png)

![checkout-cart-empty-desktop-light.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/checkout-cart-empty-desktop-light.png)

![checkout-cart-empty-phone-dark.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/checkout-cart-empty-phone-dark.png)

![checkout-cart-empty-phone-light.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/checkout-cart-empty-phone-light.png)

![owner-sales-by-state-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/owner-sales-by-state-desktop-dark.png)

![owner-sales-by-state-desktop-light.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/owner-sales-by-state-desktop-light.png)

![owner-sales-by-state-phone-dark.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/owner-sales-by-state-phone-dark.png)

![owner-sales-by-state-phone-light.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/owner-sales-by-state-phone-light.png)

![policy-accessibility-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/policy-accessibility-desktop-dark.png)

![policy-accessibility-desktop-light.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/policy-accessibility-desktop-light.png)

![policy-accessibility-phone-dark.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/policy-accessibility-phone-dark.png)

![policy-accessibility-phone-light.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/policy-accessibility-phone-light.png)

![policy-privacy-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/policy-privacy-desktop-dark.png)

![policy-privacy-desktop-light.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/policy-privacy-desktop-light.png)

![policy-privacy-phone-dark.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/policy-privacy-phone-dark.png)

![policy-privacy-phone-light.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/policy-privacy-phone-light.png)

![policy-returns-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/policy-returns-desktop-dark.png)

![policy-returns-desktop-light.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/policy-returns-desktop-light.png)

![policy-returns-phone-dark.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/policy-returns-phone-dark.png)

![policy-returns-phone-light.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/policy-returns-phone-light.png)

![policy-shipping-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/policy-shipping-desktop-dark.png)

![policy-shipping-desktop-light.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/policy-shipping-desktop-light.png)

![policy-shipping-phone-dark.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/policy-shipping-phone-dark.png)

![policy-shipping-phone-light.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/policy-shipping-phone-light.png)

![policy-subscriptions-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/policy-subscriptions-desktop-dark.png)

![policy-subscriptions-desktop-light.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/policy-subscriptions-desktop-light.png)

![policy-subscriptions-phone-dark.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/policy-subscriptions-phone-dark.png)

![policy-subscriptions-phone-light.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/policy-subscriptions-phone-light.png)

![policy-terms-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/policy-terms-desktop-dark.png)

![policy-terms-desktop-light.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/policy-terms-desktop-light.png)

![policy-terms-phone-dark.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/policy-terms-phone-dark.png)

![policy-terms-phone-light.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/policy-terms-phone-light.png)

![product-buy-box-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/product-buy-box-desktop-dark.png)

![product-buy-box-phone-light.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/product-buy-box-phone-light.png)

![subscription-cancel-phone-dark.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/subscription-cancel-phone-dark.png)

![subscription-cancelled-phone-dark.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/subscription-cancelled-phone-dark.png)

![subscription-no-consent-phone-dark.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/subscription-no-consent-phone-dark.png)

![subscription-pay-phone-dark.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/subscription-pay-phone-dark.png)

![subscription-plans-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/subscription-plans-desktop-dark.png)

![subscription-plans-desktop-light.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/subscription-plans-desktop-light.png)

![subscription-plans-phone-dark.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/subscription-plans-phone-dark.png)

![subscription-plans-phone-light.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/subscription-plans-phone-light.png)

![subscription-sign-up-phone-dark.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/subscription-sign-up-phone-dark.png)

![subscription-welcome-phone-dark.png](https://github.com/wingware-dev/teashop/raw/776b8825b26c68e7fbb2cb0de2f1f04613623254/doc/shots/2026-11-01-phase4-checkout/subscription-welcome-phone-dark.png)

**Summary**

> Phase 4 cart and checkout: a new `apps/checkout` app, policy pages and a Content-Security-Policy.
> - Cart; guest checkout with optional accounts (sign in by an emailed link, order history, "Buy again"); add-to-cart form on product pages.
> - Stripe Payment Element (cards, Apple Pay, Google Pay, Link) with a webhook. EasyPost USPS rates and address checking, 48 contiguous states and DC only. Test keys only: live keys are refused unless explicitly allowed. Stand-ins for laptops and tests.
> - New York sales tax: tea exempt, merch taxed at the destination rate, shipping split in proportion on mixed orders. Sales per state tracked against nexus thresholds, with dashboard alerts and a sales-by-state page.
> - Discount codes, a free-shipping threshold (off until set), vacation mode, promised ship dates (Mail Order Rule).
> - Emails: confirmation, shipped with tracking, owner notice. Subscriptions follow NY GBL 527-a and California's law: terms next to the button, consent box, acknowledgment email, daily renewal-reminder job, one-step cancel.
> - Policy pages (privacy lists every service that gets customer data, including Anthropic; terms; returns; shipping; subscriptions; accessibility). django-csp policy allowing Stripe and Turnstile. Honeypot, timing check, rate limit, optional Turnstile.
> - docs/checkout.md; 62 milestone screenshots in doc/shots/2026-11-01-phase4-checkout.


### T26 shrink-milestone-screenshots

- **Origin:** Filed by the Tasks Manager from the plan of T5 phase3-storefront-design
- **Goal:** Planning
- **Ran:** 2026-11-01 19:15 to 2026-11-01 19:20 (4m 34s)
- **Outcome:** done; committed [`da7c1baf5f61`](https://github.com/wingware-dev/teashop/commit/da7c1baf5f61c113e586a5fffb6e144a1f5a54ee)
- **Usage:** 1,740 input, 15k output, 1.71M cache read, 54k cache write (claude-haiku-5-5, claude-opus-5-5)
- **Tools:** 37 calls, 9 to Wing's MCP tools (wing-review 6, wing-analysis 2, wing-testing 1)

**Prompt**

> Shrink milestone screenshots
>
> Follow-up from T5 phase3-storefront-design (ea7f0526). The phase 3 milestone added 117 full-page PNGs (39 MB) to the repository, and every milestone adds more. Add lossless PNG optimisation (for example oxipng) to `manage.py milestone_shots`, and/or take phone shots at 1x, so doc/shots stays small. Optimise the existing doc/shots milestones too.

**Messages from the Tasks Manager**

- 2026-11-01 19:20: , which arrived as you finished: From the Manager: as you pointed out, committing recompressed copies of the existing screenshots adds about 27 MB to git history to save 12 MB in the checkout, which is a net loss. My task text asked for it, and that was a mistake. Please restore the existing PNGs under doc/shots/2026-11-01-phase1-skeleton/ and doc/shots/2026-11-01-phase3-storefront/ to their committed versions (`git checkout -- <those two directories>`). Keep everything else: 1x shots, the oxipng step in milestone_shots, pyoxipng in the requirements and lock, the README and the test. Adjust doc/shots/README.md if it says the old milestones were recompressed, then report done again. Carry on with the task if this changes anything, and end with task_report again.

**Judgement calls**

1. **Everyday var/shots also use 1x, not only milestones** (report 1)
   Everyday shots and milestone shots stay the same, and the code stays simpler. The 1x phone render is still crisp (I looked at account-security-phone-light).
   Alternatives: Use 1x only when recording a milestone; Set device_scale_factor=1 for phones, which would also change how the page renders
2. **Left the existing phone shots at 2x and only compressed them losslessly** (report 1)
   Downscaling them would lose detail from the historical record, and the task asked to optimise them. The README notes that the phase 1 and phase 3 phone shots are 780 wide.
   Alternatives: Downscale the existing phone shots to 390 wide for about 4x more savings
3. **oxipng level 2 rather than higher** (report 1)
   On sample shots, level 3 gave the same bytes as level 2 and took 40% longer, and level 4 was about 3x slower. Level 2 takes about 2 s per large shot.
   Alternatives: Level 4 or higher
4. **Committed the recompressed copies of the existing shots** (report 1)
   The task asked for it, and it shrinks the checkout by 12 MB. But git keeps the old blobs, so the repository's history grows by about 27 MB with this commit. Only rewriting history would avoid that.
   Alternatives: Leave the existing milestones unchanged, so history doesn't grow and only future milestones get smaller

**Summary**

> Milestone screenshots are now smaller: phone shots are taken at 1x and `manage.py milestone_shots` compresses its PNGs losslessly with oxipng.
> - `apps/core/uitesting.py`: screenshots use `scale="css"`, so phone shots are 390 px wide, a quarter of the pixels. The phone still renders at 2x.
> - `milestone_shots`: compresses the shots with oxipng (pyoxipng, level 2, safe metadata strip) once the tests pass, and reports the size and the bytes saved. It stops early with an install hint if pyoxipng is missing.
> - Added `pyoxipng` to `requirements-ui.txt` and rebuilt `requirements-ui.lock` with hashes. Only pyoxipng was added; no other pins changed.
> - Left the existing phase 1 and phase 3 milestone shots as committed, as the Tasks Manager asked: rewriting them would add about 27 MB to git history to save 12 MB in the checkout. `doc/shots/README.md` says so.
> - Added a test that the command compresses its shots.


### T33 regression-tests-after-checkout

- **Origin:** Filed by the Tasks Manager
- **Goal:** Planning
- **Ran:** 2026-11-01 19:50 to 2026-11-01 19:54 (4m 34s)
- **Outcome:** done
- **Usage:** 1,783 input, 5,200 output, 332k cache read, 30k cache write (claude-haiku-5-5, claude-opus-5-5)
- **Tools:** 12 calls, 9 to Wing's MCP tools (wing-review 5, wing-testing 4)

**Prompt**

> Regression tests after the checkout phase
>
> T6 phase4-cart-checkout (e36d1a1d) changed the shared page header and footer (templates/base.html), static/css/site.css, added CSP middleware and a global context processor, and added a catalog migration. T26 shrink-milestone-screenshots (f0abe49a) changed the screenshot harness. This is a sweep under wing_guide topic 'research': one test_run of the whole 'apps' directory, including every app's browser and WCAG tests. File each failure with report_finding (next_step fix); don't fix anything.
>
> See \<project>/.TASKS/notes/regression-tests-after-the-checkout-phase.md

**Verdict:** Check found issues; filed T35 checkout-deploy-checks-break-settings and T34 compose-checkout-env-vars

- T35 checkout-deploy-checks-break-settings: New checkout deploy checks make test_deploy_checks_pass fail (check --deploy --fail-level WARNING)
- T34 compose-checkout-env-vars: compose.yaml web service doesn't pass the 26 checkout variables added to .env.example

**Summary**

> Ran the whole `apps` directory once, including browser and WCAG tests: 382 tests, 378 passed, 3 failed, 1 skipped. The 3 failures come from 2 causes, each filed as a fix finding:
> - T34 compose-checkout-env-vars (9ce5f1b2): compose.yaml's web service is missing the 26 checkout variables added to .env.example. Two ComposeEnvironmentTests fail.
> - T35 checkout-deploy-checks-break-settings (d3a888ce): the new checkout deploy warnings checkout.W001–W006 fail ProductionSettingsTests.test_deploy_checks_pass, whose PRODUCTION_ENV sets no checkout settings.
> Nothing was fixed in place.


### T34 compose-checkout-env-vars

- **Origin:** Found by T33 regression-tests-after-checkout
- **Goal:** Planning
- **Ran:** 2026-11-01 19:55 to 2026-11-01 19:58 (0m 58s)
- **Outcome:** done; committed [`81616b891cb5`](https://github.com/wingware-dev/teashop/commit/81616b891cb5c8406a0727255689181bd756678e) (shared with T35 checkout-deploy-checks-break-settings)
- **Usage:** 18 input, 4,896 output, 248k cache read, 25k cache write (claude-opus-5-5)
- **Tools:** 9 calls, 3 to Wing's MCP tools (wing-review 2, wing-testing 1)

**Prompt**

> compose.yaml web service doesn't pass the 26 checkout variables added to .env.example
>
> Task T6 phase4-cart-checkout (e36d1a1d) added 26 settings to .env.example and config/settings.py (Stripe, EasyPost, SHIP_FROM_*, email, tax, Turnstile, CSP report URI, site/shop identity), but compose.yaml's `web` service `environment:` block was not updated. So an owner who sets these in .env would never see them reach the Django container in production, and checkout would stay closed. Fix: add each one to the web service's environment block in compose.yaml as `NAME: ${NAME:-}` (or whatever form the existing entries there use, e.g. LABEL_PACKER_ADDRESS). Also add them to any other service that runs Django, such as a worker or cron service that sends emails (check for send_subscription_reminders scheduling). Found by the regression sweep task T33 regression-tests-after-checkout (84d15c13).
>
> Evidence: Failing, in a full `test_run` of `apps` (both are pure file parsing, so they don't depend on the order tests run in):
> - apps/core/tests/test_deploy_scripts.py::ComposeEnvironmentTests.test_django_settings_in_env_example_reach_web_container (line 185: `self.assertEqual(sorted(for_django - web_environment()), [])`)
> - apps/core/tests/test_deploy_scripts.py::ComposeEnvironmentTests.test_every_env_example_variable_is_used_by_compose (line 190: `self.assertEqual(unused, [])`)
>
> Both list the same 26 missing names:
> CSP_REPORT_URI, DEFAULT_FROM_EMAIL, EASYPOST_API_KEY, EMAIL_HOST, EMAIL_HOST_PASSWORD, EMAIL_HOST_USER, EMAIL_PORT, OWNER_NOTIFY_EMAIL, SALES_TAX_STATES, SHIP_FROM_CITY, SHIP_FROM_NAME, SHIP_FROM_PHONE, SHIP_FROM_STATE, SHIP_FROM_STREET1, SHIP_FROM_STREET2, SHIP_FROM_ZIP, SHOP_CONTACT_EMAIL, SHOP_POSTAL_ADDRESS, SITE_URL, STRIPE_ALLOW_LIVE, STRIPE_PUBLISHABLE_KEY, STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, TAX_PROVIDER, TURNSTILE_SECRET_KEY, TURNSTILE_SITE_KEY
>
> To reproduce, run test_specs ["apps/core/tests/test_deploy_scripts.py::ComposeEnvironmentTests"].
>
> Suggested next step: fix

**Judgement calls**

1. **Repeated settings.py defaults in compose instead of `${NAME:-}`**
   env_str() returns an empty string, not its default, when the variable is set but empty. So `${SITE_URL:-}` would blank out SITE_URL, SHOP_CONTACT_EMAIL, DEFAULT_FROM_EMAIL, SHIP_FROM_NAME/STATE and TAX_PROVIDER. They use the settings defaults instead (DEFAULT_FROM_EMAIL and SHIP_FROM_NAME build on SHOP_NAME). I checked with `docker compose config`.
   Alternatives: Make env_str treat an empty value as unset in settings.py (wider change, affects every env_str setting)
2. **SITE_URL defaults to https://${SITE_DOMAIN} in compose**
   The settings default, http://localhost:8000, would put broken links in production emails, and SITE_DOMAIN is already required.
   Alternatives: Default to localhost like settings.py
3. **Also passed EASYPOST_ALLOW_LIVE (default false)**
   .env.example mentions it only in a comment, so the test doesn't require it, but without it an owner could never turn on live postage in production.
4. **No other service changed**
   The subscription-reminder systemd unit runs `docker compose exec web ...`, so it uses the web container's environment. No other service runs Django.

**Summary**

> compose.yaml's web service now passes the 26 checkout settings from .env.example (Stripe, EasyPost, SHIP_FROM_*, email, tax, Turnstile, CSP report URI, site/shop identity), plus EASYPOST_ALLOW_LIVE, so they reach Django in production. Where config/settings.py has a default, compose repeats it, because an empty value would override it.


### T25 organic-wording-product-pages

- **Origin:** Filed by the Tasks Manager from the plan of T5 phase3-storefront-design
- **Goal:** Planning
- **Ran:** 2026-11-01 19:55 to 2026-11-01 19:58 (2m 54s)
- **Outcome:** done; committed [`25c4f5a9a41c`](https://github.com/wingware-dev/teashop/commit/25c4f5a9a41ca2ca8dcb1e1f6568b45e3ea7e00b)
- **Usage:** 1,750 input, 14k output, 1.68M cache read, 69k cache write (claude-haiku-5-5, claude-opus-5-5)
- **Tools:** 37 calls, 6 to Wing's MCP tools (wing-review 4, wing-testing 2)

**Prompt**

> Organic wording on product pages
>
> Follow-up from T5 phase3-storefront-design (ea7f0526). Product pages don't mention organic yet. For products marked 'sold as organic', add the wording permitted under the USDA small-business exemption (under $5,000 a year of organic sales): no USDA organic seal, and 'organic' only in the permitted form. See Part 2 'Imports and origin' in .TASKS/notes/see-the-file-teashop-txt-for-a-description-of-the-project.md and the copy rules in apps/catalog/copy_rules.py.
>
> See \<project>/.TASKS/notes/organic-wording-on-product-pages.md

**Judgement calls**

1. **The page avoids the word "certified" except to say the shop has no certification**
   7 CFR 205.310 bars exempt operations from the seal and from anything that presents them as certified. Saying the grower is certified could read as that kind of claim, so the note explains why there's no seal instead.
   Alternatives: Name the supplier's organic certification; Show only the word "Organic" with no note
2. **The page doesn't state the $5,000 figure**
   The note says "a shop as small as ours". The exact limit says nothing useful to customers and hints at sales volume.
   Alternatives: Quote the $5,000 limit
3. **Any "USDA" in shop copy is refused**
   In tea copy, "USDA" almost always means "USDA organic". A blanket block is the safe net, like the health-claim list.
   Alternatives: Block only "USDA organic"
4. **The structured data (JSON-LD), product cards and package labels are left unchanged**
   The task covers product pages. These are proposed as follow-ups below.

**Summary**

> Product pages now carry wording allowed under the USDA small-business organic exemption for teas marked "sold as organic", and the copy rules stop wording the exemption doesn't allow.
> - Product page: an "Organic" chip under the summary, an "Organic: Organic tea" line under Origin, and a short note that the shop packs small batches without its own certification, so the packages carry no USDA seal.
> - `copy_rules.organic_problems`: product text and AI page designs may say "organic" only for a product sold as organic, and never "certified organic", "organic certified", "USDA" or "organic seal". It runs in the same checks as the other copy rules.
> - Tests: copy rule, product validation, page design, product page view and a browser UI test (accessibility checks and screenshots in light and dark, phone and desktop). All pass.


### T7 phase5-fulfillment-dashboard

- **Origin:** Filed by the Tasks Manager from the plan of T1 see-file-teashop-txt, at the user's request
- **Goal:** Planning
- **Ran:** 2026-11-01 19:55 to 2026-11-01 20:27 (30m 23s)
- **Outcome:** done; committed [`ddec0b27c225`](https://github.com/wingware-dev/teashop/commit/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6) (shared with T30 shared-rate-limit-cache and T31 subscription-card-update)
- **Usage:** 2,533 input, 165k output, 32.70M cache read, 348k cache write (claude-haiku-5-5, claude-opus-5-5)
- **Tools:** 191 calls, 64 to Wing's MCP tools (wing-review 54, wing-testing 10)

**Prompt**

> Phase 5: fulfillment dashboard
>
> From the report of T1 see-file-teashop-txt (6f896717), section (c) Phase 5 and section '(3) Fulfillment'. Full report: .TASKS/notes/see-the-file-teashop-txt-for-a-description-of-the-project.md
>
> Scope (2-3 weeks): order queue with packing list; a box size suggested from item volume and weight, which the user can override or replace with the box actually used; box and filler stock goes down; one-click label purchase through EasyPost or Shippo, printed on a 4x6 thermal printer; tracking emailed to the customer automatically; cancellations, full and partial refunds, reships, address changes, back-orders; scheduling the free USPS carrier pickup; a phone-friendly installable web app. Packing happens when each order arrives (the user's choice): weighing bulk tea into the pouch or tin uses up the lot and packaging stock and prints the per-package label (Part 2 label contents), with a warning before packing allergen blends.
>
> Legal requirements from Part 2: record the measured net weight of each package and the scale ID with its seal or calibration date (the scale is NTEP, legal for trade); a Mail Order Rule alert for orders nearing their promised ship date, with a delay notice and a cancel option.
>
> Notifications by email only (the user's choice); new-order summaries once a day at 6pm. Test-mode label purchases only. Screenshots into doc/shots; WCAG 2.2 AA checks.
>
> [Tasks Manager, 2026-11-01 18:37] From T4 phase2-catalog-inventory-core (4d8a1a2b): packing uses catalog.services.pack(), which packs one package per order from a single lot, and label_for() gives the label facts. This task also needs to:
> - turn label_for() into a printable label (PDF or label-printer format);
> - warn before packing a blend whose Label.allergens is set, suggesting those be packed last;
> - add a service that reverses a SoldPackage for cancellations or mistaken packs, putting tea and packaging back on their lots with 'returned' movements.
> LABEL_PACKER_ADDRESS in .env must be set for real labels. See docs/inventory.md.
>
> See \<project>/.TASKS/notes/phase-5-fulfillment-dashboard.md

**Judgement calls**

1. **EasyPost rather than Shippo**
   Checkout already uses EasyPost for rates and address checks, and its key, test/live guard and privacy-policy entry were already in place.
   Alternatives: Shippo
2. **Package labels as a hand-written PDF, 4x2 in by default (PACKAGE_LABEL_SIZE)**
   No new dependency or lock-file rebuild, and the thermal printer prints PDFs from the browser. Net-weight type is sized to 21 CFR 101.105(i) with the label taken as the principal display panel; docs mark this '(verify)'.
   Alternatives: reportlab/WeasyPrint dependency; ZPL for package labels; 4x6 package labels
3. **Box and filler leave stock when the label is bought, not at packing**
   That is when the box actually used is known, including an override. Voiding the label puts them back.
   Alternatives: Take them at the first pack
4. **Packing on an overdue-inspection scale only warns; a broken seal blocks**
   A broken seal clearly makes the scale unusable for trade. An overdue inspection date may just be the county running late.
   Alternatives: Block on overdue inspection too
5. **A delay of over 30 days, or a second notice, needs express consent; the answer deadline is the later of the old ship date or 3 working days**
   Reading of 16 CFR 435.2(b)(2)-(4). A notice sent after the old date still gives the customer time to answer.
   Alternatives: Always require express consent
6. **New-order owner email now defaults to the daily 6pm summary (checkout test_flow updated to match)**
   The user chose once-a-day summaries at 6pm. OWNER_NEW_ORDER_EMAILS=each restores per-order emails.
   Alternatives: Keep per-order emails as the default
7. **Subscription-delivery packages are recorded at the size's list price**
   A delivery's package count isn't fixed in advance, so the plan price can't be split across packages at pack time.
   Alternatives: Split the plan price when the label is bought
8. **Unpacking defaults to 'reusable'; when it isn't, stock is returned and then written off as damaged**
   This keeps 'returned' as the single reversal path while still showing spilled or sealed stock in the loss report.
   Alternatives: Separate write-off-only reversal
9. **Edited compose.yaml (3 env lines) even though another task has uncommitted changes there**
   Without them the new settings can't be changed on the server. The edit is an append in a separate spot.
   Alternatives: Leave compose.yaml for a follow-up

**Screenshots**

![fulfillment-address-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-address-desktop-dark.png)

![fulfillment-address-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-address-desktop-light.png)

![fulfillment-address-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-address-phone-dark.png)

![fulfillment-address-phone-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-address-phone-light.png)

![fulfillment-delay-answer-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-delay-answer-desktop-dark.png)

![fulfillment-delay-answer-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-delay-answer-desktop-light.png)

![fulfillment-delay-answer-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-delay-answer-phone-dark.png)

![fulfillment-delay-answer-phone-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-delay-answer-phone-light.png)

![fulfillment-flow-1-packed-phone-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-flow-1-packed-phone-light.png)

![fulfillment-flow-1b-allergen-refused-phone-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-flow-1b-allergen-refused-phone-light.png)

![fulfillment-flow-2-ready-to-label-phone-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-flow-2-ready-to-label-phone-light.png)

![fulfillment-flow-3-shipped-phone-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-flow-3-shipped-phone-light.png)

![fulfillment-order-allergen-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-order-allergen-desktop-dark.png)

![fulfillment-order-allergen-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-order-allergen-desktop-light.png)

![fulfillment-order-allergen-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-order-allergen-phone-dark.png)

![fulfillment-order-allergen-phone-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-order-allergen-phone-light.png)

![fulfillment-order-late-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-order-late-desktop-dark.png)

![fulfillment-order-late-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-order-late-desktop-light.png)

![fulfillment-order-late-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-order-late-phone-dark.png)

![fulfillment-order-late-phone-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-order-late-phone-light.png)

![fulfillment-order-shipped-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-order-shipped-desktop-dark.png)

![fulfillment-order-shipped-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-order-shipped-desktop-light.png)

![fulfillment-order-shipped-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-order-shipped-phone-dark.png)

![fulfillment-order-shipped-phone-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-order-shipped-phone-light.png)

![fulfillment-packing-list-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-packing-list-desktop-dark.png)

![fulfillment-packing-list-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-packing-list-desktop-light.png)

![fulfillment-packing-list-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-packing-list-phone-dark.png)

![fulfillment-packing-list-phone-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-packing-list-phone-light.png)

![fulfillment-pickups-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-pickups-desktop-dark.png)

![fulfillment-pickups-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-pickups-desktop-light.png)

![fulfillment-pickups-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-pickups-phone-dark.png)

![fulfillment-pickups-phone-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-pickups-phone-light.png)

![fulfillment-queue-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-queue-desktop-dark.png)

![fulfillment-queue-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-queue-desktop-light.png)

![fulfillment-queue-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-queue-phone-dark.png)

![fulfillment-queue-phone-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-queue-phone-light.png)

![fulfillment-reship-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-reship-desktop-dark.png)

![fulfillment-reship-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-reship-desktop-light.png)

![fulfillment-reship-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-reship-phone-dark.png)

![fulfillment-reship-phone-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-reship-phone-light.png)

**Summary**

> Phase 5: a new `apps/fulfillment` app with an installable, phone-friendly packing dashboard at /owner/fulfillment/ (docs/fulfillment.md).
> - Order queue (late and due orders flagged, allergen teas sorted last), a packing list with allergen teas in a separate "pack last" table, and a page per order.
> - Packing weighs each package on a registered scale. It records the measured net weight and the scale's serial number and seal date, refuses packages under the labelled weight or a scale with a broken seal, and won't pack an allergen tea until allergen handling is confirmed. It prints the package label as a PDF made without any new dependency.
> - Box suggestion from package sizes and weight, which you can override or replace with another box. Box and filler stock go down.
> - EasyPost label purchase prints a 4x6 shipping label, refuses live keys unless EASYPOST_ALLOW_LIVE is set, and marks the order shipped so the tracking email goes out. Labels can be voided (the box goes back to stock). You can ship part of an order and back-order the rest.
> - Cancellations and full or partial refunds (Stripe refund added to checkout's payments; AI agents are refused), reships, address changes checked with the post office, and USPS pickups.
> - Mail Order Rule: delay notices. A first delay of up to 30 days counts silence as consent; anything longer needs the customer's yes, given through a link in the email (wait, or cancel for a full refund). The dashboard flags notices that got no answer.
> - New-order emails become one 6pm summary (`send_order_summary` plus a systemd timer). Setting OWNER_NEW_ORDER_EMAILS=each brings back one email per order.
> - `catalog.services.reverse_package()` undoes a pack with 'returned' stock movements. Reversed packages are excluded from organic sales and the profit report.
> - Browser tests with WCAG 2.2 AA checks, and milestone screenshots in doc/shots/2026-11-01-phase5-fulfillment.


### T35 checkout-deploy-checks-break-settings

- **Origin:** Found by T33 regression-tests-after-checkout
- **Goal:** Planning
- **Ran:** 2026-11-01 19:56 to 2026-11-01 19:58 (0m 55s)
- **Outcome:** done; committed [`81616b891cb5`](https://github.com/wingware-dev/teashop/commit/81616b891cb5c8406a0727255689181bd756678e) (shared with T34 compose-checkout-env-vars)
- **Usage:** 26 input, 5,421 output, 479k cache read, 16k cache write (claude-opus-5-5)
- **Tools:** 10 calls, 4 to Wing's MCP tools (wing-review 3, wing-testing 1)

**Prompt**

> New checkout deploy checks make test_deploy_checks_pass fail (check --deploy --fail-level WARNING)
>
> Task T6 phase4-cart-checkout (e36d1a1d) added apps/checkout/checks.py, which registers `@register(deploy=True)` warnings checkout.W001–W006 for unset EMAIL_HOST, Stripe, STRIPE_WEBHOOK_SECRET, EasyPost/SHIP_FROM_*, SHOP_POSTAL_ADDRESS and SITE_URL. apps/core/tests/test_settings.py::ProductionSettingsTests.test_deploy_checks_pass runs `manage.py check --deploy --fail-level WARNING` with a minimal PRODUCTION_ENV (line 11) that sets none of these, so it now fails. The checks are doing their job, which is to warn a real deploy that's missing these. The likely fix is in the test: add test values for the checkout settings to PRODUCTION_ENV in test_settings.py (EMAIL_HOST, STRIPE_* test keys, EASYPOST_API_KEY, SHIP_FROM_*, SHOP_POSTAL_ADDRESS, SITE_URL=https://shop.example.com). Then add a test asserting the checkout warnings do appear when those are missing. Read apps/checkout/checks.py first to see exactly which variables each check needs. Silencing the checks in settings would be the wrong fix. Found by the regression sweep task T33 regression-tests-after-checkout (84d15c13).
>
> Evidence: apps/core/tests/test_settings.py::ProductionSettingsTests.test_deploy_checks_pass, line 36:
> ```
> AssertionError: 1 != 0 : SystemCheckError: System check identified some issues:
> WARNINGS:
> ?: (checkout.W001) EMAIL_HOST is not set: order emails are printed, not sent.
> ?: (checkout.W002) Stripe is not set up: checkout stays closed.
> ?: (checkout.W004) EasyPost or the SHIP_FROM_* address is not set: checkout stays closed.
> ?: (checkout.W005) SHOP_POSTAL_ADDRESS is not set: emails and policies need a postal address (CAN-SPAM).
> ?: (checkout.W006) SITE_URL is not set: links in emails point at localhost.
> System check identified 5 issues (2 silenced).
> ```
> W003 didn't fire, probably because it only applies once Stripe is set up. The test runs manage.py in a subprocess, so the order tests run in doesn't matter. To reproduce, run test_specs ["apps/core/tests/test_settings.py::ProductionSettingsTests.test_deploy_checks_pass"].
>
> Suggested next step: fix

**Judgement calls**

1. **Kept checkout variables from the shell out of the subprocess**
   Without this, a developer with Stripe or EasyPost keys exported would see the warning tests fail, or a live key would make settings refuse to load.
   Alternatives: Strip only what was stripped before (DJANGO\_, DATABASE_URL, SENTRY\_)
2. **Added a separate W003 test**
   W003 can only fire once Stripe is set up, so the test with nothing set up can't cover it.

**Summary**

> Fixed test_deploy_checks_pass by giving it a fully set-up checkout environment, and added tests that the checkout deploy warnings fire:
> - New CHECKOUT_ENV in apps/core/tests/test_settings.py holds test values: SMTP host, Stripe test keys and webhook secret, an EZTK EasyPost key, SHIP_FROM address, SHOP_POSTAL_ADDRESS and SITE_URL. test_deploy_checks_pass uses it.
> - New tests: checkout.W001/W002/W004/W005/W006 fire with only the minimal production env (W003 doesn't), and W003 fires when Stripe is set up without STRIPE_WEBHOOK_SECRET.
> - run_manage no longer passes the developer's own EMAIL_*, STRIPE_*, EASYPOST_*, SHIP_FROM_*, SHOP_POSTAL_ADDRESS, SITE_URL or *_PROVIDER variables to the subprocess, so the results don't depend on the shell.


### T30 shared-rate-limit-cache

- **Origin:** Filed by the Tasks Manager from the plan of T6 phase4-cart-checkout
- **Goal:** Planning
- **Ran:** 2026-11-01 19:58 to 2026-11-01 20:27 (2m 27s)
- **Outcome:** done; committed [`ddec0b27c225`](https://github.com/wingware-dev/teashop/commit/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6) (shared with T7 phase5-fulfillment-dashboard and T31 subscription-card-update)
- **Usage:** 2,535 input, 12k output, 1.59M cache read, 29k cache write (claude-haiku-5-5, claude-opus-5-5)
- **Tools:** 25 calls, 10 to Wing's MCP tools (wing-testing 6, wing-review 4)

**Prompt**

> Shared cache for rate limits
>
> Follow-up from T6 phase4-cart-checkout (e36d1a1d). The checkout bot rate limit (apps/checkout/protection.py) uses each gunicorn worker's own memory, so the effective limit is higher than configured. Use Django's database cache (or Redis), so the limit is shared across workers and survives restarts.
>
> [Tasks Manager, 2026-11-01 19:58] Manager: use Django's DatabaseCache (no Redis; nothing new to run on the VPS). Run `createcachetable` wherever migrate runs: the deploy/install scripts, the "Migrate dev database" entry point and the test setup. Add a test showing two separate cache clients share the count. T7 (fulfillment) and T25 (storefront) are running at the same time. Keep your config/settings.py change to the CACHES block, and don't touch apps/fulfillment or the storefront templates.
>
> See \<project>/.TASKS/notes/shared-cache-for-rate-limits.md

**Judgement calls**

1. **createcachetable runs from a post_migrate hook, not added to each script**
   The Migrate dev database entry point runs only `manage.py migrate` and can't chain a second command. A hook covers deploy.sh, the entry point, README setup and the test database in one place that can't be forgotten. Django's test runner also runs createcachetable itself.
   Alternatives: Add `manage.py createcachetable` after migrate in deploy.sh, and a second entry point
2. **The hook lives in apps/checkout/apps.py, not apps/core**
   Django sends post_migrate only to apps with models, and apps.core has none. The debugger confirmed the hook never ran there. Checkout has models and owns the rate limits.
3. **MAX_ENTRIES raised to 20000 (default 300)**
   A burst of addresses past 300 would make the cache cull and drop live counts, which is exactly what a bot run creates.
4. **Ran createcachetable on the local dev database**
   Without the table, the dev server's checkout forms would fail. I didn't run migrate there, because T7 and T25 may have unfinished migrations.

**Screenshots**

![fulfillment-address-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-address-desktop-dark.png)

![fulfillment-address-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-address-desktop-light.png)

![fulfillment-address-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-address-phone-dark.png)

![fulfillment-address-phone-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-address-phone-light.png)

![fulfillment-delay-answer-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-delay-answer-desktop-dark.png)

![fulfillment-delay-answer-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-delay-answer-desktop-light.png)

![fulfillment-delay-answer-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-delay-answer-phone-dark.png)

![fulfillment-delay-answer-phone-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-delay-answer-phone-light.png)

![fulfillment-flow-1-packed-phone-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-flow-1-packed-phone-light.png)

![fulfillment-flow-1b-allergen-refused-phone-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-flow-1b-allergen-refused-phone-light.png)

![fulfillment-flow-2-ready-to-label-phone-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-flow-2-ready-to-label-phone-light.png)

![fulfillment-flow-3-shipped-phone-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-flow-3-shipped-phone-light.png)

![fulfillment-order-allergen-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-order-allergen-desktop-dark.png)

![fulfillment-order-allergen-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-order-allergen-desktop-light.png)

![fulfillment-order-allergen-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-order-allergen-phone-dark.png)

![fulfillment-order-allergen-phone-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-order-allergen-phone-light.png)

![fulfillment-order-late-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-order-late-desktop-dark.png)

![fulfillment-order-late-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-order-late-desktop-light.png)

![fulfillment-order-late-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-order-late-phone-dark.png)

![fulfillment-order-late-phone-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-order-late-phone-light.png)

![fulfillment-order-shipped-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-order-shipped-desktop-dark.png)

![fulfillment-order-shipped-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-order-shipped-desktop-light.png)

![fulfillment-order-shipped-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-order-shipped-phone-dark.png)

![fulfillment-order-shipped-phone-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-order-shipped-phone-light.png)

![fulfillment-packing-list-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-packing-list-desktop-dark.png)

![fulfillment-packing-list-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-packing-list-desktop-light.png)

![fulfillment-packing-list-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-packing-list-phone-dark.png)

![fulfillment-packing-list-phone-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-packing-list-phone-light.png)

![fulfillment-pickups-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-pickups-desktop-dark.png)

![fulfillment-pickups-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-pickups-desktop-light.png)

![fulfillment-pickups-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-pickups-phone-dark.png)

![fulfillment-pickups-phone-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-pickups-phone-light.png)

![fulfillment-queue-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-queue-desktop-dark.png)

![fulfillment-queue-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-queue-desktop-light.png)

![fulfillment-queue-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-queue-phone-dark.png)

![fulfillment-queue-phone-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-queue-phone-light.png)

![fulfillment-reship-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-reship-desktop-dark.png)

![fulfillment-reship-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-reship-desktop-light.png)

![fulfillment-reship-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-reship-phone-dark.png)

![fulfillment-reship-phone-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-reship-phone-light.png)

**Summary**

> Checkout rate limits now live in Django's DatabaseCache, so all gunicorn workers share the count and it survives restarts:
> - config/settings.py: new CACHES block (DatabaseCache, table teashop_cache, MAX_ENTRIES 20000).
> - apps/checkout/apps.py: a post_migrate hook runs createcachetable, so every migrate creates the table (deploy.sh, the Migrate dev database entry point, README setup, test database creation).
> - New apps/checkout/tests/test_rate_limit_cache.py: two separate DatabaseCache clients share one count, and migrate recreates a dropped cache table.


### T31 subscription-card-update

- **Origin:** Filed by the Tasks Manager from the plan of T6 phase4-cart-checkout
- **Goal:** Planning
- **Ran:** 2026-11-01 19:59 to 2026-11-01 20:27 (6m 20s)
- **Outcome:** done; committed [`ddec0b27c225`](https://github.com/wingware-dev/teashop/commit/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6) (shared with T7 phase5-fulfillment-dashboard and T30 shared-rate-limit-cache)
- **Usage:** 1,937 input, 31k output, 3.31M cache read, 106k cache write (claude-haiku-5-5, claude-opus-5-5)
- **Tools:** 53 calls, 7 to Wing's MCP tools (wing-review 3, wing-analysis 2, wing-testing 2)

**Prompt**

> Customer payment-method updates for subscriptions
>
> Follow-up from T6 phase4-cart-checkout (e36d1a1d). A customer whose subscription renewal fails can only write in or cancel. Add Stripe's customer portal or a SetupIntent page, so they can update their card online, linked from the payment-failed email. Use stand-ins in tests: no Stripe account exists, and none may be created.
>
> [Tasks Manager, 2026-11-01 19:59] Manager: T7 (fulfillment) and T30 (rate-limit cache in apps/checkout/protection.py) are running at the same time. If you must change apps/checkout/emails.py, change only the payment-failed email's link and keep every function's call signature, because T29 will move these sends onto a job queue. Don't edit protection.py or config/settings.py, except to add one setting if you need it. Prefer a SetupIntent page on the shop's own pages, which can be tested with stand-ins, over the hosted portal. Check it in the browser harness (apps/core/uitesting.py), including the axe accessibility check.
>
> See \<project>/.TASKS/notes/customer-payment-method-updates-for-subscriptions.md

**Judgement calls**

1. **Built a SetupIntent page on the shop's own pages, not Stripe's hosted customer portal**
   The Tasks Manager preferred it, it can be tested with stand-ins, and it reuses the existing Payment Element and CSP.
2. **The card page needs no sign-in: the subscription token in the link is enough**
   This matches the one-step cancel link that is already in every subscription email. The worst a leaked link allows is attaching someone else's card to the subscription.
   Alternatives: Require the account sign-in link first
3. **Each visit to the card page creates a new SetupIntent**
   It's simple, and unused SetupIntents cost nothing. Email link scanners may leave a few incomplete ones in Stripe.
   Alternatives: Cache the SetupIntent id in the session and reuse it
4. **Added handling for the setup_intent.succeeded webhook, which the owner must add in Stripe's dashboard**
   Without it, a customer who closes the tab during the 3-D Secure redirect has their card saved but not used. docs/checkout.md and the webhooks.py docstring now list the event.
5. **The stand-in provider's card save counts as a successful retry of a missed renewal and creates the delivery order**
   This mirrors fake_pay, so the whole flow can be tried on a laptop.

**Screenshots**

![fulfillment-address-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-address-desktop-dark.png)

![fulfillment-address-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-address-desktop-light.png)

![fulfillment-address-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-address-phone-dark.png)

![fulfillment-address-phone-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-address-phone-light.png)

![fulfillment-delay-answer-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-delay-answer-desktop-dark.png)

![fulfillment-delay-answer-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-delay-answer-desktop-light.png)

![fulfillment-delay-answer-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-delay-answer-phone-dark.png)

![fulfillment-delay-answer-phone-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-delay-answer-phone-light.png)

![fulfillment-flow-1-packed-phone-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-flow-1-packed-phone-light.png)

![fulfillment-flow-1b-allergen-refused-phone-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-flow-1b-allergen-refused-phone-light.png)

![fulfillment-flow-2-ready-to-label-phone-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-flow-2-ready-to-label-phone-light.png)

![fulfillment-flow-3-shipped-phone-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-flow-3-shipped-phone-light.png)

![fulfillment-order-allergen-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-order-allergen-desktop-dark.png)

![fulfillment-order-allergen-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-order-allergen-desktop-light.png)

![fulfillment-order-allergen-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-order-allergen-phone-dark.png)

![fulfillment-order-allergen-phone-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-order-allergen-phone-light.png)

![fulfillment-order-late-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-order-late-desktop-dark.png)

![fulfillment-order-late-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-order-late-desktop-light.png)

![fulfillment-order-late-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-order-late-phone-dark.png)

![fulfillment-order-late-phone-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-order-late-phone-light.png)

![fulfillment-order-shipped-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-order-shipped-desktop-dark.png)

![fulfillment-order-shipped-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-order-shipped-desktop-light.png)

![fulfillment-order-shipped-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-order-shipped-phone-dark.png)

![fulfillment-order-shipped-phone-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-order-shipped-phone-light.png)

![fulfillment-packing-list-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-packing-list-desktop-dark.png)

![fulfillment-packing-list-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-packing-list-desktop-light.png)

![fulfillment-packing-list-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-packing-list-phone-dark.png)

![fulfillment-packing-list-phone-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-packing-list-phone-light.png)

![fulfillment-pickups-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-pickups-desktop-dark.png)

![fulfillment-pickups-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-pickups-desktop-light.png)

![fulfillment-pickups-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-pickups-phone-dark.png)

![fulfillment-pickups-phone-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-pickups-phone-light.png)

![fulfillment-queue-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-queue-desktop-dark.png)

![fulfillment-queue-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-queue-desktop-light.png)

![fulfillment-queue-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-queue-phone-dark.png)

![fulfillment-queue-phone-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-queue-phone-light.png)

![fulfillment-reship-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-reship-desktop-dark.png)

![fulfillment-reship-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-reship-desktop-light.png)

![fulfillment-reship-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-reship-phone-dark.png)

![fulfillment-reship-phone-light.png](https://github.com/wingware-dev/teashop/raw/ddec0b27c225c96cd5e4669f3d43d08d4eeb5fc6/doc/shots/2026-11-01-phase5-fulfillment/fulfillment-reship-phone-light.png)

**Summary**

> Subscribers can now update their card online on the shop's own card page, which uses a Stripe SetupIntent and is linked from the payment-failed email:
> - New page `/subscriptions/card/<token>/` (subscription_views.card / card_done / card_fake, template subscriptions/card.html). Like the cancel link, it needs no sign-in and works while the shop is closed. The Payment Element saves the card, which then becomes the subscription's and the customer's default, and any open renewal invoice is retried on it right away. The page reports one of: paid, saved, declined, processing or failed.
> - New `start_card_update` / `finish_card_update` on StripePayments and FakePayments (payments.CardUpdate), plus `subscriptions.can_update_card` / `update_card`. `finish_card_update` is safe to repeat and refuses a SetupIntent whose metadata or customer belongs to a different subscription.
> - The webhook now handles `setup_intent.succeeded` as a backstop in case the customer never reaches the return page. checkout.js calls confirmSetup when the form has `data-intent="setup"`.
> - In emails.py only the payment-failed email changed: it gains `card_url`, and no function signature changed. Also added Subscription.card_url(), an "Update card" button on the account page, and updates to docs/checkout.md.
> - 13 unit tests use stand-in Stripe clients. A browser test (axe, reflow, both viewport/theme combos) covers the page from the email link through to updated and cancelled. The targeted tests all pass.


### T29 background-job-queue

- **Origin:** Filed by the Tasks Manager from the plan of T6 phase4-cart-checkout
- **Goal:** Planning
- **Ran:** 2026-11-01 20:27 to 2026-11-01 20:43 (15m 01s)
- **Outcome:** done; committed [`8371a0532c29`](https://github.com/wingware-dev/teashop/commit/8371a0532c2953c18264a6a15d1e5faf9daaecf7) (shared with T44 refund-records-tax)
- **Usage:** 2,174 input, 85k output, 11.07M cache read, 175k cache write (claude-haiku-5-5, claude-opus-5-5)
- **Tools:** 137 calls, 28 to Wing's MCP tools (wing-review 22, wing-testing 6)

**Prompt**

> Background job queue for emails
>
> Follow-up from T6 phase4-cart-checkout (e36d1a1d). Emails are sent inside the request or webhook. A failure is logged and flagged on the dashboard with a resend action, but nothing retries automatically. Move the sends (apps/checkout/emails.py) and the subscription-reminder job onto the PostgreSQL-backed job queue planned in docs/architecture.md, with automatic retries. Keep the email functions' call signatures so later phases (fulfillment, the email list, owner reminders) can call them and get queued sending for free. Document how other apps queue jobs.
>
> [Tasks Manager, 2026-11-01 20:27] Manager: T7 phase5-fulfillment-dashboard (d598b6a8, committed ddec0b2) added more senders and timers. These are the shipping/tracking email, delay notices, `send_order_summary` with its 6pm systemd timer, and the T31 card-update link in the payment-failed email. Move these onto the job queue too, or schedule them through it, and keep systemd only for the worker or ticker unit. Make sure install-app.sh installs any unit you add. T8 will add a daily owner reminder and T10 the email list, both on this queue, so document an API both can use: enqueue, scheduled/periodic jobs, retries. T41 (tax reports) and T42 (apps/inventory/reorder.py) run at the same time. Stay out of apps/checkout's tax/nexus report code and apps/inventory.
>
> See \<project>/.TASKS/notes/background-job-queue-for-emails.md

**Judgement calls**

1. **Built a small queue in apps/jobs instead of adding django-tasks**
   The task needs automatic retries and scheduled/periodic jobs. django-tasks' database backend offers neither, so they would have had to be built on top of it anyway. Doing it in-house adds no dependency to the hash-locked requirements, and the code is about 300 lines of tested code.
   Alternatives: django-tasks DatabaseBackend plus our own retry and schedule layer; Procrastinate or django-q2 (more features, another dependency)
2. **The worker is a compose service; no new systemd unit**
   docs/architecture.md planned the worker as one more compose service. Docker restarts it, and deploy/rollback start it with web. systemd now keeps only the backup and restore-test timers, which run outside the app.
   Alternatives: A systemd unit running `docker compose run worker`; A systemd ticker that enqueues the daily jobs
3. **Email functions now return the queued Job (truthy), not whether the email was delivered**
   Sending happens later. The job sets confirmation_sent_at, notice.sent_at, refund.email_sent_at and so on. So the admin 'marked shipped' message, the delay-notice page message and the resend action no longer report an email failure on the spot. The dashboard alerts now wait 10 minutes before flagging an unsent confirmation or delay notice.
   Alternatives: Wait for the job in the request (defeats the purpose)
4. **Each failed attempt is logged; only the final failure goes in the audit log, as jobs.failed**
   A job runs in a transaction that rolls back when it fails, which would also roll back a per-attempt checkout.email_failed / fulfillment.email_failed record. The final failure is recorded and shown on the dashboard.
   Alternatives: Run email jobs outside a transaction so per-attempt audit records survive
5. **JOBS_EAGER is on except in production**
   On a laptop and in tests a job runs as soon as it is queued, through the same code path as the worker, so existing mail.outbox tests and the dev workflow keep working without a worker. Production always uses the worker.
   Alternatives: Always queue and make tests call run_due()
6. **Job rows are excluded from the audit log**
   Job arguments can contain sign-in links, and job bookkeeping would flood the log. What the jobs do (emails sent, failures) is still recorded.
7. **Rolling back to a build from before the queue stops the worker**
   Older builds have no run_jobs command and send their emails themselves. Jobs already queued wait until a build with the worker is deployed again.

**Summary**

> Added a PostgreSQL-backed background job queue (apps/jobs) with automatic retries and daily/periodic schedules, and moved every email and both daily timers onto it:
> - New `apps/jobs`: `@jobs.job`, `enqueue()` (transactional, `delay`/`run_at`, dedupe `key`), `jobs.schedule(daily_at=/every=, tz=)`, `jobs.Retry`, the `run_jobs` worker command (SKIP LOCKED, reclaims jobs a dead worker left running, stops cleanly on SIGTERM), admin pages with a "Run again" action, dashboard items for failed jobs and for a worker that isn't running, and a nightly purge of old job rows.
> - All senders in apps/checkout/emails.py and apps/fulfillment/emails.py keep their signatures and now queue a job: confirmation, shipped/tracking, part shipped, reshipped, delay notice, cancellation, refund, sign-in link, owner notices, and the subscription emails, including the card-update link in the payment-failed email. The job sets the "sent at" fields once the email is sent. Emails retry for about 18 hours; sign-in links for about 20 minutes.
> - The 6pm order summary and the subscription reminders are now schedules in apps/fulfillment/jobs.py and apps/checkout/jobs.py. Their systemd units are deleted, and install-app.sh disables and removes them on servers that already have them. A new `worker` service in compose.yaml uses the web image and settings and has a heartbeat healthcheck; deploy.sh and rollback.sh start it alongside web.
> - docs/jobs.md explains how apps queue, schedule and retry jobs (for T8 and T10); architecture, checkout, fulfillment and ops docs are updated.


### T41 net-refunds-from-tax-reports

- **Origin:** Filed by the Tasks Manager from the plan of T7 phase5-fulfillment-dashboard
- **Goal:** Planning
- **Ran:** 2026-11-01 20:27 to 2026-11-01 20:31 (3m 11s)
- **Outcome:** done; committed [`97b350bafc60`](https://github.com/wingware-dev/teashop/commit/97b350bafc6096509a0ab8ec50ee8f321da14e87)
- **Usage:** 52 input, 16k output, 1.15M cache read, 53k cache write (claude-opus-5-5)
- **Tools:** 30 calls, 5 to Wing's MCP tools (wing-review 4, wing-testing 1)

**Prompt**

> Net refunds out of sales-tax and nexus figures
>
> Refunds are recorded in fulfillment.Refund (added by T7 phase5-fulfillment-dashboard (d598b6a8)), but checkout's NY tax-by-quarter and nexus reports still count each order's full total. Subtract refunds, including refunded merch tax, so the tax filings are right.
>
> See \<project>/.TASKS/notes/net-refunds-out-of-sales-tax-and-nexus-figures.md

**Judgement calls**

1. **Partial refunds give back tax in proportion to the order's total**
   Refund records only an amount, not which lines it covers, so a partial refund of exempt tea is treated as partly taxable. Full refunds and cancellations are exact.
   Alternatives: Record taxable/tax amounts on Refund when it is issued (fulfillment model change, outside this task's scope)
2. **Cancelled orders that were paid now count as sales in their paid period, offset by their refund**
   Before, they dropped out of their original quarter retroactively. That contradicts the refund-period rule and changes figures that may already be filed. The only way to cancel a paid order (cancel_order) always records a Refund for what is left.
   Alternatives: Keep excluding cancelled orders and skip their refunds
3. **Nexus order counts still exclude cancelled orders; the NY table counts every order that took payment**
   A cancelled sale is arguably not a transaction for state thresholds. The NY table's order count matches the sales it sums.
   Alternatives: Count cancelled orders in both; Exclude them from both
4. **Net figures can go negative in a period with refunds of earlier sales**
   That is what a refund in a later period means on a return, so I shown it as is rather than clamping to zero.

**Summary**

> Net refunds out of the NY sales-tax-by-quarter and nexus figures, each refund taken off the period it was issued in.
> - `nexus.refund_shares` splits each fulfillment Refund into sales, taxable and tax shares in proportion to its order's total, cumulatively, so partial refunds add up to exactly the tax collected; refunded overpayments don't count as sales.
> - `nexus.sales_by_state` and the new `nexus.ny_tax_by_quarter` (moved out of owner_views) count orders that took payment, including later-cancelled ones, in their paid period and subtract refunds in the period issued.
> - The Sales by state page gets a Refunded column and help text saying refunds reduce the period they were issued in, as NY returns require.


### T44 refund-records-tax

- **Origin:** Filed by the Tasks Manager from the plan of T41 net-refunds-from-tax-reports
- **Goal:** Planning
- **Ran:** 2026-11-01 20:31 to 2026-11-01 20:43 (4m 45s)
- **Outcome:** done; committed [`8371a0532c29`](https://github.com/wingware-dev/teashop/commit/8371a0532c2953c18264a6a15d1e5faf9daaecf7) (shared with T29 background-job-queue)
- **Usage:** 1,696 input, 23k output, 2.87M cache read, 45k cache write (claude-haiku-5-5, claude-opus-5-5)
- **Tools:** 49 calls, 6 to Wing's MCP tools (wing-analysis 2, wing-review 2, wing-testing 2)

**Prompt**

> Record refunded tax on each Refund
>
> Store taxable and tax amounts on fulfillment.Refund when it is issued, from the refunded lines. Then partial refunds of exempt items stop being apportioned by total in the tax reports changed by T41 net-refunds-from-tax-reports (a5c0cde9).

**Judgement calls**

1. **Owner ticks what a refund is for; nothing ticked means the order as a whole**
   Refunds were amount-only with no record of lines. Ticking is optional, so goodwill refunds and service callers (cancel_order) keep working, with the old proportional split as the fallback.
   Alternatives: Require items for every partial refund; Store per-line RefundLine records
2. **Amount may be less than the ticked items come to, never more**
   Covers part-refunds such as half back for a chipped lid, and stops a refund of tea from quietly covering taxable goods.
   Alternatives: Treat any excess as a share of the rest of the order
3. **Only the taxable and tax amounts are stored, not which lines were refunded**
   That is what the task asked for, and all the tax reports need.
   Alternatives: Add a RefundLine model
4. **Existing refunds backfilled with the old proportional split**
   They don't record what they were for, and this matches what the reports showed until now.

**Summary**

> Each fulfillment Refund now records the taxable amount and sales tax it gives back, from what it is for, and the tax reports use those instead of a share of the order's total.
> - New `checkout.tax.refund_tax`: spreads the refund over the ticked items and shipping by their cost with tax, so refunded tea gives back no tax. It refuses more than the ticked items come to; with nothing ticked it falls back to a share of the order. Tax given back never exceeds what was collected, and the refund that completes the order gives back exactly the rest.
> - The refund form on the order page gains per-item quantity boxes and a shipping checkbox; the refunds list shows the tax given back, and the admin shows it too.
> - Migration 0002_refund_tax adds the fields and fills in existing refunds by the old proportional method; `nexus.refund_shares` reads the stored figures.


### T42 net-returns-from-reorder-use

- **Origin:** Filed by the Tasks Manager from the plan of T7 phase5-fulfillment-dashboard
- **Goal:** Planning
- **Ran:** 2026-11-01 20:43 to 2026-11-01 20:44 (1m 07s)
- **Outcome:** done; committed [`97da9953f218`](https://github.com/wingware-dev/teashop/commit/97da9953f218f61096ea0284baf81ff277e8708e)
- **Usage:** 1,649 input, 5,210 output, 596k cache read, 37k cache write (claude-haiku-5-5, claude-opus-5-5)
- **Tools:** 16 calls, 6 to Wing's MCP tools (wing-review 5, wing-testing 1)

**Prompt**

> Net returned stock out of reorder daily use
>
> inventory/reorder.py counts SALE movements as demand but ignores the 'returned' adjustments from catalog reverse_package (added by T7 phase5-fulfillment-dashboard (d598b6a8)). Cancelled packs therefore overstate daily use a little.

**Judgement calls**

1. **Net any positive 'returned' adjustment, not only those from reverse_package**
   The query can't tell reverse_package rows from a manual 'Returned to stock' adjustment made in admin, and either way the stock came back rather than being used.
   Alternatives: Net only returns whose reference matches a SALE movement in the window
2. **Date a return by when it happened and clamp net use at zero**
   If an order was packed before the 90-day window and unpacked inside it, the return could otherwise push daily use below zero. Clamping keeps it simple; matching returns to their own sales would be exact but costs an extra query.
   Alternatives: Count a return only when the sale it reverses falls inside the window

**Summary**

> Reorder daily use now subtracts stock returned to the shelf:
> - `apps/inventory/reorder.py`: `used_movements()` also picks up positive 'returned' adjustments (as written by catalog `reverse_package`), and an item's net use within the window is clamped at zero; module docstring updated.
> - New test `ReorderTests.test_returned_stock_nets_out_of_use` covers a plain return, a return later written off as damaged (which correctly ends up as a loss, not demand), and the clamp.


### T10 phase8-email-list

- **Origin:** Filed by the Tasks Manager from the plan of T1 see-file-teashop-txt, at the user's request
- **Goal:** Planning
- **Ran:** 2026-11-01 20:43 to 2026-11-01 21:06 (13m 08s)
- **Outcome:** done; committed [`ccc52ca8f8f1`](https://github.com/wingware-dev/teashop/commit/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402) (shared with T8 phase6-owner-dashboard-reporting)
- **Usage:** 193k input, 106k output, 8.71M cache read, 224k cache write (claude-haiku-5-5, claude-opus-5-5)
- **Tools:** 131 calls, 39 to Wing's MCP tools (wing-review 38, wing-testing 1)

**Prompt**

> Phase 8: marketing email list
>
> From the report of T1 see-file-teashop-txt (6f896717), section (c) Phase 8 and section '(6) Marketing'. Full report: .TASKS/notes/see-the-file-teashop-txt-for-a-description-of-the-project.md
>
> Scope (1-2 weeks), built in-house (the user's choice): opt-in only (default no) with a confirmation email; consent records; each subscriber picks a maximum frequency, and the system combines content to stay within it; the user approves every mailing before it goes out. Sending goes through a bulk email service: the user mentioned Zoho, the report suggested Amazon SES or Postmark. Compare them and recommend one, but sign up for nothing.
>
> Legal requirements from Part 2: CAN-SPAM (a physical postal address, which can be the registered PO box; a working unsubscribe; honest subject lines); the Gmail and Yahoo bulk-sender rules (one-click unsubscribe; SPF, DKIM and DMARC).
>
> [Tasks Manager, 2026-11-01 20:42] Manager, from T29 background-job-queue (e7891f25): queue email-list sends with `apps.jobs` (docs/jobs.md). Enqueue one job per recipient with a `key`, so each email retries on its own. Recurring work uses `jobs.schedule`, with no systemd units. Use a stand-in email backend in tests and sign up for no service. T8 (owner dashboard and reporting) may run at the same time. Register the mailing-approval item through the attention registry (apps/core/attention.py) and leave the dashboard template to T8. Check the sign-up and unsubscribe pages in the browser harness with axe, and record milestone screenshots.
>
> See \<project>/.TASKS/notes/phase-8-marketing-email-list.md

**Judgement calls**

1. **Recommended Amazon SES over Postmark and Zoho**
   Checked against the providers' own pages. SES costs about $0.10 per 1,000 emails with no minimum, and it sends our message as built, with our unsubscribe headers, so our consent records stay the only list. Postmark costs about $15-18 a month for 10,000 emails, and by default it adds its own unsubscribe link and keeps its own unsubscribe list; using ours instead needs Postmark support's approval. Zoho Mail's and ZeptoMail's terms forbid marketing email, and Zoho Campaigns only sends to lists stored in Zoho.
   Alternatives: Postmark Broadcast stream; Zoho Campaigns with the list synced into Zoho
2. **Approval releases a mailing's content; the combined email itself isn't approved separately**
   Combining mailings to respect each subscriber's limit means some people get emails made of several approved mailings. Asking for approval of every combination would be unworkable. The preview page explains how combining works.
   Alternatives: Approve each day's batch of combined emails
3. **Monthly is preselected on the sign-up form**
   Joining is still opt-in, since nothing signs anyone up except submitting this form and confirming by email. Preselecting the least frequent choice is the least intrusive.
   Alternatives: No choice preselected (an extra required click)
4. **Mailings approved before someone joined are never sent to them**
   A new subscriber shouldn't get a burst of old news or expired offers.
   Alternatives: Send them recent mailings that are still current
5. **Used T8's new attention fields (kind/key/since)**
   The mailing-approval item uses kind="approvals" so it gets the 3-day reminder deadline. These fields exist only in T8's uncommitted edits to apps/core/attention.py, so this work must be committed together with or after T8.
   Alternatives: Plain Attention items with no kind (would fall under 'other', reminded daily)
6. **Sign-up page appears only once the shop is open; unsubscribe, confirm and settings links always work**
   The sign-up page follows the shop's existing visibility rule. Unsubscribe links in sent emails must always work (CAN-SPAM).
   Alternatives: Also put a sign-up form on the coming-soon page

**Screenshots**

![account-security-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/account-security-desktop-dark.png)

![account-security-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/account-security-desktop-light.png)

![account-security-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/account-security-phone-dark.png)

![account-security-phone-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/account-security-phone-light.png)

![login-code-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/login-code-desktop-dark.png)

![login-code-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/login-code-desktop-light.png)

![login-code-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/login-code-phone-dark.png)

![login-code-phone-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/login-code-phone-light.png)

![login-password-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/login-password-desktop-dark.png)

![login-password-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/login-password-desktop-light.png)

![login-password-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/login-password-phone-dark.png)

![login-password-phone-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/login-password-phone-light.png)

![login-wrong-code-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/login-wrong-code-desktop-light.png)

![owner-dashboard-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/owner-dashboard-desktop-dark.png)

![owner-dashboard-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/owner-dashboard-desktop-light.png)

![owner-dashboard-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/owner-dashboard-phone-dark.png)

![owner-dashboard-phone-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/owner-dashboard-phone-light.png)

![owner-dashboard-queue-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/owner-dashboard-queue-desktop-dark.png)

![owner-dashboard-queue-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/owner-dashboard-queue-desktop-light.png)

![owner-dashboard-queue-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/owner-dashboard-queue-phone-dark.png)

![owner-dashboard-queue-phone-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/owner-dashboard-queue-phone-light.png)

![purchasing-profit-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/purchasing-profit-desktop-dark.png)

![purchasing-profit-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/purchasing-profit-desktop-light.png)

![purchasing-profit-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/purchasing-profit-phone-dark.png)

![purchasing-profit-phone-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/purchasing-profit-phone-light.png)

![reports-accounting-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/reports-accounting-desktop-dark.png)

![reports-accounting-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/reports-accounting-desktop-light.png)

![reports-accounting-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/reports-accounting-phone-dark.png)

![reports-accounting-phone-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/reports-accounting-phone-light.png)

![reports-estimated-tax-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/reports-estimated-tax-desktop-dark.png)

![reports-estimated-tax-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/reports-estimated-tax-desktop-light.png)

![reports-estimated-tax-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/reports-estimated-tax-phone-dark.png)

![reports-estimated-tax-phone-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/reports-estimated-tax-phone-light.png)

![reports-margin-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/reports-margin-desktop-dark.png)

![reports-margin-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/reports-margin-desktop-light.png)

![reports-margin-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/reports-margin-phone-dark.png)

![reports-margin-phone-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/reports-margin-phone-light.png)

![reports-sales-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/reports-sales-desktop-dark.png)

![reports-sales-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/reports-sales-desktop-light.png)

![reports-sales-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/reports-sales-phone-dark.png)

![reports-sales-phone-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/reports-sales-phone-light.png)

![reports-sales-tax-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/reports-sales-tax-desktop-dark.png)

![reports-sales-tax-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/reports-sales-tax-desktop-light.png)

![reports-sales-tax-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/reports-sales-tax-phone-dark.png)

![reports-sales-tax-phone-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/reports-sales-tax-phone-light.png)

![emaillist-confirm-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-confirm-desktop-dark.png)

![emaillist-confirm-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-confirm-desktop-light.png)

![emaillist-confirm-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-confirm-phone-dark.png)

![emaillist-confirm-phone-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-confirm-phone-light.png)

![emaillist-flow-check-email-phone-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-flow-check-email-phone-light.png)

![emaillist-flow-confirmed-phone-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-flow-confirmed-phone-light.png)

![emaillist-flow-frequency-saved-phone-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-flow-frequency-saved-phone-light.png)

![emaillist-flow-unsubscribed-phone-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-flow-unsubscribed-phone-light.png)

![emaillist-manage-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-manage-desktop-dark.png)

![emaillist-manage-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-manage-desktop-light.png)

![emaillist-manage-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-manage-phone-dark.png)

![emaillist-manage-phone-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-manage-phone-light.png)

![emaillist-owner-home-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-owner-home-desktop-dark.png)

![emaillist-owner-home-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-owner-home-desktop-light.png)

![emaillist-owner-home-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-owner-home-phone-dark.png)

![emaillist-owner-home-phone-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-owner-home-phone-light.png)

![emaillist-owner-mailing-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-owner-mailing-desktop-dark.png)

![emaillist-owner-mailing-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-owner-mailing-desktop-light.png)

![emaillist-owner-mailing-form-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-owner-mailing-form-desktop-dark.png)

![emaillist-owner-mailing-form-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-owner-mailing-form-desktop-light.png)

![emaillist-owner-mailing-form-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-owner-mailing-form-phone-dark.png)

![emaillist-owner-mailing-form-phone-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-owner-mailing-form-phone-light.png)

![emaillist-owner-mailing-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-owner-mailing-phone-dark.png)

![emaillist-owner-mailing-phone-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-owner-mailing-phone-light.png)

![emaillist-sign-up-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-sign-up-desktop-dark.png)

![emaillist-sign-up-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-sign-up-desktop-light.png)

![emaillist-sign-up-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-sign-up-phone-dark.png)

![emaillist-sign-up-phone-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-sign-up-phone-light.png)

![emaillist-unsubscribe-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-unsubscribe-desktop-dark.png)

![emaillist-unsubscribe-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-unsubscribe-desktop-light.png)

![emaillist-unsubscribe-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-unsubscribe-phone-dark.png)

![emaillist-unsubscribe-phone-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-unsubscribe-phone-light.png)

![emaillist-unsubscribed-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-unsubscribed-desktop-dark.png)

![emaillist-unsubscribed-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-unsubscribed-desktop-light.png)

![emaillist-unsubscribed-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-unsubscribed-phone-dark.png)

![emaillist-unsubscribed-phone-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-unsubscribed-phone-light.png)

**Summary**

> Phase 8: a new `apps/emaillist` app holds an in-house marketing email list. Amazon SES is the recommended sending service; nothing was signed up for.
> - **Sign-up:** opt-in only. Visitors join from the "Email news" page, linked in every page's footer, and pick weekly, every two weeks or monthly (monthly is preselected). A confirmation email follows, and the page gives the same answer whether or not the address is already on the list. It uses the same bot checks as checkout, plus a limit of 3 confirmation emails per address per hour.
> - **Consent records:** each step is recorded and can't be changed or deleted: asked to join (with the exact words the form showed), confirmed, changed frequency, unsubscribed, or removed by the owner. Each record keeps the time, the visitor's IP address and browser.
> - **Mailings:** the owner writes a draft and previews it as a subscriber sees it, then approves it. AI agents can draft but cannot approve, and approval is refused until the postal address is set. Approved mailings go to each subscriber no more often than they chose; several waiting mailings are combined into one email with an honest combined subject ("X, and 2 more updates"). Old mailings are not sent to new subscribers, a mailing can be withdrawn, and it can have a last day it may be sent.
> - **Legal requirements:** every mailing has the postal address, a reason line, links to change frequency and to unsubscribe, and List-Unsubscribe / List-Unsubscribe-Post headers. Mail apps' one-click unsubscribe works without a CSRF token, and unsubscribe links keep working even while the shop is closed. Mailings can go through their own SMTP host (`EMAIL_LIST_EMAIL_*`).
> - **Jobs and dashboard:** each recipient's email is its own `apps.jobs` job with a key. A daily `jobs.schedule` run at 10:00 sends to subscribers who are due, and approving a mailing also sends at once to those due. Through the attention registry, each draft is an "approvals" item, and stuck emails or a missing postal address are "problems" items.
> - **Docs and settings:** new `docs/emaillist.md` covers the provider comparison and SES/SPF/DKIM/DMARC setup steps; architecture.md, jobs.md, `.env.example`, compose.yaml, settings and urls are updated.
> - **Tests:** 39 tests pass, including browser tests with axe on the sign-up, confirm, manage and unsubscribe pages and the owner pages. Milestone screenshots are in `doc/shots/2026-11-01-phase8-email-list`.


### T8 phase6-owner-dashboard-reporting

- **Origin:** Filed by the Tasks Manager from the plan of T1 see-file-teashop-txt, at the user's request
- **Goal:** Planning
- **Ran:** 2026-11-01 20:43 to 2026-11-01 21:06 (21m 34s)
- **Outcome:** done; committed [`ccc52ca8f8f1`](https://github.com/wingware-dev/teashop/commit/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402) (shared with T10 phase8-email-list)
- **Usage:** 234 input, 119k output, 21.38M cache read, 284k cache write (claude-opus-5-5)
- **Tools:** 195 calls, 56 to Wing's MCP tools (wing-review 48, wing-testing 8)

**Prompt**

> Phase 6: owner dashboard and reporting
>
> From the report of T1 see-file-teashop-txt (6f896717), section (c) Phase 6 and sections 'General automation and the owner dashboard' and '(4) Business reporting, accounting and payroll'. Full report: .TASKS/notes/see-the-file-teashop-txt-for-a-description-of-the-project.md
>
> Scope (2-3 weeks): a single 'needs your attention' queue for posts to approve, purchase orders, refunds, support escalations, low stock and failed jobs. Each kind has its own deadline, and an overdue item sends a reminder email. The user's starting deadlines: support is immediate, orders once a day at 6pm, others as makes sense. Also: sales reports by period, product, category and channel; cost of goods sold, gross margin, inventory value and loss; an automatic daily summary entry sent to Wave (the user's accounting choice) by API; reports for NY sales-tax filing and for quarterly estimated income tax (the user is a sole proprietor taking owner's draws, so no payroll yet).
>
> Screenshots into doc/shots; WCAG 2.2 AA checks.
>
> [Tasks Manager, 2026-11-01 18:19] From T2 phase1-infrastructure-skeleton (edd0e993): the owner dashboard already exists in apps/core (views.owner_dashboard, templates/core/owner_dashboard.html), with a placeholder 'Needs your attention' section and recent audit events. Extend it there or move it into a dashboard app. Follow docs/architecture.md.
>
> [Tasks Manager, 2026-11-01 18:31] From T15 record-ops-events (29373a71): move the failed or overdue ops items out of owner_dashboard.html and into an attention provider registered in AuditConfig.ready(). apps.audit.ops.ops_status already computes needs_attention. Use the attention registry in apps/core/attention.py (from T4 phase2-catalog-inventory-core (4d8a1a2b)) once the dashboard calls collect().
>
> [Tasks Manager, 2026-11-01 18:52] From T9 phase7-purchasing-loss-tracking (ca29736e): this task also needs to (1) add per-order shipping charged, postage paid and Stripe fees, recorded by checkout, to the profit report in apps/purchasing, so margin is per order rather than landed cost only; and (2) send the daily reminder email to cover items at their reorder level and draft purchase orders waiting for approval.
>
> [Tasks Manager, 2026-11-01 20:42] Manager, from T29 background-job-queue (e7891f25): add the daily owner reminder as a schedule in the app's jobs.py, using `@jobs.job` plus `jobs.schedule(fn, daily_at="HH:MM")` as docs/jobs.md describes. Don't add a systemd timer. Send its email with `apps.checkout.emails.send_now` inside a job. "Failed jobs" in the attention queue come from apps.jobs. Refund figures should use the per-refund taxable and tax amounts from T44 refund-records-tax (f01fa3bc). T10 (email list) may run at the same time, so keep apps/marketing (or whatever T10 names its app) out of this task. Wave has no account yet: build the Wave export against a stand-in client, and don't call Wave's API.
>
> See \<project>/.TASKS/notes/phase-6-owner-dashboard-and-reporting.md

**Judgement calls**

1. **Put the reports, reminders and Wave export in a new `reports` app; the dashboard view stays in core**
   core can't send email (that needs checkout's `send_now`). Keeping the view and URL in core avoids renaming `core:owner_dashboard`, which many templates and tests use. The clock for each item (`AttentionRecord`) lives in core so the dashboard can show due and overdue times.
   Alternatives: Move the dashboard view into a new dashboard app
2. **Orders are reminded only by the existing 6pm order summary, not by a second email**
   You asked for orders once a day at 6pm, and fulfillment's 6pm summary already does that. A second email at 6pm would repeat it.
   Alternatives: Send a separate attention email for orders at 6pm
3. **The daily reminder goes out at 8am; overdue items get one email each, then appear in every daily reminder**
   A morning list of everything waiting suits stock and purchase orders. Re-emailing overdue items every few minutes would be noise.
   Alternatives: Daily reminder at 6pm alongside the order summary; Repeat overdue emails every N hours
4. **Started-out deadlines: refunds 4h, broken things and failed jobs 1h, approvals 3 days, the rest daily**
   You said 'others as makes sense'. All can be changed with ATTENTION_DEADLINES.
5. **Wave gets one deposit per day on the Stripe clearing account; inventory purchases are listed but not posted**
   Supplier payments reach Wave through its bank feed, so posting them too would count them twice. Stock received still shows on the Wave page for reference.
   Alternatives: Post inventory purchases as a second transaction
6. **Wrote a real client for Wave's API (GraphQL `moneyTransactionCreate`), tested only against a fake HTTP session; it stays off (WAVE_CLIENT=fake)**
   Wave has no account yet, and the instructions were not to call its API. The client is there for when you connect, and docs/reports.md says to check the first posted day in Wave.
7. **Stripe fees: the fee Stripe reports, read by a job a few minutes after payment; until then, and for the stand-in payments, an estimate at 2.9% + 30¢ that the reports mark as estimated**
   Stripe settles the fee after the payment, and margin per order needs a figure even before then.
8. **The estimated-tax page uses placeholder income-tax rates (12% federal, 5.5% NY, both settings) and is labelled a set-aside guide**
   Your actual brackets depend on income outside the shop.
9. **Sales are counted when paid, refunds when given, and cost of goods when packed**
   This matches the existing nexus and tax reports and NY's rule that a refund counts in the period it is given.

**Findings filed**

- T51 ny-tax-table-calendar-quarters: Checkout's NY sales tax table uses calendar quarters, not New York's filing quarters

**Screenshots**

![account-security-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/account-security-desktop-dark.png)

![account-security-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/account-security-desktop-light.png)

![account-security-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/account-security-phone-dark.png)

![account-security-phone-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/account-security-phone-light.png)

![login-code-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/login-code-desktop-dark.png)

![login-code-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/login-code-desktop-light.png)

![login-code-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/login-code-phone-dark.png)

![login-code-phone-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/login-code-phone-light.png)

![login-password-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/login-password-desktop-dark.png)

![login-password-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/login-password-desktop-light.png)

![login-password-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/login-password-phone-dark.png)

![login-password-phone-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/login-password-phone-light.png)

![login-wrong-code-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/login-wrong-code-desktop-light.png)

![owner-dashboard-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/owner-dashboard-desktop-dark.png)

![owner-dashboard-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/owner-dashboard-desktop-light.png)

![owner-dashboard-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/owner-dashboard-phone-dark.png)

![owner-dashboard-phone-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/owner-dashboard-phone-light.png)

![owner-dashboard-queue-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/owner-dashboard-queue-desktop-dark.png)

![owner-dashboard-queue-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/owner-dashboard-queue-desktop-light.png)

![owner-dashboard-queue-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/owner-dashboard-queue-phone-dark.png)

![owner-dashboard-queue-phone-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/owner-dashboard-queue-phone-light.png)

![purchasing-profit-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/purchasing-profit-desktop-dark.png)

![purchasing-profit-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/purchasing-profit-desktop-light.png)

![purchasing-profit-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/purchasing-profit-phone-dark.png)

![purchasing-profit-phone-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/purchasing-profit-phone-light.png)

![reports-accounting-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/reports-accounting-desktop-dark.png)

![reports-accounting-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/reports-accounting-desktop-light.png)

![reports-accounting-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/reports-accounting-phone-dark.png)

![reports-accounting-phone-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/reports-accounting-phone-light.png)

![reports-estimated-tax-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/reports-estimated-tax-desktop-dark.png)

![reports-estimated-tax-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/reports-estimated-tax-desktop-light.png)

![reports-estimated-tax-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/reports-estimated-tax-phone-dark.png)

![reports-estimated-tax-phone-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/reports-estimated-tax-phone-light.png)

![reports-margin-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/reports-margin-desktop-dark.png)

![reports-margin-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/reports-margin-desktop-light.png)

![reports-margin-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/reports-margin-phone-dark.png)

![reports-margin-phone-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/reports-margin-phone-light.png)

![reports-sales-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/reports-sales-desktop-dark.png)

![reports-sales-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/reports-sales-desktop-light.png)

![reports-sales-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/reports-sales-phone-dark.png)

![reports-sales-phone-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/reports-sales-phone-light.png)

![reports-sales-tax-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/reports-sales-tax-desktop-dark.png)

![reports-sales-tax-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/reports-sales-tax-desktop-light.png)

![reports-sales-tax-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/reports-sales-tax-phone-dark.png)

![reports-sales-tax-phone-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase6-reports/reports-sales-tax-phone-light.png)

![emaillist-confirm-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-confirm-desktop-dark.png)

![emaillist-confirm-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-confirm-desktop-light.png)

![emaillist-confirm-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-confirm-phone-dark.png)

![emaillist-confirm-phone-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-confirm-phone-light.png)

![emaillist-flow-check-email-phone-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-flow-check-email-phone-light.png)

![emaillist-flow-confirmed-phone-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-flow-confirmed-phone-light.png)

![emaillist-flow-frequency-saved-phone-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-flow-frequency-saved-phone-light.png)

![emaillist-flow-unsubscribed-phone-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-flow-unsubscribed-phone-light.png)

![emaillist-manage-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-manage-desktop-dark.png)

![emaillist-manage-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-manage-desktop-light.png)

![emaillist-manage-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-manage-phone-dark.png)

![emaillist-manage-phone-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-manage-phone-light.png)

![emaillist-owner-home-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-owner-home-desktop-dark.png)

![emaillist-owner-home-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-owner-home-desktop-light.png)

![emaillist-owner-home-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-owner-home-phone-dark.png)

![emaillist-owner-home-phone-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-owner-home-phone-light.png)

![emaillist-owner-mailing-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-owner-mailing-desktop-dark.png)

![emaillist-owner-mailing-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-owner-mailing-desktop-light.png)

![emaillist-owner-mailing-form-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-owner-mailing-form-desktop-dark.png)

![emaillist-owner-mailing-form-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-owner-mailing-form-desktop-light.png)

![emaillist-owner-mailing-form-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-owner-mailing-form-phone-dark.png)

![emaillist-owner-mailing-form-phone-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-owner-mailing-form-phone-light.png)

![emaillist-owner-mailing-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-owner-mailing-phone-dark.png)

![emaillist-owner-mailing-phone-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-owner-mailing-phone-light.png)

![emaillist-sign-up-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-sign-up-desktop-dark.png)

![emaillist-sign-up-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-sign-up-desktop-light.png)

![emaillist-sign-up-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-sign-up-phone-dark.png)

![emaillist-sign-up-phone-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-sign-up-phone-light.png)

![emaillist-unsubscribe-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-unsubscribe-desktop-dark.png)

![emaillist-unsubscribe-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-unsubscribe-desktop-light.png)

![emaillist-unsubscribe-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-unsubscribe-phone-dark.png)

![emaillist-unsubscribe-phone-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-unsubscribe-phone-light.png)

![emaillist-unsubscribed-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-unsubscribed-desktop-dark.png)

![emaillist-unsubscribed-desktop-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-unsubscribed-desktop-light.png)

![emaillist-unsubscribed-phone-dark.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-unsubscribed-phone-dark.png)

![emaillist-unsubscribed-phone-light.png](https://github.com/wingware-dev/teashop/raw/ccc52ca8f8f1eae6ca2efb5168fdcf0a764b8402/doc/shots/2026-11-01-phase8-email-list/emaillist-unsubscribed-phone-light.png)

**Summary**

> Phase 6: the owner dashboard's attention queue now has a deadline per kind of item and sends reminder emails, and a new reports app has sales, margin and tax reports plus a nightly summary for Wave.
> - Queue: each item has a kind, a key and a start time (`apps/core/attention.py`, `core.AttentionRecord`). The dashboard groups items by kind and shows when each is due or overdue. Default deadlines: support at once, refunds 4h, broken things and failed jobs 1h, orders at the 6pm order summary, approvals 3 days, and stock, purchase orders and the rest in the daily reminder. They can be changed with `ATTENTION_DEADLINES`. Every app's alerts now set a kind and key. The ops failures (backups, deploys) moved out of the template into a provider registered in `AuditConfig.ready()`.
> - Reminders (`apps/reports/jobs.py`): an overdue check every 5 minutes and a daily reminder at 8am. Both send with `send_now` inside a job. The daily one covers low stock, items at their reorder level and draft purchase orders.
> - Reports at `/owner/reports/`: sales by period, channel, category and product; cost of goods sold, gross margin, postage, fees, loss, samples and stock value; the NY sales-tax return by NY's own quarters (or the annual year) and by jurisdiction, net of each refund's own taxable amount and tax; and quarterly estimated income tax (self-employment tax plus income tax set-asides).
> - Wave: each day is posted once as a deposit to the Stripe clearing account. It runs against a stand-in client by default; Wave's API is never called.
> - Per-order profit: the purchasing profit page now has a "Per order" table (shipping charged, refunds, goods cost, postage paid, Stripe fee). Checkout stores Stripe's fee on each order (`Order.payment_fee`) through a job that runs after payment.
> - Docs: new `docs/reports.md`; updated architecture, jobs and `.env.example`. Screenshots are in `doc/shots/2026-11-01-phase6-reports`; all browser tests, including the WCAG 2.2 AA checks, passed.


### T51 ny-tax-table-calendar-quarters

- **Origin:** Found by T8 phase6-owner-dashboard-reporting
- **Goal:** Bug Fixes
- **Ran:** 2026-11-01 21:07 to 2026-11-01 21:08 (1m 36s)
- **Outcome:** done; committed [`10287803ff84`](https://github.com/wingware-dev/teashop/commit/10287803ff848255709684a912aa6e006a619ce3)
- **Usage:** 2,669 input, 8,869 output, 4.96M cache read, 16k cache write (claude-haiku-5-5, claude-opus-5-5)
- **Tools:** 20 calls, 4 to Wing's MCP tools (wing-review 2, wing-testing 2)

**Prompt**

> Checkout's NY sales tax table uses calendar quarters, not New York's filing quarters
>
> apps/checkout/nexus.py ny_tax_by_quarter() (shown on /owner/checkout/sales-by-state/ as "New York sales tax collected") groups by calendar quarters Jan-Mar, Apr-Jun, ... But New York's quarterly sales tax periods run Mar-May, Jun-Aug, Sep-Nov and Dec-Feb (annual: Mar-Feb). Someone filing from that table would report the wrong figures. The new reports app (apps/reports/taxes.py, /owner/reports/sales-tax/) has the NY periods and jurisdiction breakdown. Fix: either regroup that table by NY quarters (reuse apps.reports.taxes.ny_quarter is not possible without checkout importing reports; move ny_quarter into checkout/nexus.py and have reports use it), or drop the table and link to the reports page.
>
> Evidence: apps/checkout/nexus.py ny_tax_by_quarter: start = date(year, quarter * 3 + 1, 1); apps/checkout/templates/checkout/owner/sales_by_state.html says "File from these figures".
>
> Suggested next step: fix

**Judgement calls**

1. **Kept the table and regrouped it, rather than dropping it for a link**
   It is a quick glance at the last four quarters next to the nexus figures; the full return breakdown stays in the reports page, which it now links to.
   Alternatives: Drop the table and only link to /owner/reports/sales-tax/
2. **The table shows the last four NY quarters up to today rather than one calendar year**
   NY quarters cross the year boundary (Dec–Feb), so a per-year view no longer fits.
3. **Moved one test's dates (cancelled order Feb 27, refund Mar 2)**
   Its old dates (Mar 30 / Apr 2) were in different calendar quarters but fall in the same NY quarter, so the test no longer checked the split it was written for.

**Summary**

> Checkout's "New York sales tax collected" table now groups by New York's filing quarters (Mar–May, Jun–Aug, Sep–Nov, Dec–Feb), each with its due date, instead of calendar quarters.
> - `ny_quarter`, `ny_quarters` and `Period` moved into `apps/checkout/nexus.py`, and the reports app now imports them, so the two pages share one definition.
> - `ny_tax_by_quarter(today, count=4)` returns the last four NY quarters, and the page links to the full NY sales tax return report.
> - Updated the checkout tests to NY quarters and added one that pins the period boundaries (Feb 28 and Mar 1 fall in different quarters; the due date is the 20th).


### T11 phase9-support-agent

- **Origin:** Filed by the Tasks Manager from the plan of T1 see-file-teashop-txt, at the user's request
- **Goal:** Planning
- **Ran:** 2026-11-01 21:07 to 2026-11-01 21:31 (23m 10s)
- **Outcome:** done; committed [`1adcd0719e2a`](https://github.com/wingware-dev/teashop/commit/1adcd0719e2a37121eee0fa188262c7948f8409e)
- **Usage:** 2,350 input, 122k output, 14.22M cache read, 239k cache write (claude-haiku-5-5, claude-opus-5-5)
- **Tools:** 116 calls, 59 to Wing's MCP tools (wing-review 56, wing-testing 3)

**Prompt**

> Phase 9: customer support agent
>
> From the report of T1 see-file-teashop-txt (6f896717), section (c) Phase 9 and section 'General automation and the owner dashboard'. Full report: .TASKS/notes/see-the-file-teashop-txt-for-a-description-of-the-project.md
>
> Scope (3-4 weeks): chat widget and email inbox; the agent runs around the clock (the user's choice) but answers only clear-cut questions (order status, brewing advice, shipping times) using read-only tools for order lookup, tracking and the catalog. Otherwise it tells the customer 'we'll get back to you' and escalates to the owner dashboard immediately. Watch mode first: the agent drafts, the user edits and sends, and it learns the user's voice from those edits; it then answers routine categories alone as the user's approval rate shows it is ready.
>
> Guardrails (Part 2): label it clearly as an 'AI assistant' in chat and in AI-sent emails (California BOT Act); no health or disease claims; no refunds or spending without approval; a monthly AI spending cap; every action logged; treat incoming chats and emails as untrusted input that may try to manipulate the agent.
>
> Open question: whether the user's $100/month Claude Code subscription terms allow running production agents, or whether separate API billing (about $20-100/month) is needed. Develop and test with stand-ins; do not call a live AI API without the user's approval.
>
> [Tasks Manager, 2026-11-01 21:06] Manager, from T8 phase6-owner-dashboard-reporting (836f1839, committing now): register an attention provider with kind="support" in apps/core/attention.py, using the kind/key/since fields, so the dashboard's reminder emails escalations at once. Queue the agent's emails and inbox polling with apps.jobs (docs/jobs.md), not systemd. Log agent actions with apps.audit `acting_as_agent`. Agents can't refund or cancel orders: apps/fulfillment already refuses those.
>
> See \<project>/.TASKS/notes/phase-9-customer-support-agent.md

**Questions**

1. The support agent for the tea shop runs on an offline stand-in until it is given a Claude API key. My understanding is that a Claude Pro/Max subscription (the $100/month one used for Claude Code) covers a person using Claude, not a program answering customers around the clock, so a separate Anthropic API account billed per token is needed (about $20-100/month at small volume; the code caps it at $50/month by default). Please check Anthropic's current terms. How do you want to proceed?
   - Options: Set up an Anthropic API account later myself; keep the stand-in for now; Set up an API account now and approve one short live test of the support agent (a few chat questions, well under $1); Keep only the stand-in until launch; revisit then
   - **Unanswered**

**Judgement calls**

1. **Only the owner can switch a category to answering alone; the agent never switches itself** (report 1)
   The task says it answers alone 'as the approval rate shows it is ready'. Letting it switch itself would put a customer-facing change outside the owner's control, so the dashboard and support page offer the switch once the rate qualifies, and agents are refused in code.
   Alternatives: Switch automatically once the rate passes the threshold
2. **Readiness: 90% of the last 20 decided drafts sent with ≥90% of words unchanged** (report 1)
   Gives a clear, adjustable bar (SUPPORT_READY_RATE, SUPPORT_READY_MIN_DRAFTS). Discarded drafts count against; drafts replaced by a newer customer message don't count either way.
   Alternatives: Exact-match only; Fewer drafts (e.g. 10)
3. **Drafts the owner sends carry no 'AI assistant' label; anything the agent sends on its own always does** (report 1)
   A reply a person reads, edits and sends is the person's. The BOT Act concerns bots talking unattended. Automated notices ('we'll get back to you', the watch-mode acknowledgement) are labelled too.
   Alternatives: Label AI-drafted replies even after owner approval
4. **Deterministic screening escalates refunds, damage, health, allergy, discount and similar topics before any AI call** (report 1)
   It is cheap, it can't be talked around, and it keeps the agent to clear-cut questions. The cost is that some harmless messages ('returning customer') go to the owner.
   Alternatives: Let the model classify everything
5. **Chat requires an email; order lookup needs both the order number and the matching email** (report 1)
   Lets the owner reply after the customer leaves, and stops one customer reading another's order with only a guessed number. No address or payment data is ever given to the agent.
   Alternatives: Order number alone; Verify the email by link before lookups
6. **Live mode is per agent (AGENTS_LIVE) and calls the API with requests, without adding the anthropic SDK** (report 1)
   Means T12 and T13 stay on stand-ins until each is approved, and avoids a new dependency. The default model is claude-haiku-5-5 at an assumed $1/$5 per million tokens (AGENTS_PRICE_PER_MTOK), which must be checked against Anthropic's price list.
   Alternatives: One global switch; Use the anthropic Python SDK
7. **Message bodies are left out of the model-change audit log; support.\* events record each message instead** (report 1)
   Avoids copying every customer message into the append-only log twice, while every action is still logged.
   Alternatives: Audit message bodies too
8. **Default monthly AI cap $50** (report 1)
   Within the report's $20-100/month estimate; change it with AGENTS_MONTHLY_CAP.
   Alternatives: $100
9. **Milestone shots limited to apps.support.tests.test_ui (24 shots)** (report 2)
   The Tasks Manager asked for support pages only; milestone_shots accepts test labels, so the rest of the project's browser tests were not re-run.
   Alternatives: Full milestone_shots run

**Screenshots**

![agents-owner-home-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/1adcd0719e2a37121eee0fa188262c7948f8409e/doc/shots/2026-11-01-phase9-support/agents-owner-home-desktop-dark.png)

![agents-owner-home-desktop-light.png](https://github.com/wingware-dev/teashop/raw/1adcd0719e2a37121eee0fa188262c7948f8409e/doc/shots/2026-11-01-phase9-support/agents-owner-home-desktop-light.png)

![agents-owner-home-phone-dark.png](https://github.com/wingware-dev/teashop/raw/1adcd0719e2a37121eee0fa188262c7948f8409e/doc/shots/2026-11-01-phase9-support/agents-owner-home-phone-dark.png)

![agents-owner-home-phone-light.png](https://github.com/wingware-dev/teashop/raw/1adcd0719e2a37121eee0fa188262c7948f8409e/doc/shots/2026-11-01-phase9-support/agents-owner-home-phone-light.png)

![support-chat-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/1adcd0719e2a37121eee0fa188262c7948f8409e/doc/shots/2026-11-01-phase9-support/support-chat-desktop-dark.png)

![support-chat-desktop-light.png](https://github.com/wingware-dev/teashop/raw/1adcd0719e2a37121eee0fa188262c7948f8409e/doc/shots/2026-11-01-phase9-support/support-chat-desktop-light.png)

![support-chat-phone-dark.png](https://github.com/wingware-dev/teashop/raw/1adcd0719e2a37121eee0fa188262c7948f8409e/doc/shots/2026-11-01-phase9-support/support-chat-phone-dark.png)

![support-chat-phone-light.png](https://github.com/wingware-dev/teashop/raw/1adcd0719e2a37121eee0fa188262c7948f8409e/doc/shots/2026-11-01-phase9-support/support-chat-phone-light.png)

![support-chat-start-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/1adcd0719e2a37121eee0fa188262c7948f8409e/doc/shots/2026-11-01-phase9-support/support-chat-start-desktop-dark.png)

![support-chat-start-desktop-light.png](https://github.com/wingware-dev/teashop/raw/1adcd0719e2a37121eee0fa188262c7948f8409e/doc/shots/2026-11-01-phase9-support/support-chat-start-desktop-light.png)

![support-chat-start-phone-dark.png](https://github.com/wingware-dev/teashop/raw/1adcd0719e2a37121eee0fa188262c7948f8409e/doc/shots/2026-11-01-phase9-support/support-chat-start-phone-dark.png)

![support-chat-start-phone-light.png](https://github.com/wingware-dev/teashop/raw/1adcd0719e2a37121eee0fa188262c7948f8409e/doc/shots/2026-11-01-phase9-support/support-chat-start-phone-light.png)

![support-flow-chat-answered-phone-light.png](https://github.com/wingware-dev/teashop/raw/1adcd0719e2a37121eee0fa188262c7948f8409e/doc/shots/2026-11-01-phase9-support/support-flow-chat-answered-phone-light.png)

![support-flow-chat-waiting-phone-light.png](https://github.com/wingware-dev/teashop/raw/1adcd0719e2a37121eee0fa188262c7948f8409e/doc/shots/2026-11-01-phase9-support/support-flow-chat-waiting-phone-light.png)

![support-flow-owner-edits-desktop-light.png](https://github.com/wingware-dev/teashop/raw/1adcd0719e2a37121eee0fa188262c7948f8409e/doc/shots/2026-11-01-phase9-support/support-flow-owner-edits-desktop-light.png)

![support-flow-owner-sent-desktop-light.png](https://github.com/wingware-dev/teashop/raw/1adcd0719e2a37121eee0fa188262c7948f8409e/doc/shots/2026-11-01-phase9-support/support-flow-owner-sent-desktop-light.png)

![support-owner-conversation-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/1adcd0719e2a37121eee0fa188262c7948f8409e/doc/shots/2026-11-01-phase9-support/support-owner-conversation-desktop-dark.png)

![support-owner-conversation-desktop-light.png](https://github.com/wingware-dev/teashop/raw/1adcd0719e2a37121eee0fa188262c7948f8409e/doc/shots/2026-11-01-phase9-support/support-owner-conversation-desktop-light.png)

![support-owner-conversation-phone-dark.png](https://github.com/wingware-dev/teashop/raw/1adcd0719e2a37121eee0fa188262c7948f8409e/doc/shots/2026-11-01-phase9-support/support-owner-conversation-phone-dark.png)

![support-owner-conversation-phone-light.png](https://github.com/wingware-dev/teashop/raw/1adcd0719e2a37121eee0fa188262c7948f8409e/doc/shots/2026-11-01-phase9-support/support-owner-conversation-phone-light.png)

![support-owner-inbox-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/1adcd0719e2a37121eee0fa188262c7948f8409e/doc/shots/2026-11-01-phase9-support/support-owner-inbox-desktop-dark.png)

![support-owner-inbox-desktop-light.png](https://github.com/wingware-dev/teashop/raw/1adcd0719e2a37121eee0fa188262c7948f8409e/doc/shots/2026-11-01-phase9-support/support-owner-inbox-desktop-light.png)

![support-owner-inbox-phone-dark.png](https://github.com/wingware-dev/teashop/raw/1adcd0719e2a37121eee0fa188262c7948f8409e/doc/shots/2026-11-01-phase9-support/support-owner-inbox-phone-dark.png)

![support-owner-inbox-phone-light.png](https://github.com/wingware-dev/teashop/raw/1adcd0719e2a37121eee0fa188262c7948f8409e/doc/shots/2026-11-01-phase9-support/support-owner-inbox-phone-light.png)

**Summary**

> Phase 9, customer support agent: a shared AI-agents app that the marketing and ops agents (T12, T13) can reuse, and the support app with a chat, an email inbox, watch mode and escalations. It runs on a free offline stand-in; no live AI API was called.
> - apps/agents (shared, documented in docs/agents.md): the AI client interface with a Claude API client and offline stand-ins. An agent calls the live API only if named in AGENTS_LIVE. Also: the monthly spending cap (AGENTS_MONTHLY_CAP, AIUsage rows, dashboard warning at 80%), the 'AI assistant' label for chat and email (California BOT Act), untrusted-input handling (random-id fences, invisible-character removal, injection detection), checks on what agents write (health claims, refund or discount promises, outside links, requests for card numbers), an audited tool loop credited via acting_as_agent, and an owner page at owner/agents/ showing spending and recent agent actions.
> - apps/support (documented in docs/support.md): a chat at /help/chat/ ('Chat with us' in the footer) that polls for replies and works without JavaScript. The IMAP inbox is polled by an apps.jobs schedule; it skips auto-replies, bounces and mailing lists, threads replies and drops quoted text. The agent has read-only tools: order lookup (needs the order number and the email on the order), parcel tracking, catalog and brewing facts, shipping facts.
> - Before any AI call, screening hands to the owner: manipulation attempts, requests for a person, judgement topics (refunds, damage, health, allergies…) and floods. The customer is told 'we'll get back to you', and an attention item of kind 'support' triggers the owner's reminder at once.
> - Watch mode: drafts go to the owner, who edits and sends them. Recent edits are shown to the agent as examples of the owner's voice, and the approval rate per category (90% of the last 20 drafts sent with small or no edits) unlocks 'Let it answer alone'.
> - Owner pages: support inbox, conversation with the draft in the reply box, discard, close, and per-category mode. Plus settings, .env.example and compose.yaml entries, the architecture and jobs docs, migrations, and 78 tests including browser tests (WCAG checks, screenshots reviewed).
> - Phase 9 milestone screenshots (support and agents pages only) recorded in doc/shots/2026-11-01-phase9-support.


### T55 regression-sweep-shop-pages

- **Origin:** Filed by the Tasks Manager
- **Goal:** Planning
- **Ran:** 2026-11-01 21:31 to 2026-11-01 21:35 (3m 43s)
- **Outcome:** done
- **Usage:** 1,767 input, 1,273 output, 198k cache read, 19k cache write (claude-haiku-5-5, claude-opus-5-5)
- **Tools:** 6 calls, 5 to Wing's MCP tools (wing-review 3, wing-testing 2)

**Prompt**

> Regression tests for phases 5-8: shop-facing apps
>
> A sweep under wing_guide topic 'research'. Covers the work committed since the last sweep: T7, T25, T29, T30, T31, T34, T35, T41, T42, T44, T8, T10 and T51. Make one test_run per batch, with these specs:
> 1. apps/checkout/tests
> 2. apps/storefront/tests and apps/emaillist/tests
> File each failure with report_finding (next_step fix), with the test name, error and likely cause. Don't fix anything.
>
> See \<project>/.TASKS/notes/regression-tests-for-phases-5-8-shop-facing-apps.md

**Summary**

> Regression sweep of the shop-facing apps (phases 5-8: T7, T25, T29, T30, T31, T34, T35, T41, T42, T44, T8, T10, T51) found no failures, so no findings were filed and nothing was changed.
> - Batch 1, apps/checkout/tests: all 145 passed (73.1s, run 1793586687867)
> - Batch 2, apps/storefront/tests + apps/emaillist/tests: all 110 passed (128.1s, run 1793586763311)


### T56 regression-sweep-backend

- **Origin:** Filed by the Tasks Manager
- **Goal:** Planning
- **Ran:** 2026-11-01 21:35 to 2026-11-01 21:38 (3m 02s)
- **Outcome:** done
- **Usage:** 1,808 input, 3,779 output, 244k cache read, 25k cache write (claude-haiku-5-5, claude-opus-5-5)
- **Tools:** 10 calls, 7 to Wing's MCP tools (wing-review 4, wing-testing 3)

**Prompt**

> Regression tests for phases 5-8: backend apps
>
> A sweep under wing_guide topic 'research'. Covers the work committed since the last sweep: T7, T25, T29, T30, T31, T34, T35, T41, T42, T44, T8, T10 and T51. Make one test_run per batch, with these specs:
> 1. apps/core/tests, apps/audit and apps/jobs/tests
> 2. apps/fulfillment/tests, apps/reports/tests, apps/catalog/tests, apps/inventory/tests and apps/purchasing
> File each failure with report_finding (next_step fix), with the test name, error and likely cause. Don't fix anything.
>
> See \<project>/.TASKS/notes/regression-tests-for-phases-5-8-backend-apps.md

**Verdict:** Check found issues; filed T60 compose-missing-phase6-env-vars

- T60 compose-missing-phase6-env-vars: compose.yaml doesn't pass phase-6 dashboard/Wave/estimated-tax settings to the containers

**Summary**

> Ran the backend regression tests for phases 5-8 in two batches. Two tests failed, both from one cause, filed as one finding.
> - Batch 1 (apps/core/tests, apps/audit, apps/jobs/tests): 96 passed, 2 failed, 1 skipped.
> - Batch 2 (apps/fulfillment/tests, apps/reports/tests, apps/catalog/tests, apps/inventory/tests, apps/purchasing): all 254 passed.
> - Filed T60 compose-missing-phase6-env-vars (54ec9c85): phase 6 added nine settings to .env.example and settings.py (ATTENTION_*, WAVE_*, ESTIMATED_TAX_*) but not to compose.yaml. The owner's .env values never reach the web or worker containers, and the two ComposeEnvironmentTests in apps/core/tests/test_deploy_scripts.py fail.
> - Nothing was fixed in place.


### T60 compose-missing-phase6-env-vars

- **Origin:** Found by T56 regression-sweep-backend
- **Goal:** Bug Fixes
- **Ran:** 2026-11-01 21:38 to 2026-11-01 21:38 (0m 36s)
- **Outcome:** done; committed [`cd96d7b1a2be`](https://github.com/wingware-dev/teashop/commit/cd96d7b1a2be542f14237301e5dc0d83742526bb)
- **Usage:** 2,686 input, 3,113 output, 283k cache read, 31k cache write (claude-haiku-5-5, claude-opus-5-5)
- **Tools:** 9 calls, 4 to Wing's MCP tools (wing-review 3, wing-testing 1)

**Prompt**

> compose.yaml doesn't pass phase-6 dashboard/Wave/estimated-tax settings to the containers
>
> Phase 6 (commit ccc52ca: owner dashboard deadlines, reports, Wave summary) added nine settings to .env.example and config/settings.py, but none of them were added to the `environment: &app-environment` block of compose.yaml. In production the owner's .env values never reach the web or worker containers, so Wave sync stays on the "fake" client, and the attention deadlines and estimated-tax rates silently fall back to their defaults. Missing variables: ATTENTION_DAILY_AT, ATTENTION_DEADLINES, ESTIMATED_TAX_FEDERAL_RATE, ESTIMATED_TAX_STATE_RATE, WAVE_ACCOUNTS, WAVE_BUSINESS_ID, WAVE_CLIENT, WAVE_START_DATE, WAVE_TOKEN.
>
> Two tests fail because of this (found by sweep task T56 regression-sweep-backend (e3d36b6c)):
> - apps/core/tests/test_deploy_scripts.py::ComposeEnvironmentTests.test_django_settings_in_env_example_reach_web_container (line 185: `self.assertEqual(sorted(for_django - web_environment()), [])`, "First list contains 9 additional elements")
> - apps/core/tests/test_deploy_scripts.py::ComposeEnvironmentTests.test_every_env_example_variable_is_used_by_compose (line 198: AssertionError: Lists differ: ['ATTENTION_DAILY_AT', 'ATTENTION_DEADLINES', 'ESTIMATED_TAX_FEDERAL_RATE', 'ESTIMATED_TAX_STATE_RATE', 'WAVE_ACCOUNTS', 'WAVE_BUSINESS_ID', 'WAVE_CLIENT', 'WAVE_START_DATE', 'WAVE_TOKEN'] != [])
>
> Likely fix (high confidence): add `NAME: ${NAME:-<default>}` entries for all nine variables to compose.yaml's app-environment block, following the pattern of the existing entries. Use defaults that match settings.py, e.g. WAVE_CLIENT `fake`, ATTENTION_DAILY_AT `08:00`, ESTIMATED_TAX_FEDERAL_RATE `0.12`, ESTIMATED_TAX_STATE_RATE `0.055`, and empty for the rest. The worker shares the block through the *app-environment anchor, so it gets them too. Also check whether WAVE_API_URL (settings.py:411) should be added.
>
> Evidence: .env.example:72-85 defines the variables; config/settings.py:387-420 reads them; compose.yaml has none of them (grep finds no match). Reproduce: test_run test_specs=["apps/core/tests/test_deploy_scripts.py::ComposeEnvironmentTests"]. The failure is deterministic and doesn't depend on test order.
>
> Suggested next step: fix
>
> [Tasks Manager, 2026-11-01 21:38] Manager: also check that every variable that T10 (EMAIL_LIST_*) and T11 (AGENTS_*, SUPPORT_*) added to .env.example reaches the web and worker containers. Then run ComposeEnvironmentTests. Make no other changes.

**Judgement calls**

1. **Did not add WAVE_API_URL to compose.yaml**
   It isn't in .env.example and looks like a test/dev override with a fixed production default; the Manager said to make no other changes.
   Alternatives: Add WAVE_API_URL: ${WAVE_API_URL:-https://gql.waveapps.com/graphql/public} (and document it in .env.example)
2. **Repeated settings.py defaults (08:00, fake, 0.12, 0.055) in compose rather than empty values**
   compose.yaml's own comment notes an empty value would replace the settings.py default; e.g. an empty ESTIMATED_TAX_FEDERAL_RATE would crash Decimal().

**Summary**

> Added the nine phase-6 settings (ATTENTION_*, WAVE_*, ESTIMATED_TAX_*) to compose.yaml's shared app-environment block, so web and worker now receive them. Defaults match config/settings.py. The EMAIL_LIST_*, AGENTS_*, ANTHROPIC_API_KEY and SUPPORT_* variables in .env.example were already passed through. ComposeEnvironmentTests: 3 passed.


### T12 phase10-marketing-agent

- **Origin:** Filed by the Tasks Manager from the plan of T1 see-file-teashop-txt, at the user's request
- **Goal:** Planning
- **Ran:** 2026-11-01 21:39 to 2026-11-01 22:03 (23m 50s)
- **Outcome:** done; committed [`18ca28bc59d5`](https://github.com/wingware-dev/teashop/commit/18ca28bc59d560562241a221227b5271b4263709) (shared with T13 phase11-ops-security-agent)
- **Usage:** 2,388 input, 126k output, 20.17M cache read, 277k cache write (claude-haiku-5-5, claude-opus-5-5)
- **Tools:** 139 calls, 51 to Wing's MCP tools (wing-review 47, wing-testing 4)

**Prompt**

> Phase 10: marketing agent and tea info section
>
> From the report of T1 see-file-teashop-txt (6f896717), section (c) Phase 10 and section '(6) Marketing'. Full report: .TASKS/notes/see-the-file-teashop-txt-for-a-description-of-the-project.md
>
> Scope (2-3 weeks): an idea backlog combining the user's ideas and the agent's; drafts for posts on all the major networks (the user's answer: all of them); an approval and scheduling calendar, so nothing is posted without the user's approval of when, where and what; posting through Buffer or direct APIs where easy (Meta Graph API, Pinterest, Bluesky; X charges for API access and TikTok requires an audit); publishing to the tea info and history section; discount codes tied to campaigns; privacy-respecting analytics (Plausible or self-hosted Umami).
>
> Guardrails (Part 2): no health or disease claims; no fake reviews or testimonials; disclose free products given to reviewers or influencers; truthful claims about origin and quality; no personalised pricing.
>
> No real social accounts and no live AI calls without the user's approval; use stand-ins.
>
> [Tasks Manager, 2026-11-01 21:33] Manager, from T11 phase9-support-agent (4905724b, committed 1adcd07): build on apps/agents (docs/agents.md). It provides the AI client and stand-in, AGENTS_LIVE, the monthly cap, untrusted-input fences, output checks (health claims, refund or discount promises) and the audited tool loop. Don't duplicate any of it. The owner said (Q6) to keep the stand-in, so make no live AI calls. Approvals go in the attention registry with kind "approvals". Scheduled posting runs with apps.jobs `jobs.schedule`. Email campaigns can hand off to the email list app (apps/emaillist) instead of sending themselves. T13 runs at the same time, so keep to your own app plus small hooks in shared files.
>
> See \<project>/.TASKS/notes/phase-10-marketing-agent-and-tea-info-section.md

**Judgement calls**

1. **No Buffer integration; direct APIs for Bluesky, Meta and Pinterest, by hand for X and TikTok**
   Buffer adds a subscription and an account holding every network's access, and its public API stopped taking new apps (I couldn't verify whether a new one is open now). The publisher interface makes adding it later easy.
   Alternatives: Build a Buffer publisher
2. **Every network posts by hand by default; live posting is opt-in per network via MARKETING_POST_LIVE**
   No real accounts may be used without approval; this mirrors AGENTS_LIVE.
   Alternatives: A pretend-posting stand-in publisher
3. **Analytics script only on storefront (catalog) pages**
   Checkout, order, account, chat and email-list URLs can carry tokens or personal data; campaign sales are measured through discount codes instead.
   Alternatives: Load it on every public page
4. **Guardrail problems block approval even for the owner, except testimonials in the owner's own posts, which only warn**
   Health, disclosure and pricing rules are legal requirements; the owner may legitimately quote a real review, while the AI must never write one.
   Alternatives: Show everything as warnings to the owner
5. **Agent posts that fail the checks are saved (approval refused); agent emails that fail are held back**
   The owner sees what the agent did with posts, but the email list's own approval doesn't run these checks.
   Alternatives: Discard failing drafts
6. **A live post more than 6 hours late isn't posted, and a timeout marks the post failed instead of retrying**
   Avoids stale posts after downtime and double posts when the outcome is unknown.
   Alternatives: Always post when the worker gets to it; Retry on timeout
7. **The dashboard reminder for a post due by hand uses kind "approvals" (3-day reminder) at urgent level**
   Adding a new attention kind would mean editing core, which T13 is also changing.
   Alternatives: Add a "posts" kind with a 1-hour deadline in apps/core/attention.py

**Findings filed**

- T62 site-css-leaves-date: site.css leaves date, datetime-local and url inputs unstyled

**Summary**

> Phase 10: a marketing app (apps/marketing) built on apps/agents, with an idea backlog, the marketing agent's drafts, an approval and scheduling calendar, posting, campaigns with discount codes and cookieless analytics. Nothing is posted, published or sent without the owner's approval.
> - Idea backlog with the owner's ideas and the agent's (on request and weekly). From an idea the agent drafts one post per network (Instagram, Facebook, Pinterest, Bluesky, X, TikTok), an unpublished Tea notes article, or an email handed to the email list as a draft. It runs on the stand-in only; read-only tools, no customer data.
> - Guardrails on every post and article: no health claims (shared checks), truthful origin/organic/caffeine-free, no agent-written reviews or testimonials, required gift disclosure, no personalised prices, codes only if they are real, active, public and belong to the post's campaign, shop-only links, network limits.
> - The owner approves what, where and when together, and any edit withdraws the approval. Owner pages: backlog, idea, post, month calendar (a list on phones), campaigns with code results, article publish. Approvals go on the dashboard as kind "approvals"; posts due by hand and failed posts are listed there too.
> - Posting: a jobs.schedule sweep every 5 minutes. Bluesky, Facebook Page, Instagram and Pinterest can post through their APIs once named in MARKETING_POST_LIVE with credentials (a system check enforces this); everything else, always including X and TikTok, comes to the owner to post by hand. Retries and stale-post holdback included; no real accounts connected.
> - Campaigns: UTM-tagged links and a list of public DiscountCodes, with paid orders and revenue per campaign. Plausible or self-hosted Umami script only on catalog pages, CSP host added when on, privacy policy lists it.
> - Small hooks in shared files: settings (app, marketing block), urls, base.html, .env.example plus compose.yaml (ComposeEnvironmentTests pass), storefront privacy processors, architecture.md and jobs.md. New docs/marketing.md. 63 tests including browser/axe tests pass.


### T13 phase11-ops-security-agent

- **Origin:** Filed by the Tasks Manager from the plan of T1 see-file-teashop-txt, at the user's request
- **Goal:** Planning
- **Ran:** 2026-11-01 21:39 to 2026-11-01 22:03 (23m 13s)
- **Outcome:** done; committed [`18ca28bc59d5`](https://github.com/wingware-dev/teashop/commit/18ca28bc59d560562241a221227b5271b4263709) (shared with T12 phase10-marketing-agent)
- **Usage:** 2,355 input, 128k output, 17.14M cache read, 244k cache write (claude-haiku-5-5, claude-opus-5-5)
- **Tools:** 119 calls, 42 to Wing's MCP tools (wing-review 38, wing-testing 4)

**Prompt**

> Phase 11: ops and security agent
>
> From the report of T1 see-file-teashop-txt (6f896717), section (c) Phase 11 and section '(5) Deployment, operations, security'. Full report: .TASKS/notes/see-the-file-teashop-txt-for-a-description-of-the-project.md
>
> Scope (1-3 weeks): a non-root server account for the agent with a narrow allow-list of sudo commands; it reads logs and health, applies OS updates, rotates logs and writes health and update reports to the owner dashboard, and proposes anything larger for the user's approval. An automatic security review runs on every change, with dependency alerts (pip-audit, Dependabot), plus a quarterly review checklist and an outside vulnerability scan.
>
> No access to a real server and no live AI calls without the user's approval.
>
> [Tasks Manager, 2026-11-01 18:19] From T2 phase1-infrastructure-skeleton (edd0e993): deploy/server/harden.sh creates the server accounts (admin with sudo, and deploy with Docker access). The agent's limited account and its sudo allow-list still need to be added there. Agent actions should run inside apps.audit.acting_as_agent(...). Follow docs/architecture.md.
>
> [Tasks Manager, 2026-11-01 21:33] Manager, from T11 phase9-support-agent (4905724b, committed 1adcd07): build on apps/agents (docs/agents.md) for the AI client and stand-in, the monthly cap, untrusted-input handling and the audited tool loop. The owner said (Q6) to keep the stand-in, so make no live AI calls. Server checks run as apps.jobs schedules. Report health and update results through the attention registry and the dashboard's Operations card, alongside apps.audit.ops. CI already runs pip-audit from requirements-ci.lock. T12 runs at the same time, so keep to your own app, deploy/ and the CI files.
>
> See \<project>/.TASKS/notes/phase-11-ops-and-security-agent.md

**Judgement calls**

1. **The worker reaches the server over SSH with a key locked to one command**
   The Manager said server checks run as apps.jobs schedules, but jobs run inside a container that can't touch the host. A key that can only run teashop-ops-command (the same pattern as the CI deploy key), with a root-owned authorized_keys file and root-owned copies of the commands, keeps the agent's account out of Docker, which is root-equivalent. A leaked key can only read health and logs, install security updates and rotate logs, and only from the server itself.
   Alternatives: A host systemd timer writing reports into a shared volume (the docs say no new timers for app work); Give the agent's account Docker access (root-equivalent)
2. **Restarts, other updates and release upgrades are proposals only, never agent actions**
   Least privilege. Unattended-upgrades already restarts the server at 04:30 UTC. Approving a proposal records the owner's decision, and the owner or someone they trust carries out the steps; the agent does nothing more.
   Alternatives: Allow a reboot verb that the agent runs after approval
3. **Edited shared files: Dockerfile (openssh-client), compose.yaml (worker key mount, host-gateway, OPS\_\* env), settings, urls, .env.example, apps/audit/ops.py**
   The worker can't reach the server without them. The audit change is a generic register_kind() plus an optional actor= argument, so the Manager's 'alongside apps.audit.ops' works without core naming the ops app. Each edit is small and grouped next to the code it belongs with.
   Alternatives: Keep to apps/ops, deploy/ and CI only (the agent couldn't reach the server)
4. **Health results go in the audit log only when they change, plus once a day**
   Hourly events would crowd the dashboard's Recent activity. ServerReport rows are left out of the audit log, and the Operations card flags the check after 26 hours without one.
   Alternatives: An audit event every hour
5. **Urgent findings are attention kind 'problems' and warnings kind 'other'; a check that couldn't run shows as failed on the Operations card**
   'Succeeded' means the check ran. Each finding gets its own attention item instead of one combined failure.
   Alternatives: Mark the health check failed whenever there is an urgent finding
6. **The quarterly review shows from the quarter's second month, and only where OPS_SERVER is set**
   Gives a month of grace and doesn't nag a laptop or break the dashboard's empty-list tests.
   Alternatives: Show it from the first day of each quarter
7. **The AI security review in CI is built but off by default, and reports without failing the job unless AI_REVIEW_FAIL_ON is set**
   It costs money per change (about $0.15 at most with the default claude-sonnet-5-5, diff capped at 150k characters), and no live AI calls were to be made without approval. Static checks (bandit, Django deploy checks, pip-audit) run on every change regardless.
   Alternatives: Turn it on now; Leave AI review out entirely
8. **bandit gates on new findings only, with a committed baseline of 7 reviewed false positives**
   The existing findings (the invisible-character regex in agents/untrusted.py, mark_safe on already-escaped HTML in storefront, the heartbeat file in /tmp) are in other apps and are not bugs; adding #nosec there was outside my files.
   Alternatives: Add #nosec comments in other apps' files; Skip those bandit test ids everywhere
9. **Dependabot: documented turning on alerts instead of adding a pip ecosystem**
   The uv-compiled hashed locks aren't something Dependabot version updates can keep consistent, which dependabot.yml already says. Alerts still read the locks through the dependency graph.
   Alternatives: Add a pip entry to dependabot.yml

**Findings filed**

- T61 fix-shellcheck-sc2164-deploy-scripts: CI's shellcheck step warns (SC2164) on deploy/backup-job.sh and deploy/record-ops-event.sh

**Summary**

> Phase 11: ops and security agent.
> - New `apps/ops`: an hourly server health check with no AI (findings for disk, memory, updates, pending restart, failed services, containers, Ubuntu end of support). There is also a daily upkeep agent on the shared `apps/agents` tool loop, running on a free stand-in. It may only install security updates and rotate logs, each once a day and only when the findings call for it. Anything larger it proposes, with steps, for the owner to approve, decline or mark done.
> - Server side (`deploy/server/ops/`): a `teashop-ops` account with no sudo or docker group. The job worker's SSH key is locked to one command and to the server's private networks, and root owns its authorized_keys. A root helper with fixed commands is reachable only through an exact-argument sudo allow-list. `harden.sh` and `install-app.sh` install all of this, and `compose.yaml` and the Dockerfile let the worker reach the server.
> - Reporting: new Operations-card kinds (health check, upkeep, quarterly review) through a small `register_kind()` hook in `apps.audit.ops`. Attention items for findings, proposals and a due review. An owner page at owner/ops/ and a quarterly review checklist at owner/ops/review/ that fills in what the shop already knows under each item.
> - CI: a new "Security review" job runs on every change: bandit (only new findings fail, against a reviewed baseline), Django's production security checks, and an optional AI review of each diff (off until the owner sets `AI_SECURITY_REVIEW=on` and the API key). A passive OWASP ZAP outside scan runs monthly once `OUTSIDE_SCAN=on`. Dependabot alerts are documented, and bandit was added to requirements-ci.lock.
> - Docs: docs/ops/ops-agent.md and docs/security/quarterly-review.md are new; the security policy, ops README, architecture, agents and jobs docs are updated.


### T61 fix-shellcheck-sc2164-deploy-scripts

- **Origin:** Found by T13 phase11-ops-security-agent
- **Goal:** Bug Fixes
- **Ran:** 2026-11-01 22:03 to 2026-11-01 22:05 (0m 55s)
- **Outcome:** done; committed [`6c3df87654b3`](https://github.com/wingware-dev/teashop/commit/6c3df87654b322e0bbade73bdae30d9f8526137a)
- **Usage:** 1,900 input, 3,610 output, 328k cache read, 24k cache write (claude-haiku-5-5, claude-opus-5-5)
- **Tools:** 15 calls, 4 to Wing's MCP tools (wing-review 4)

**Prompt**

> CI's shellcheck step warns (SC2164) on deploy/backup-job.sh and deploy/record-ops-event.sh
>
> CI runs `shellcheck --severity=warning deploy/*.sh ...`. With the current shellcheck (shellcheck-py), two existing scripts report SC2164 ("cd ... || exit") on their `cd "$(dirname "$0")/.."` line, so that CI step exits 1 and fails the test job (and with it deploys, since deploy.yml reuses ci.yml). Neither script uses `set -e`, so a failed cd would also carry on in the wrong directory. Fix: `cd "$(dirname "$0")/.." || exit 1` in both. Then re-run shellcheck over all deploy scripts.
>
> Evidence: uvx --from shellcheck-py shellcheck --severity=warning deploy/*.sh deploy/backup/*.sh deploy/server/*.sh -> SC2164 at deploy/backup-job.sh:12 and deploy/record-ops-event.sh:14; exit 1.
>
> Suggested next step: fix

**Judgement calls**

1. **record-ops-event.sh exits 0, not 1, when its cd fails**
   The script promises it is best effort and always exits 0, so recording 'never turns a good deploy into a failed one'. deploy.sh, rollback.sh and backup-job.sh all call it. Exiting 1 there would break that promise.
   Alternatives: `|| exit 1` in both scripts, as the task suggested

**Summary**

> Fixed shellcheck SC2164 so CI's shellcheck step passes again:
> - `deploy/backup-job.sh`: `cd "$(dirname "$0")/.." || exit 1`.
> - `deploy/record-ops-event.sh`: a failed cd now logs "cannot cd to the checkout; not recorded" and exits 0. The `log` helper moved above the cd so it can be used there.
> CI's exact command (`shellcheck --severity=warning deploy/*.sh deploy/backup/*.sh deploy/server/*.sh deploy/server/ops/*.sh`, run through shellcheck-py) now exits 0, and `bash -n` passes on both scripts.


### T62 site-css-leaves-date

- **Origin:** Found by T12 phase10-marketing-agent
- **Goal:** Bug Fixes
- **Ran:** 2026-11-01 22:03 to 2026-11-01 22:05 (0m 49s)
- **Outcome:** done; committed [`91d3ea2713de`](https://github.com/wingware-dev/teashop/commit/91d3ea2713dee871b6ec70216cfc238655060037)
- **Usage:** 1,791 input, 3,066 output, 559k cache read, 27k cache write (claude-haiku-5-5, claude-opus-5-5)
- **Tools:** 19 calls, 4 to Wing's MCP tools (wing-review 3, wing-testing 1)

**Prompt**

> site.css leaves date, datetime-local and url inputs unstyled
>
> site.css styles text, number, email and similar inputs (full width, 2.75rem tall, bordered), but not input[type=date], [type=datetime-local] or [type=url]. Those render as small browser-default boxes that don't match the rest of a form, e.g. the email list's "send until" date on owner/email-list/new/. The marketing pages work around it in static/css/marketing.css. The fix is to add those three types to site.css's input rule (about line 216), then drop the copy from marketing.css.
>
> Evidence: static/css/site.css:216 selector list; screenshot var/shots/marketing-post-desktop-light.png (before the workaround) shows the small "Goes out at" input
>
> Suggested next step: fix

**Summary**

> site.css's shared input rule now also covers url, date and datetime-local inputs, so they match the other form fields site-wide (e.g. the email list's "Send until" date). The duplicate workaround rule in marketing.css is removed.


### T64 posts-attention-kind

- **Origin:** Filed by the Tasks Manager from the plan of T12 phase10-marketing-agent
- **Goal:** Planning
- **Ran:** 2026-11-01 22:04 to 2026-11-01 22:05 (0m 56s)
- **Outcome:** done; committed [`4a4988908292`](https://github.com/wingware-dev/teashop/commit/4a4988908292007c8f5ac2b3ae5ba76439931448)
- **Usage:** 1,670 input, 5,021 output, 599k cache read, 36k cache write (claude-haiku-5-5, claude-opus-5-5)
- **Tools:** 18 calls, 5 to Wing's MCP tools (wing-review 4, wing-testing 1)

**Prompt**

> Attention kind for posts due by hand
>
> Add an attention kind (e.g. "posts", deadline 1h) in apps/core/attention.py, and use it in apps/marketing/alerts.py for "Time to post on ..." items. Then the reminder email comes soon after a post is due instead of after 3 days. T12 phase10-marketing-agent (43c10c0c) left these on the 3-day "approvals" kind.

**Judgement calls**

1. **Deadline 1h, title "Posts to put up by hand", listed right after Orders and before approvals**
   The task suggested 1h. The kind's place in KINDS sets where its group appears on the dashboard, so it sits beside the other time-sensitive groups and ahead of the 3-day approvals.
   Alternatives: 30m; Place it next to problems/jobs
2. **Made the first batch of edits with a Python replace script instead of the edit tool**
   That was an oversight: Wing may only guess which task those edits belong to. The changed files are apps/core/attention.py, apps/marketing/alerts.py, docs/marketing.md, docs/reports.md and the first test line in test_posting.py.

**Summary**

> Added a "posts" attention kind ("Posts to put up by hand", 1-hour deadline) and moved marketing's "Time to post on ..." items to it, so the reminder email comes an hour after a by-hand post is due instead of after 3 days.
> - apps/core/attention.py: new kind; apps/marketing/alerts.py uses it
> - Tests check the kind, its 1h deadline and the item going overdue at 61 minutes; docs/reports.md and docs/marketing.md updated


### T65 milestone-shots-phase9-10

- **Origin:** Filed by the Tasks Manager from the plan of T12 phase10-marketing-agent
- **Goal:** Planning
- **Ran:** 2026-11-01 22:05 to 2026-11-01 22:10 (3m 15s)
- **Outcome:** done; committed [`6a6a8760b422`](https://github.com/wingware-dev/teashop/commit/6a6a8760b422830314d04592692a5a4d9e5145b1)
- **Usage:** 76 input, 13k output, 2.07M cache read, 88k cache write (claude-opus-5-5)
- **Tools:** 41 calls, 7 to Wing's MCP tools (wing-review 7)

**Prompt**

> Milestone screenshots for phases 9 and 10
>
> Run `python manage.py milestone_shots phase9-support` and `python manage.py milestone_shots phase10-marketing` to record the support chat and inbox pages (T11 phase9-support-agent (4905724b)) and the marketing pages (T12 phase10-marketing-agent (43c10c0c)) in doc/shots/, as earlier phases did. Look at the shots before finishing, and report anything that looks wrong as a finding.

**Judgement calls**

1. **Limited each run to its own app's browser tests (apps.support, apps.marketing)**
   Earlier milestone folders hold only that phase's pages; the command's default (all apps) would have put every page in each folder.
   Alternatives: Run with the default labels, recording every page in both folders
2. **Overwrote the already-committed phase 9 shots**
   The task asked for the phase9-support run. The new shots show the same pages with fresh test data, plus small layout changes since phase 9 was committed.
   Alternatives: Skip phase 9 and keep the committed shots

**Findings filed**

- T69 health-claim-label-overlap: Health-claim warnings mislabel "boosts immunity" and report overlapping matches twice
- T68 calendar-empty-day-style: Marketing calendar: days without posts take the site-wide .empty empty-state style
- T70 agent-audit-attribution: AI agents page: unrelated actions credited to support-agent, plus small layout glitches

**Screenshots**

![marketing-article-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/6a6a8760b422830314d04592692a5a4d9e5145b1/doc/shots/2026-11-01-phase10-marketing/marketing-article-desktop-dark.png)

![marketing-article-desktop-light.png](https://github.com/wingware-dev/teashop/raw/6a6a8760b422830314d04592692a5a4d9e5145b1/doc/shots/2026-11-01-phase10-marketing/marketing-article-desktop-light.png)

![marketing-article-phone-dark.png](https://github.com/wingware-dev/teashop/raw/6a6a8760b422830314d04592692a5a4d9e5145b1/doc/shots/2026-11-01-phase10-marketing/marketing-article-phone-dark.png)

![marketing-article-phone-light.png](https://github.com/wingware-dev/teashop/raw/6a6a8760b422830314d04592692a5a4d9e5145b1/doc/shots/2026-11-01-phase10-marketing/marketing-article-phone-light.png)

![marketing-calendar-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/6a6a8760b422830314d04592692a5a4d9e5145b1/doc/shots/2026-11-01-phase10-marketing/marketing-calendar-desktop-dark.png)

![marketing-calendar-desktop-light.png](https://github.com/wingware-dev/teashop/raw/6a6a8760b422830314d04592692a5a4d9e5145b1/doc/shots/2026-11-01-phase10-marketing/marketing-calendar-desktop-light.png)

![marketing-calendar-phone-dark.png](https://github.com/wingware-dev/teashop/raw/6a6a8760b422830314d04592692a5a4d9e5145b1/doc/shots/2026-11-01-phase10-marketing/marketing-calendar-phone-dark.png)

![marketing-calendar-phone-light.png](https://github.com/wingware-dev/teashop/raw/6a6a8760b422830314d04592692a5a4d9e5145b1/doc/shots/2026-11-01-phase10-marketing/marketing-calendar-phone-light.png)

![marketing-campaigns-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/6a6a8760b422830314d04592692a5a4d9e5145b1/doc/shots/2026-11-01-phase10-marketing/marketing-campaigns-desktop-dark.png)

![marketing-campaigns-desktop-light.png](https://github.com/wingware-dev/teashop/raw/6a6a8760b422830314d04592692a5a4d9e5145b1/doc/shots/2026-11-01-phase10-marketing/marketing-campaigns-desktop-light.png)

![marketing-campaigns-phone-dark.png](https://github.com/wingware-dev/teashop/raw/6a6a8760b422830314d04592692a5a4d9e5145b1/doc/shots/2026-11-01-phase10-marketing/marketing-campaigns-phone-dark.png)

![marketing-campaigns-phone-light.png](https://github.com/wingware-dev/teashop/raw/6a6a8760b422830314d04592692a5a4d9e5145b1/doc/shots/2026-11-01-phase10-marketing/marketing-campaigns-phone-light.png)

![marketing-flow-approved-desktop-light.png](https://github.com/wingware-dev/teashop/raw/6a6a8760b422830314d04592692a5a4d9e5145b1/doc/shots/2026-11-01-phase10-marketing/marketing-flow-approved-desktop-light.png)

![marketing-flow-drafted-desktop-light.png](https://github.com/wingware-dev/teashop/raw/6a6a8760b422830314d04592692a5a4d9e5145b1/doc/shots/2026-11-01-phase10-marketing/marketing-flow-drafted-desktop-light.png)

![marketing-home-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/6a6a8760b422830314d04592692a5a4d9e5145b1/doc/shots/2026-11-01-phase10-marketing/marketing-home-desktop-dark.png)

![marketing-home-desktop-light.png](https://github.com/wingware-dev/teashop/raw/6a6a8760b422830314d04592692a5a4d9e5145b1/doc/shots/2026-11-01-phase10-marketing/marketing-home-desktop-light.png)

![marketing-home-phone-dark.png](https://github.com/wingware-dev/teashop/raw/6a6a8760b422830314d04592692a5a4d9e5145b1/doc/shots/2026-11-01-phase10-marketing/marketing-home-phone-dark.png)

![marketing-home-phone-light.png](https://github.com/wingware-dev/teashop/raw/6a6a8760b422830314d04592692a5a4d9e5145b1/doc/shots/2026-11-01-phase10-marketing/marketing-home-phone-light.png)

![marketing-idea-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/6a6a8760b422830314d04592692a5a4d9e5145b1/doc/shots/2026-11-01-phase10-marketing/marketing-idea-desktop-dark.png)

![marketing-idea-desktop-light.png](https://github.com/wingware-dev/teashop/raw/6a6a8760b422830314d04592692a5a4d9e5145b1/doc/shots/2026-11-01-phase10-marketing/marketing-idea-desktop-light.png)

![marketing-idea-phone-dark.png](https://github.com/wingware-dev/teashop/raw/6a6a8760b422830314d04592692a5a4d9e5145b1/doc/shots/2026-11-01-phase10-marketing/marketing-idea-phone-dark.png)

![marketing-idea-phone-light.png](https://github.com/wingware-dev/teashop/raw/6a6a8760b422830314d04592692a5a4d9e5145b1/doc/shots/2026-11-01-phase10-marketing/marketing-idea-phone-light.png)

![marketing-post-blocked-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/6a6a8760b422830314d04592692a5a4d9e5145b1/doc/shots/2026-11-01-phase10-marketing/marketing-post-blocked-desktop-dark.png)

![marketing-post-blocked-desktop-light.png](https://github.com/wingware-dev/teashop/raw/6a6a8760b422830314d04592692a5a4d9e5145b1/doc/shots/2026-11-01-phase10-marketing/marketing-post-blocked-desktop-light.png)

![marketing-post-blocked-phone-dark.png](https://github.com/wingware-dev/teashop/raw/6a6a8760b422830314d04592692a5a4d9e5145b1/doc/shots/2026-11-01-phase10-marketing/marketing-post-blocked-phone-dark.png)

![marketing-post-blocked-phone-light.png](https://github.com/wingware-dev/teashop/raw/6a6a8760b422830314d04592692a5a4d9e5145b1/doc/shots/2026-11-01-phase10-marketing/marketing-post-blocked-phone-light.png)

![marketing-post-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/6a6a8760b422830314d04592692a5a4d9e5145b1/doc/shots/2026-11-01-phase10-marketing/marketing-post-desktop-dark.png)

![marketing-post-desktop-light.png](https://github.com/wingware-dev/teashop/raw/6a6a8760b422830314d04592692a5a4d9e5145b1/doc/shots/2026-11-01-phase10-marketing/marketing-post-desktop-light.png)

![marketing-post-phone-dark.png](https://github.com/wingware-dev/teashop/raw/6a6a8760b422830314d04592692a5a4d9e5145b1/doc/shots/2026-11-01-phase10-marketing/marketing-post-phone-dark.png)

![marketing-post-phone-light.png](https://github.com/wingware-dev/teashop/raw/6a6a8760b422830314d04592692a5a4d9e5145b1/doc/shots/2026-11-01-phase10-marketing/marketing-post-phone-light.png)

![agents-owner-home-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/6a6a8760b422830314d04592692a5a4d9e5145b1/doc/shots/2026-11-01-phase9-support/agents-owner-home-desktop-dark.png)

![agents-owner-home-desktop-light.png](https://github.com/wingware-dev/teashop/raw/6a6a8760b422830314d04592692a5a4d9e5145b1/doc/shots/2026-11-01-phase9-support/agents-owner-home-desktop-light.png)

![agents-owner-home-phone-dark.png](https://github.com/wingware-dev/teashop/raw/6a6a8760b422830314d04592692a5a4d9e5145b1/doc/shots/2026-11-01-phase9-support/agents-owner-home-phone-dark.png)

![agents-owner-home-phone-light.png](https://github.com/wingware-dev/teashop/raw/6a6a8760b422830314d04592692a5a4d9e5145b1/doc/shots/2026-11-01-phase9-support/agents-owner-home-phone-light.png)

![support-chat-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/6a6a8760b422830314d04592692a5a4d9e5145b1/doc/shots/2026-11-01-phase9-support/support-chat-desktop-dark.png)

![support-chat-desktop-light.png](https://github.com/wingware-dev/teashop/raw/6a6a8760b422830314d04592692a5a4d9e5145b1/doc/shots/2026-11-01-phase9-support/support-chat-desktop-light.png)

![support-chat-phone-dark.png](https://github.com/wingware-dev/teashop/raw/6a6a8760b422830314d04592692a5a4d9e5145b1/doc/shots/2026-11-01-phase9-support/support-chat-phone-dark.png)

![support-chat-phone-light.png](https://github.com/wingware-dev/teashop/raw/6a6a8760b422830314d04592692a5a4d9e5145b1/doc/shots/2026-11-01-phase9-support/support-chat-phone-light.png)

![support-flow-chat-answered-phone-light.png](https://github.com/wingware-dev/teashop/raw/6a6a8760b422830314d04592692a5a4d9e5145b1/doc/shots/2026-11-01-phase9-support/support-flow-chat-answered-phone-light.png)

![support-flow-chat-waiting-phone-light.png](https://github.com/wingware-dev/teashop/raw/6a6a8760b422830314d04592692a5a4d9e5145b1/doc/shots/2026-11-01-phase9-support/support-flow-chat-waiting-phone-light.png)

![support-flow-owner-edits-desktop-light.png](https://github.com/wingware-dev/teashop/raw/6a6a8760b422830314d04592692a5a4d9e5145b1/doc/shots/2026-11-01-phase9-support/support-flow-owner-edits-desktop-light.png)

![support-flow-owner-sent-desktop-light.png](https://github.com/wingware-dev/teashop/raw/6a6a8760b422830314d04592692a5a4d9e5145b1/doc/shots/2026-11-01-phase9-support/support-flow-owner-sent-desktop-light.png)

![support-owner-conversation-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/6a6a8760b422830314d04592692a5a4d9e5145b1/doc/shots/2026-11-01-phase9-support/support-owner-conversation-desktop-dark.png)

![support-owner-conversation-desktop-light.png](https://github.com/wingware-dev/teashop/raw/6a6a8760b422830314d04592692a5a4d9e5145b1/doc/shots/2026-11-01-phase9-support/support-owner-conversation-desktop-light.png)

![support-owner-conversation-phone-dark.png](https://github.com/wingware-dev/teashop/raw/6a6a8760b422830314d04592692a5a4d9e5145b1/doc/shots/2026-11-01-phase9-support/support-owner-conversation-phone-dark.png)

![support-owner-conversation-phone-light.png](https://github.com/wingware-dev/teashop/raw/6a6a8760b422830314d04592692a5a4d9e5145b1/doc/shots/2026-11-01-phase9-support/support-owner-conversation-phone-light.png)

![support-owner-inbox-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/6a6a8760b422830314d04592692a5a4d9e5145b1/doc/shots/2026-11-01-phase9-support/support-owner-inbox-desktop-dark.png)

![support-owner-inbox-desktop-light.png](https://github.com/wingware-dev/teashop/raw/6a6a8760b422830314d04592692a5a4d9e5145b1/doc/shots/2026-11-01-phase9-support/support-owner-inbox-desktop-light.png)

![support-owner-inbox-phone-dark.png](https://github.com/wingware-dev/teashop/raw/6a6a8760b422830314d04592692a5a4d9e5145b1/doc/shots/2026-11-01-phase9-support/support-owner-inbox-phone-dark.png)

![support-owner-inbox-phone-light.png](https://github.com/wingware-dev/teashop/raw/6a6a8760b422830314d04592692a5a4d9e5145b1/doc/shots/2026-11-01-phase9-support/support-owner-inbox-phone-light.png)

**Summary**

> Recorded milestone screenshots for phases 9 and 10:
> - doc/shots/2026-11-01-phase10-marketing/: 30 new marketing shots (8 browser tests passed), added to git.
> - doc/shots/2026-11-01-phase9-support/: re-recorded over the copies committed in 1adcd07 (6 browser tests passed, 24 shots). 20 files changed, mainly timestamps and order numbers, and support-chat-phone is now 26px taller.
> - Looked through the shots: 3 findings filed, T68 calendar-empty-day-style (002a72e9), T69 health-claim-label-overlap (fb9ab987) and T70 agent-audit-attribution (6d0fd704).


### T67 regression-sweep-phases-9-11

- **Origin:** Filed by the Tasks Manager
- **Goal:** Planning
- **Ran:** 2026-11-01 22:05 to 2026-11-01 22:13 (7m 53s)
- **Outcome:** done
- **Usage:** 1,862 input, 1,897 output, 267k cache read, 20k cache write (claude-haiku-5-5, claude-opus-5-5)
- **Tools:** 7 calls, 6 to Wing's MCP tools (wing-review 3, wing-testing 3)

**Prompt**

> Regression tests for phases 9-11 and their fixes
>
> A sweep under wing_guide topic 'research'. Covers the work committed since the last sweep: T60, T11, T12, T13, T61, T62 and T64. Make one test_run per batch, with these specs:
> 1. apps/checkout/tests, apps/storefront/tests, apps/emaillist/tests, apps/support/tests and apps/marketing/tests
> 2. apps/core/tests, apps/audit, apps/jobs/tests, apps/agents/tests, apps/ops/tests, apps/reports/tests, apps/fulfillment/tests, apps/catalog/tests, apps/inventory/tests and apps/purchasing
> File each failure with report_finding (next_step fix), with the test name, error and likely cause. Don't fix anything.
>
> See \<project>/.TASKS/notes/regression-tests-for-phases-9-11-and-their-fixes.md

**Summary**

> Regression sweep of phases 9-11 and their fixes (T60, T11, T12, T13, T61, T62, T64) passed, so no findings were filed:
> - Batch 1 (checkout, storefront, emaillist, support, marketing): 370 passed.
> - Batch 2 (core, audit, jobs, agents, ops, reports, fulfillment, catalog, inventory, purchasing): 444 passed, 1 skipped. The skipped test only runs on PostgreSQL ("trigger exists on PostgreSQL only").


### T70 agent-audit-attribution

- **Origin:** Found by T65 milestone-shots-phase9-10
- **Goal:** Planning
- **Ran:** 2026-11-01 22:14 to 2026-11-01 22:18 (4m 10s)
- **Outcome:** done; committed [`597bcda585fb`](https://github.com/wingware-dev/teashop/commit/597bcda585fbd10d2c69cfba114c2b98624aa180)
- **Usage:** 98 input, 18k output, 2.98M cache read, 77k cache write (claude-opus-5-5)
- **Tools:** 68 calls, 7 to Wing's MCP tools (wing-review 4, wing-testing 3)

**Prompt**

> AI agents page: unrelated actions credited to support-agent, plus small layout glitches
>
> The "What the agents did lately" table on the owner's AI agents page lists "support-agent  create  Checkout settings" and "support-agent  reports.email_sent  · overdue: ...". The settings row comes from a read-only tool (likely lookup_order) creating the checkout-settings singleton via get_or_create inside acting_as_agent. The overdue-reminder emails are dashboard jobs, not something the agent decided. An owner reading the log may think the agent changed shop settings. Two things need deciding: whether jobs queued during an agent run, and lazy singleton creation, should be credited to the agent, and whether the page should show only agent-specific actions. Two cosmetic issues on the same page: the Details cell starts with " · " when object_repr is empty, and the "Share of the cap used" \<meter> renders at the browser default of about 80px wide.
>
> Evidence: doc/shots/2026-11-01-phase9-support/agents-owner-home-desktop-light.png; apps/agents/templates/agents/owner_home.html:10 (meter, no width) and :41 (unconditional " · " before message); apps/agents/runner.py:114 acting_as_agent wraps the whole run, tools included; apps/audit/context.py.
>
> Suggested next step: decide
>
> [Tasks Manager, 2026-11-01 22:09] Manager decision: credit the agent only with actions it takes on purpose, meaning its tools' writes and the messages and drafts it sends. Lazy creation of settings singletons should be attributed to the system, for example by creating them before the agent context starts or by suspending agent attribution for get_or_create of singletons. Background jobs enqueued during a run run later as the system, not as the agent. On the AI agents page, list only agent-attributed events after that change. Also fix the leading " · " when object_repr is empty, and give the cap \<meter> a sensible width. Add tests for the attribution.
>
> See \<project>/.TASKS/notes/ai-agents-page-unrelated-actions-credited-to-support-age.md

**Judgement calls**

1. **Agent-queued jobs run as plain "system", with no record of which agent queued them**
   The Manager said such jobs run as the system. A label like "system (for support-agent)" would also flow into fields such as emaillist's created_by.
   Alternatives: Store the actor as system with a label naming the agent; Add a queued_by field to Actor
2. **Applies to every job an agent queues, including send_reply (the email delivering the agent's own message)**
   The agent's message and draft creation stay credited to it. The email delivery is the shop's background job, and its audit record is now the system's.
   Alternatives: Keep the agent actor for send_reply only
3. **Restyled the meter with a site.css class instead of an inline style**
   Keeps styling in CSS. It can be reused for other gauges.
   Alternatives: Inline style on the meter

**Summary**

> The AI agents page now credits an agent only with what it does on purpose, and the page's two layout glitches are fixed:
> - A job an agent queues (such as the overdue-reminder email) is now stored to run as the system (`_job_actor` in `apps/jobs/queue.py`).
> - `CheckoutSettings.current()` now creates its missing row under the new `acting_as_system()` (in `apps/audit`), so the system gets the credit, not an agent.
> - The owner page still lists only agent-attributed events. The Details cell no longer starts with " · " when there is no object, and the cap `<meter>` gets a `gauge` class (block, 100% wide, at most 24rem).
> - New tests cover the attribution end to end (support agent with a lazily created settings row, plus the reminder job), job-actor storage and the page. The docs (`docs/jobs.md`, `docs/agents.md`) and the runner docstring are updated.


### T68 calendar-empty-day-style

- **Origin:** Found by T65 milestone-shots-phase9-10
- **Goal:** Bug Fixes
- **Ran:** 2026-11-01 22:14 to 2026-11-01 22:15 (1m 07s)
- **Outcome:** done; committed [`be1a8845497c`](https://github.com/wingware-dev/teashop/commit/be1a8845497c08d73ea7e64a02f0d065aa591fbd)
- **Usage:** 1,696 input, 3,305 output, 1.41M cache read, 9,577 cache write (claude-haiku-5-5, claude-opus-5-5)
- **Tools:** 13 calls, 2 to Wing's MCP tools (wing-review 2)

**Prompt**

> Marketing calendar: days without posts take the site-wide .empty empty-state style
>
> On the owner marketing calendar (desktop), days with nothing on them are centred, padded and rounded, while days with posts are left-aligned and square-cornered, so the month grid looks inconsistent. The cause is that the template marks those days with class "empty", and site.css already has a global `.empty` rule for empty-state panels (padding 2rem 1rem; text-align: center; dashed border; border-radius). That rule leaks into the calendar cells. Fix: rename the day class (e.g. "day-empty" or "nothing") in the calendar template and in marketing.css's phone media query that hides empty days, or reset those properties under `.month .day`.
>
> Evidence: doc/shots/2026-11-01-phase10-marketing/marketing-calendar-desktop-{light,dark}.png (compare the "Mon 2" cell with the rest); apps/marketing/templates/marketing/owner/calendar.html:20 adds `empty`; static/css/site.css:472 `.empty {...}`; static/css/marketing.css:53 hides `.month .day.empty` on phones.
>
> Suggested next step: fix
>
> [Tasks Manager, 2026-11-01 22:08] Manager: after the fix, replace only the two marketing-calendar desktop shots in doc/shots/2026-11-01-phase10-marketing/ (light and dark), with the same names. Don't re-take or recompress the other committed shots, because that only grows the git history.

**Judgement calls**

1. **Renamed the class to day-empty rather than resetting .empty's properties under .month .day**
   Avoids fighting a global rule property by property; any future change to .empty can't leak back in.
   Alternatives: Override padding/text-align/border/radius under .month .day

**Screenshots**

![marketing-calendar-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/be1a8845497c08d73ea7e64a02f0d065aa591fbd/doc/shots/2026-11-01-phase10-marketing/marketing-calendar-desktop-dark.png)

![marketing-calendar-desktop-light.png](https://github.com/wingware-dev/teashop/raw/be1a8845497c08d73ea7e64a02f0d065aa591fbd/doc/shots/2026-11-01-phase10-marketing/marketing-calendar-desktop-light.png)

**Summary**

> Fixed the uneven marketing calendar: days without posts used the class "empty", which picked up site.css's centred, rounded empty-state panel style. They now use "day-empty", in calendar.html and in marketing.css's phone rule that hides them. Replaced only the two marketing-calendar desktop milestone shots (light, dark) with recompressed new ones; all days now share one style.


### T69 health-claim-label-overlap

- **Origin:** Found by T65 milestone-shots-phase9-10
- **Goal:** Bug Fixes
- **Ran:** 2026-11-01 22:14 to 2026-11-01 22:16 (1m 30s)
- **Outcome:** done; committed [`6dd2fd5b9101`](https://github.com/wingware-dev/teashop/commit/6dd2fd5b9101778caa0dc35817882147d5fc8cc3)
- **Usage:** 1,908 input, 4,442 output, 477k cache read, 28k cache write (claude-haiku-5-5, claude-opus-5-5)
- **Tools:** 14 calls, 5 to Wing's MCP tools (wing-review 4, wing-testing 1)

**Prompt**

> Health-claim warnings mislabel "boosts immunity" and report overlapping matches twice
>
> The blocked-post page shows: Health or disease claim: "boosts immunity" (boosts metabolism, energy or mood), "immunity" (immunity). This has two problems. (1) The label for the "boost(s) ..." pattern says "metabolism, energy or mood", but the pattern also matches immunity and health, so the label it prints contradicts the words it quotes. (2) Overlapping matches are each listed, so one phrase produces two warnings. Fix: relabel that pattern (e.g. "boosts a body function") and, in health_claims(), drop matches that fall inside a span already reported. The same text appears in product copy checks, the admin and the AI variant importer, since they all use apps/catalog/copy_rules.py.
>
> Evidence: doc/shots/2026-11-01-phase10-marketing/marketing-post-blocked-desktop-light.png; apps/catalog/copy_rules.py:43-44 (immunity and boosts patterns) and health_claims() at ~line 76.
>
> Suggested next step: fix

**Judgement calls**

1. **Drop only matches wholly contained in a reported span; keep partial overlaps**
   The task asks to drop matches that fall inside a reported span. A partial overlap quotes different words that can be a separate claim, so it still gets reported.
   Alternatives: Drop any match that overlaps a reported span at all
2. **Label text: "boosts a body function"**
   The task suggested it, and it covers metabolism, energy, immunity, health and mood.
   Alternatives: "boosts health, energy or mood"

**Summary**

> Health-claim warnings no longer mislabel or double-report "boosts immunity":
> - Relabelled the "boost(s) ..." pattern in apps/catalog/copy_rules.py to "boosts a body function", since it also matches immunity and health.
> - health_claims() now drops a match that lies wholly inside one already reported (the longest match at each position wins), so "boosts immunity" gives one warning instead of two; added a test for this.


### T71 agent-guards-cover-queued-jobs

- **Origin:** Filed by the Tasks Manager from the plan of T70 agent-audit-attribution
- **Goal:** Planning
- **Ran:** 2026-11-01 22:18 to 2026-11-01 22:23 (4m 57s)
- **Outcome:** done; committed [`c015e896a99d`](https://github.com/wingware-dev/teashop/commit/c015e896a99d4576be39a56d93b40da6b9b3dcd2)
- **Usage:** 2,189 input, 9,611 output, 1.72M cache read, 16k cache write (claude-haiku-5-5, claude-opus-5-5)
- **Tools:** 37 calls, 3 to Wing's MCP tools (wing-review 2, wing-testing 1)

**Prompt**

> Make agent guards cover jobs an agent queues
>
> Several guards refuse an action only when `current_actor().type == "agent"`: `_refuse_agents` in fulfillment and in marketing, and `support.services.set_answers_alone`. Since T70 agent-audit-attribution (6d0fd704), jobs an agent queues run as the system, so a guard would let such a job through. None reaches a guard today (the only ones are send_reply and overdue_reminders), but keep the protection. Record the queuing agent on the job (for example a `queued_by` on the job or Actor) and check it in these guards, while keeping the audit log's system attribution. Add a test where an agent-queued job tries a refused action. Also run apps/checkout, apps/support, apps/marketing, apps/ops and apps/emaillist tests once at the end, because T70 changed CheckoutSettings.current() and job attribution.

**Judgement calls**

1. **Updated all six agent guards, not only the three the task named**
   Purchasing, inventory and the email list use the same check. Those also need a signed-in user, but keeping every guard on one idiom stops a future copy from missing jobs.
   Alternatives: Change only fulfillment, marketing and support
2. **Kept the agent name on the job's stored actor (Actor.for_agent), not as a new Job column**
   No migration. It flows through the existing actor JSON, which jobs already restore, and old job rows read as "".
   Alternatives: queued_by column on Job
3. **Marketing's edited_by_owner check also uses agent_involved()**
   A job queued by an agent that changes a post's text is not the owner editing it.
   Alternatives: Leave it on actor.type

**Summary**

> Agent guards now also refuse jobs an AI agent queued, while the audit log still credits those jobs to the system:
> - `Actor` gains a `for_agent` field, which is not written to the audit log. A job an agent queues is stored as the system with `for_agent` set to the agent's name, and jobs that job queues keep it.
> - New `apps.audit.agent_involved()` returns the agent's name for an agent or its jobs. Every agent guard now checks it instead of `current_actor().type == "agent"`: the fulfillment and marketing `_refuse_agents`, `set_answers_alone`, `approve_purchase_order`, `apply_count` and the email-list `approve`. Marketing's `edited_by_owner` check uses it too.
> - New tests: a job an agent queued, and a job queued by that job, are both refused by `set_answers_alone`; an owner-queued job is not. The guidance in `docs/agents.md` and `docs/jobs.md` now names `agent_involved()`.


### T72 don-see-dashboard-set

- **Origin:** Written by the user
- **Goal:** Planning
- **Ran:** 2026-11-01 22:40 to 2026-11-01 22:46 (5m 40s)
- **Outcome:** done; committed [`4acb92edff11`](https://github.com/wingware-dev/teashop/commit/4acb92edff11cbbbaf869e633e5cb7ebc4c5b0bf)
- **Usage:** 120 input, 34k output, 5.33M cache read, 125k cache write (claude-opus-5-5)
- **Tools:** 67 calls, 11 to Wing's MCP tools (wing-review 8, wing-analysis 2, wing-testing 1)

**Prompt**

> I don't see where in the dashboard to set up inventory, shipping supplies, etc.  Does this exist already?  Either way, can you populate the local dev database with some sample teas and other content?
>
> [Tasks Manager, 2026-11-01 22:40] Manager: setup for teas, lots, packaging, boxes, scales and suppliers is only in the Django admin; the dashboard has no shortcuts to it. Do both: (1) add grouped dashboard shortcuts (attention.register_shortcut in each app's ready()) to the admin pages for catalog, receiving lots, stock count, packaging and shipping supplies, scales and boxes, and suppliers. (2) Extend load_demo_catalog, or add a dev-only command that refuses to run with DEBUG off, safe to run twice. It should load about 10 teas with sizes, prices, labels and one allergen blend; suppliers, lots, packaging, boxes and a scale; orders at several stages; a subscription; email subscribers and a draft mailing; a support conversation; and marketing ideas. Run it on the local dev database and check it in the browser harness. Report the exact command, and say that the owner account comes from createsuperuser plus two-factor.
>
> See \<project>/.TASKS/notes/i-don-t-see-where-in-the-dashboard-to-set-up-inventory-s.md

**Judgement calls**

1. **Added a new command, load_demo_shop, and left load_demo_catalog unchanged**
   The browser tests and milestone screenshots call demo.load() and expect only the catalog. Orders, support and mailings would add attention items and change their pages. load_demo_shop loads the catalog first, so it is the one command to run.
   Alternatives: Extend load_demo_catalog with a flag such as --business
2. **Ungrouped shortcuts stay at the top of the card; the new admin links are listed under group headings below them**
   Keeps the existing report and work-page links where the owner already finds them.
   Alternatives: Give every existing shortcut a group too; Put the setup links in their own dashboard card
3. **The shipped demo order has no parcel or packing records and does not take stock**
   Shipping for real goes through the label purchase, which calls the carrier API. The order shows up correctly in the Shipped tab and on its order page.
   Alternatives: Pack it through fulfillment services, which takes stock but still needs a fake label

**Findings filed**

- T73 shipped-tab-late-badge: Shipped tab of the packing queue labels orders shipped on time as "Late"

**Summary**

> Setup existed only in the Django admin. The owner dashboard now links to those admin pages in groups, and a new dev-only command fills the local database with sample data.
> - Dashboard Shortcuts card: three new groups. "Catalog: teas and goods" has products, sizes/prices/SKUs, categories, collections and regions. "Stock: receiving, lots and suppliers" has receive a delivery, lots, stock items, purchase orders, suppliers and stock counts. "Packaging and shipping supplies" has packaging and shipping-box stock (filtered item lists), box sizes, package dimensions and scales. `attention.register_shortcut()` takes optional `group` and `query` arguments, and the new `shortcut_groups()` returns the links grouped. Each app registers its own links in `ready()`.
> - New command `python manage.py load_demo_shop`. It refuses to run unless DEBUG is on and it is not production, and running it twice adds nothing. It loads the demo catalog: 10 teas with sizes, prices and label names, including Vanilla Almond Black, whose lot carries the tree-nut allergen, plus 3 goods. Around that it adds 3 suppliers and a receiving delivery of 2 new lots from a second supplier. It also adds tissue filler, a mailer and 2 boxes in stock, 3 box sizes and a sealed scale. There are orders at every stage (waiting for payment, paid and due, paid and late, paid with an allergen tea, shipped, cancelled), a monthly subscription with a paid delivery, and 5 email subscribers with consent records. Finally there is a draft mailing, an emailed support question with a drafted reply plus an answered chat, and an autumn campaign with 4 marketing ideas.
> - I ran it on the local dev database (`var/dev.sqlite3`), twice. The owner account is not created by the command: make it with `python manage.py createsuperuser`, then set up two-factor at the first sign-in.


### T73 shipped-tab-late-badge

- **Origin:** Found by T72 don-see-dashboard-set
- **Goal:** Bug Fixes
- **Ran:** 2026-11-01 22:45 to 2026-11-01 22:47 (1m 34s)
- **Outcome:** done; committed [`418808b616df`](https://github.com/wingware-dev/teashop/commit/418808b616dfe44fbd459b87167485cd68304857)
- **Usage:** 38 input, 5,861 output, 618k cache read, 36k cache write (claude-opus-5-5)
- **Tools:** 17 calls, 5 to Wing's MCP tools (wing-review 4, wing-testing 1)

**Prompt**

> Shipped tab of the packing queue labels orders shipped on time as "Late"
>
> apps/fulfillment/views.py ship_status() compares only order.ship_by with today, and _row() uses it for every row, including the "Shipped" tab (?show=shipped). An order that shipped before its promised date shows a red "Late: promised ... (N days ago)" badge once that date has passed. The owner may then think the shop broke the FTC Mail Order Rule when it didn't. For shipped orders the badge should compare shipped_at with ship_by: no badge, or "Shipped late" only when shipped_at.date() > ship_by.
>
> Evidence: Seen with the demo data (python manage.py load_demo_shop): order paid Oct 26, ship_by Oct 29, shipped Oct 27. /owner/fulfillment/?show=shipped shows "Late: promised Thu Oct 29 (3 days ago)" next to "Shipped Oct 27". Code: apps/fulfillment/views.py:38-48 (ship_status) and :64 (_row).
>
> Suggested next step: fix

**Judgement calls**

1. **Only the Shipped tab uses the new check; the To pack and Back-ordered tabs still use ship_status()**
   Shipped orders with reship or back-ordered parcels still show on those tabs and still owe items, so being past the promised date there is a real Mail Order Rule problem. The order page only shows the badge for paid orders, so it was never affected.
   Alternatives: Make ship_status() itself use shipped_at for every shipped order
2. **Wording "Shipped late: promised Thu Oct 29 (2 days after)", with the existing red late style**
   It follows the existing "Late: promised ..." badge. A shipped-late order is a real rule breach, so red fits. The urgent "ship today" alert only shows on the To pack tab, so this badge doesn't trigger it.
   Alternatives: A neutral badge style (needs a CSS change outside this task's files)

**Summary**

> The Shipped tab of the packing queue now decides lateness by when the order actually shipped. It used to compare the promised date with today. An order that shipped on or before its ship_by date gets no badge. One that shipped after gets a red "Shipped late: promised ... (N days after)" badge (new shipped_status() in apps/fulfillment/views.py, plus a test in test_views.py).


### T74 demo-package-dimensions

- **Origin:** Filed by the Tasks Manager from the plan of T72 don-see-dashboard-set
- **Goal:** Planning
- **Ran:** 2026-11-01 22:47 to 2026-11-01 22:49 (1m 25s)
- **Outcome:** done; committed [`2eac01edd623`](https://github.com/wingware-dev/teashop/commit/2eac01edd6238ae1075d1de13975742322aa4836)
- **Usage:** 1,930 input, 8,261 output, 2.37M cache read, 15k cache write (claude-haiku-5-5, claude-opus-5-5)
- **Tools:** 19 calls, 4 to Wing's MCP tools (wing-review 3, wing-testing 1)

**Prompt**

> Sample package dimensions in load_demo_shop
>
> Add PackageDimensions for the demo pouch and tin sizes in `load_demo_shop` (apps/storefront/demo_shop.py, from T72 don-see-dashboard-set (3ab3ad10)), so the box suggestion on the packing page has real data to work with. Re-run it on the local dev database; it must still add nothing on a second run.
>
> See \<project>/.TASKS/notes/sample-package-dimensions-in-load-demo-shop.md

**Judgement calls**

1. **Invented plausible sizes per package type and weight, e.g. 50 g pouch 6 × 4 × 1.5 in, 100 g tin 3.25 × 3.25 × 5.5 in**
   Demo data only. The sizes are chosen so the three demo boxes all get suggested in the sample orders: the mailer for flat pouches, the boxes for tins and mixed orders.
   Alternatives: Use settings.PACKAGE_DIMENSIONS_IN's defaults, which would make the records pointless

**Findings filed**

- T75 box-suggest-ignores-thick-package: Box suggestion can pick a mailer too thin for one of the packages

**Summary**

> `load_demo_shop` now records package dimensions for all 15 demo tea sizes (pouches of 25, 30 and 50 g; tins of 25, 50 and 100 g), so the packing page's box suggestion works from measured sizes instead of the defaults in settings.
> - Only demo teas' sizes that have no dimensions yet get them, so a second run adds nothing and the owner's own measurements are never changed.
> - Re-ran it twice on the local dev database: 15 dimensions both times. The test now also checks that a 50 g pouch is suggested the padded mailer and a 100 g tin the 8 × 6 × 4 box.


### T75 box-suggest-ignores-thick-package

- **Origin:** Found by T74 demo-package-dimensions
- **Goal:** Bug Fixes
- **Ran:** 2026-11-01 22:49 to 2026-11-01 22:52 (2m 22s)
- **Outcome:** done; committed [`5dca5dd57597`](https://github.com/wingware-dev/teashop/commit/5dca5dd5759781edda4e05e13664174669f3fb00)
- **Usage:** 38 input, 5,762 output, 959k cache read, 15k cache write (claude-opus-5-5)
- **Tools:** 13 calls, 5 to Wing's MCP tools (wing-review 3, wing-testing 2)

**Prompt**

> Box suggestion can pick a mailer too thin for one of the packages
>
> apps/fulfillment/boxes.py suggest() keeps only the "biggest" package's sides, picked by comparing the sorted side lists lexicographically (`if sides > result.biggest`). holds() then checks just that one package's sides against the box. A long, flat pouch therefore wins over a shorter but thicker tin, and the tin's thickness is never checked. The packing page can then suggest a padded mailer the tin won't fit in. The fix: check each package's sides (or the side-wise maximum) against the box, not only one package's.
>
> Evidence: With the demo data (python manage.py load_demo_shop): boxes.suggest([(SizeOption sku ASSAM-SECOND-50 [pouch 6 × 4 × 1.5 in], 1), (SILVER-NEEDL-25 [tin 3 × 2.75 × 2.75 in], 1)]) returns "Padded mailer 6 × 9 in (9 × 6 × 1.5 in)". The 2.75 in tin cannot go in a 1.5 in mailer. Code: apps/fulfillment/boxes.py suggest(), the `if sides > result.biggest` line, and holds().
>
> Suggested next step: fix
>
> [Tasks Manager, 2026-11-01 22:48] Manager: T74 is running at the same time and adds PackageDimensions to apps/storefront/demo_shop.py. Keep to apps/fulfillment/boxes.py and the fulfillment tests; don't edit demo_shop.py. Add a test with a long flat pouch plus a thicker tin that must not get the 1.5 in mailer.

**Messages from the Tasks Manager**

- 2026-11-01 22:50: , which arrived as you finished: Manager: no other writer is active now. Please run the whole of apps/fulfillment/tests in one test_run, since the packing page and label purchase also use suggest(). Fix anything your change broke, then report again. Carry on with the task if this changes anything, and end with task_report again.

**Judgement calls**

1. **Kept Suggestion.biggest but it now holds the largest of each side across packages** (report 1)
   Each package's sides are sorted longest first, so a box (also sorted) holds every package exactly when each of its sides is at least the largest matching side of any package. One envelope check is the same as checking each package, and holds() can stay as it is.
   Alternatives: Loop over every package in holds() and drop biggest
2. **Note wording: "...holds N cubic inches and every package (up to 6 × 4 × 2.75 in)"** (report 1)
   The envelope can be a size no single package has, so "the biggest package (...)" would describe a package that doesn't exist. The "No box" note says "packages up to ..." the same way.
   Alternatives: Keep the "biggest package" wording

**Summary**

> The box suggestion now checks every package against each box, not just the one with the longest side. It does this by testing the box against the largest longest, middle and shortest sides across all packages, so a long flat pouch with a thicker tin no longer gets the 1.5 in padded mailer. Added a BoxTests test with exactly that pair; all 77 tests in apps/fulfillment/tests pass.


### T76 graphic-design-site-bit

- **Origin:** Written by the user
- **Goal:** Planning
- **Ran:** 2026-11-01 22:54 to 2026-11-01 23:08 (13m 42s)
- **Outcome:** done; committed [`c6ecec10c58c`](https://github.com/wingware-dev/teashop/commit/c6ecec10c58c66dbf65fc9c2be75c5eedca48915)
- **Usage:** 74 input, 61k output, 2.61M cache read, 109k cache write (claude-opus-5-5)
- **Tools:** 35 calls, 6 to Wing's MCP tools (wing-review 6)

**Prompt**

> The graphic design of the site is a bit weak.  I was envisioning much richer natural look, with vines and branches and leaves twining around the edges and between page areas.  The leaves. birds, insects, etc, would be in those vine/branch/leaf areas.  The overall look inspired by elven art, art nouveau, and jugendstil era German children's books.  Can you work up a mockup for me to react to, opening it in my browser when done?
>
> [Tasks Manager, 2026-11-01 22:54] Manager: This is a mockup for the user to react to. Don't change the live templates or CSS yet. Build a standalone HTML page in doc/mockups/ (create it with create_tracked_file) that shows the storefront home page and a product page in the new style. Use hand-built inline SVG for the vines, branches, leaves, birds and insects in the borders and dividers, and keep it original art: no paid or AI image services and no copied artwork. Use the shop's real content from the demo data for the text. Make sure the text stays readable and the layout works at phone width. Check it in a headless browser first, then open it in the user's default browser (e.g. `open <file>`) as they asked. In your report, list the design choices they might want to change (palette, fonts, how dense the ornament is).
>
> See \<project>/.TASKS/notes/the-graphic-design-of-the-site-is-a-bit-weak-i-was-envi.md

**Judgement calls**

1. **Fonts: Federant for headings, Alegreya for body text, loaded from Google Fonts**
   Federant has a Jugendstil feel and Alegreya is a readable book face. They are free, and the page falls back to Optima/Palatino when offline.
   Alternatives: Only system fonts (Optima/Palatino); A blackletter or Eckmann-style face for the wordmark only
2. **The border vines are drawn by a small script from hand-drawn leaf, flower and creature shapes**
   This lets the vines fit any page height and phone width, and lets the mockup offer an ornament-density switch.
   Alternatives: Fixed hand-placed border artwork per page
3. **Added Palette (Spring moss / Autumn russet / Dusk) and Ornament (Sparse / Medium / Lush) switches in the mockup's top bar**
   So you can react to the palette and how dense the ornament is without another round of work.
4. **Text sits on plain cream panels; ornament stays in the gutters and section dividers**
   Keeps the text readable. Nothing is drawn behind body text.

**Summary**

> Added a standalone design mockup, doc/mockups/vine-style.html, showing the storefront home page and the Assam Second Flush product page in a vine-and-leaf style inspired by Art Nouveau and Jugendstil. Vines, leaves, flowers, birds and insects are hand-built inline SVG, and the text is the demo shop's real content. Live templates and CSS are unchanged.


### T77 apply-vine-style-storefront

- **Origin:** Filed by the Tasks Manager from the plan of T76 graphic-design-site-bit
- **Goal:** Planning
- **Ran:** 2026-11-01 23:10 to 2026-11-01 23:29 (18m 24s)
- **Outcome:** done; committed [`8941ec08c835`](https://github.com/wingware-dev/teashop/commit/8941ec08c83595cdb0e0b6683281a8c2a4dcef15)
- **Usage:** 2,060 input, 59k output, 15.01M cache read, 134k cache write (claude-haiku-5-5, claude-opus-5-5)
- **Tools:** 84 calls, 6 to Wing's MCP tools (wing-review 5, wing-testing 1)

**Prompt**

> Apply the chosen vine style to the live storefront
>
> Once the user has reacted to doc/mockups/vine-style.html (T76) and picked a palette, fonts, ornament density, vine weight and card shapes, move the SVG shapes into the motif template tag and base.html, and the CSS into the site stylesheet. Then update the browser screenshots. Wait for the user's choices before starting.
>
> [Tasks Manager, 2026-11-01 23:10] Manager: The user chose Spring moss palette and Medium ornament density (review comment on T76). Keep everything else as in the mockup: Federant headings, Alegreya body, arched cards and pictures, the current vine weight. Drop the palette and density switches; they were for the mockup only. Apply the style across all storefront pages (home, catalog, product, cart, checkout, account, policy pages) without touching the owner back-office pages. Keep text on plain panels and readable at phone width, and keep the existing storefront tests passing. Self-host the two fonts under static/ if their licenses allow (both are OFL), so the site doesn't depend on Google Fonts. Drive the pages in a headless browser, and record new milestone screenshots in doc/shots without recompressing committed ones.
>
> See \<project>/.TASKS/notes/apply-the-chosen-vine-style-to-the-live-storefront.md

**Judgement calls**

1. **Customer pages are those outside /owner/ in the storefront, checkout, email list, support and fulfillment apps**
   Owner pages share base.html, so a flag in the storefront context processor (vine_frame) switches the frame, fonts and paper background on only for customer pages. The staff sign-in and account-security pages keep the plain look too.
   Alternatives: A separate base template for customer pages
2. **Kept dark mode, with dark ornament colours**
   The site already follows the device's theme and has a theme button, and the browser tests check both themes. Spring moss was chosen for the light theme; the dark theme keeps its existing colours, with vines in muted greens and tans.
   Alternatives: Drop dark mode on customer pages
3. **Kept the existing page-design motifs (leaf, bird, bee and so on) as they were and added the frame drawings as separate orn-\* symbols**
   Owner-approved page designs use the motif names and their per-palette colours. Redrawing them would change approved designs.
   Alternatives: Redraw the existing motifs in the mockup's style
4. **The milestone keeps only customer-page shots (184 shots, 64 MB)**
   Earlier milestones kept only the pages their phase changed. The run captured all 356 pages, so I removed the 172 back-office shots: those pages didn't change. The ornament makes each shot larger than before; the phase 3 storefront folder was 38 MB for 117 shots.
   Alternatives: Keep all 356 shots (92 MB); Keep only light-theme or only desktop shots to save space
5. **Fixed product-card and product-page summaries showing as boxed panels**
   The checkout's .summary box style also matched those paragraphs. This dates from phase 4, not this task, but it sat on the cards I was restyling, so I reset it there.
6. **Without JavaScript, the dividers fall back to the old plain vine strip and there is no frame**
   The frame is decoration, and the CSP allows no inline styles, so the script draws it. The page reads the same without it.

**Screenshots**

![account-confirm-sign-in-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/account-confirm-sign-in-phone-light.png)

![account-home-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/account-home-desktop-dark.png)

![account-home-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/account-home-phone-light.png)

![account-link-sent-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/account-link-sent-phone-light.png)

![account-sign-in-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/account-sign-in-phone-light.png)

![checkout-1-cart-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/checkout-1-cart-desktop-dark.png)

![checkout-1-cart-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/checkout-1-cart-phone-light.png)

![checkout-2-address-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/checkout-2-address-desktop-dark.png)

![checkout-2-address-errors-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/checkout-2-address-errors-desktop-dark.png)

![checkout-2-address-errors-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/checkout-2-address-errors-phone-light.png)

![checkout-2-address-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/checkout-2-address-phone-light.png)

![checkout-3-shipping-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/checkout-3-shipping-desktop-dark.png)

![checkout-3-shipping-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/checkout-3-shipping-phone-light.png)

![checkout-4-pay-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/checkout-4-pay-desktop-dark.png)

![checkout-4-pay-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/checkout-4-pay-phone-light.png)

![checkout-5-done-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/checkout-5-done-desktop-dark.png)

![checkout-5-done-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/checkout-5-done-phone-light.png)

![checkout-address-not-shipped-desktop-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/checkout-address-not-shipped-desktop-light.png)

![checkout-cart-empty-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/checkout-cart-empty-desktop-dark.png)

![checkout-cart-empty-desktop-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/checkout-cart-empty-desktop-light.png)

![checkout-cart-empty-phone-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/checkout-cart-empty-phone-dark.png)

![checkout-cart-empty-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/checkout-cart-empty-phone-light.png)

![collection-this-weeks-picks-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/collection-this-weeks-picks-desktop-dark.png)

![collection-this-weeks-picks-desktop-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/collection-this-weeks-picks-desktop-light.png)

![collection-this-weeks-picks-phone-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/collection-this-weeks-picks-phone-dark.png)

![collection-this-weeks-picks-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/collection-this-weeks-picks-phone-light.png)

![coming-soon-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/coming-soon-desktop-dark.png)

![coming-soon-desktop-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/coming-soon-desktop-light.png)

![coming-soon-phone-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/coming-soon-phone-dark.png)

![coming-soon-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/coming-soon-phone-light.png)

![emaillist-confirm-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/emaillist-confirm-desktop-dark.png)

![emaillist-confirm-desktop-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/emaillist-confirm-desktop-light.png)

![emaillist-confirm-phone-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/emaillist-confirm-phone-dark.png)

![emaillist-confirm-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/emaillist-confirm-phone-light.png)

![emaillist-flow-check-email-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/emaillist-flow-check-email-phone-light.png)

![emaillist-flow-confirmed-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/emaillist-flow-confirmed-phone-light.png)

![emaillist-flow-frequency-saved-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/emaillist-flow-frequency-saved-phone-light.png)

![emaillist-flow-unsubscribed-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/emaillist-flow-unsubscribed-phone-light.png)

![emaillist-manage-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/emaillist-manage-desktop-dark.png)

![emaillist-manage-desktop-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/emaillist-manage-desktop-light.png)

![emaillist-manage-phone-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/emaillist-manage-phone-dark.png)

![emaillist-manage-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/emaillist-manage-phone-light.png)

![emaillist-sign-up-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/emaillist-sign-up-desktop-dark.png)

![emaillist-sign-up-desktop-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/emaillist-sign-up-desktop-light.png)

![emaillist-sign-up-phone-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/emaillist-sign-up-phone-dark.png)

![emaillist-sign-up-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/emaillist-sign-up-phone-light.png)

![emaillist-unsubscribe-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/emaillist-unsubscribe-desktop-dark.png)

![emaillist-unsubscribe-desktop-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/emaillist-unsubscribe-desktop-light.png)

![emaillist-unsubscribe-phone-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/emaillist-unsubscribe-phone-dark.png)

![emaillist-unsubscribe-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/emaillist-unsubscribe-phone-light.png)

![emaillist-unsubscribed-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/emaillist-unsubscribed-desktop-dark.png)

![emaillist-unsubscribed-desktop-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/emaillist-unsubscribed-desktop-light.png)

![emaillist-unsubscribed-phone-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/emaillist-unsubscribed-phone-dark.png)

![emaillist-unsubscribed-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/emaillist-unsubscribed-phone-light.png)

![fulfillment-delay-answer-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/fulfillment-delay-answer-desktop-dark.png)

![fulfillment-delay-answer-desktop-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/fulfillment-delay-answer-desktop-light.png)

![fulfillment-delay-answer-phone-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/fulfillment-delay-answer-phone-dark.png)

![fulfillment-delay-answer-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/fulfillment-delay-answer-phone-light.png)

![menu-teas-open-desktop-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/menu-teas-open-desktop-light.png)

![merch-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/merch-desktop-dark.png)

![merch-desktop-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/merch-desktop-light.png)

![merch-phone-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/merch-phone-dark.png)

![merch-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/merch-phone-light.png)

![merch-product-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/merch-product-desktop-dark.png)

![merch-product-desktop-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/merch-product-desktop-light.png)

![merch-product-phone-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/merch-product-phone-dark.png)

![merch-product-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/merch-product-phone-light.png)

![policy-accessibility-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/policy-accessibility-desktop-dark.png)

![policy-accessibility-desktop-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/policy-accessibility-desktop-light.png)

![policy-accessibility-phone-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/policy-accessibility-phone-dark.png)

![policy-accessibility-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/policy-accessibility-phone-light.png)

![policy-privacy-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/policy-privacy-desktop-dark.png)

![policy-privacy-desktop-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/policy-privacy-desktop-light.png)

![policy-privacy-phone-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/policy-privacy-phone-dark.png)

![policy-privacy-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/policy-privacy-phone-light.png)

![policy-returns-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/policy-returns-desktop-dark.png)

![policy-returns-desktop-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/policy-returns-desktop-light.png)

![policy-returns-phone-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/policy-returns-phone-dark.png)

![policy-returns-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/policy-returns-phone-light.png)

![policy-shipping-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/policy-shipping-desktop-dark.png)

![policy-shipping-desktop-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/policy-shipping-desktop-light.png)

![policy-shipping-phone-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/policy-shipping-phone-dark.png)

![policy-shipping-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/policy-shipping-phone-light.png)

![policy-subscriptions-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/policy-subscriptions-desktop-dark.png)

![policy-subscriptions-desktop-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/policy-subscriptions-desktop-light.png)

![policy-subscriptions-phone-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/policy-subscriptions-phone-dark.png)

![policy-subscriptions-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/policy-subscriptions-phone-light.png)

![policy-terms-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/policy-terms-desktop-dark.png)

![policy-terms-desktop-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/policy-terms-desktop-light.png)

![policy-terms-phone-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/policy-terms-phone-dark.png)

![policy-terms-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/policy-terms-phone-light.png)

![product-allergens-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/product-allergens-desktop-dark.png)

![product-allergens-desktop-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/product-allergens-desktop-light.png)

![product-allergens-phone-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/product-allergens-phone-dark.png)

![product-allergens-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/product-allergens-phone-light.png)

![product-buy-box-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/product-buy-box-desktop-dark.png)

![product-buy-box-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/product-buy-box-phone-light.png)

![product-design-story-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/product-design-story-phone-light.png)

![product-design-wide-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/product-design-wide-desktop-dark.png)

![product-design-wide-desktop-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/product-design-wide-desktop-light.png)

![product-design-wide-phone-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/product-design-wide-phone-dark.png)

![product-design-wide-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/product-design-wide-phone-light.png)

![product-herbal-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/product-herbal-desktop-dark.png)

![product-herbal-desktop-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/product-herbal-desktop-light.png)

![product-herbal-phone-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/product-herbal-phone-dark.png)

![product-herbal-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/product-herbal-phone-light.png)

![product-organic-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/product-organic-desktop-dark.png)

![product-organic-desktop-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/product-organic-desktop-light.png)

![product-organic-phone-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/product-organic-phone-dark.png)

![product-organic-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/product-organic-phone-light.png)

![product-photos-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/product-photos-desktop-dark.png)

![product-photos-desktop-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/product-photos-desktop-light.png)

![product-photos-phone-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/product-photos-phone-dark.png)

![product-photos-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/product-photos-phone-light.png)

![region-darjeeling-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/region-darjeeling-desktop-dark.png)

![region-darjeeling-desktop-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/region-darjeeling-desktop-light.png)

![region-darjeeling-phone-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/region-darjeeling-phone-dark.png)

![region-darjeeling-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/region-darjeeling-phone-light.png)

![regions-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/regions-desktop-dark.png)

![regions-desktop-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/regions-desktop-light.png)

![regions-phone-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/regions-phone-dark.png)

![regions-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/regions-phone-light.png)

![search-no-results-phone-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/search-no-results-phone-dark.png)

![search-no-results-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/search-no-results-phone-light.png)

![search-results-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/search-results-desktop-dark.png)

![search-results-desktop-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/search-results-desktop-light.png)

![search-results-phone-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/search-results-phone-dark.png)

![search-results-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/search-results-phone-light.png)

![shop-home-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/shop-home-desktop-dark.png)

![shop-home-desktop-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/shop-home-desktop-light.png)

![shop-home-phone-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/shop-home-phone-dark.png)

![shop-home-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/shop-home-phone-light.png)

![subscription-cancel-phone-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/subscription-cancel-phone-dark.png)

![subscription-cancelled-phone-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/subscription-cancelled-phone-dark.png)

![subscription-card-cancelled-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/subscription-card-cancelled-phone-light.png)

![subscription-card-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/subscription-card-desktop-dark.png)

![subscription-card-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/subscription-card-phone-light.png)

![subscription-card-updated-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/subscription-card-updated-desktop-dark.png)

![subscription-card-updated-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/subscription-card-updated-phone-light.png)

![subscription-no-consent-phone-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/subscription-no-consent-phone-dark.png)

![subscription-pay-phone-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/subscription-pay-phone-dark.png)

![subscription-plans-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/subscription-plans-desktop-dark.png)

![subscription-plans-desktop-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/subscription-plans-desktop-light.png)

![subscription-plans-phone-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/subscription-plans-phone-dark.png)

![subscription-plans-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/subscription-plans-phone-light.png)

![subscription-sign-up-phone-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/subscription-sign-up-phone-dark.png)

![subscription-welcome-phone-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/subscription-welcome-phone-dark.png)

![support-chat-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/support-chat-desktop-dark.png)

![support-chat-desktop-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/support-chat-desktop-light.png)

![support-chat-phone-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/support-chat-phone-dark.png)

![support-chat-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/support-chat-phone-light.png)

![support-chat-start-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/support-chat-start-desktop-dark.png)

![support-chat-start-desktop-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/support-chat-start-desktop-light.png)

![support-chat-start-phone-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/support-chat-start-phone-dark.png)

![support-chat-start-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/support-chat-start-phone-light.png)

![support-flow-chat-answered-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/support-flow-chat-answered-phone-light.png)

![support-flow-chat-waiting-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/support-flow-chat-waiting-phone-light.png)

![tea-note-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/tea-note-desktop-dark.png)

![tea-note-desktop-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/tea-note-desktop-light.png)

![tea-note-phone-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/tea-note-phone-dark.png)

![tea-note-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/tea-note-phone-light.png)

![tea-notes-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/tea-notes-desktop-dark.png)

![tea-notes-desktop-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/tea-notes-desktop-light.png)

![tea-notes-phone-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/tea-notes-phone-dark.png)

![tea-notes-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/tea-notes-phone-light.png)

![teas-all-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/teas-all-desktop-dark.png)

![teas-all-desktop-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/teas-all-desktop-light.png)

![teas-all-phone-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/teas-all-phone-dark.png)

![teas-all-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/teas-all-phone-light.png)

![teas-category-black-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/teas-category-black-desktop-dark.png)

![teas-category-black-desktop-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/teas-category-black-desktop-light.png)

![teas-category-black-phone-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/teas-category-black-phone-dark.png)

![teas-category-black-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/teas-category-black-phone-light.png)

![teas-category-herbal-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/teas-category-herbal-desktop-dark.png)

![teas-category-herbal-desktop-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/teas-category-herbal-desktop-light.png)

![teas-category-herbal-phone-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/teas-category-herbal-phone-dark.png)

![teas-category-herbal-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/teas-category-herbal-phone-light.png)

![teas-filtered-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/teas-filtered-desktop-dark.png)

![teas-filtered-desktop-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/teas-filtered-desktop-light.png)

![teas-filtered-phone-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/teas-filtered-phone-dark.png)

![teas-filtered-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/teas-filtered-phone-light.png)

![teas-filtered-phone-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/teas-filtered-phone-phone-light.png)

![theme-chosen-dark-desktop-dark.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/theme-chosen-dark-desktop-dark.png)

![theme-chosen-light-on-dark-device-phone-light.png](https://github.com/wingware-dev/teashop/raw/8941ec08c83595cdb0e0b6683281a8c2a4dcef15/doc/shots/2026-11-01-vine-style/theme-chosen-light-on-dark-device-phone-light.png)

**Summary**

> Applied the vine-and-leaf style (Spring moss, medium ornament) to every customer page; the owner's back office keeps its plain look.
> - Customer pages sit on a sheet framed by twining vines with leaves, flowers, birds and insects (new static/js/vines.js). Leafy dividers separate page areas and a strip of grass and ferns sits above the footer. Text stays on plain panels.
> - The leaf, flower and creature drawings are new orn-* symbols in static/img/motifs.svg. A new `ornament` template tag places them. The home and coming-soon pages get an arched picture of a flowering tea branch with a songbird.
> - Federant headings and Alegreya text are self-hosted in static/fonts/ with their OFL licences. Cards, tiles, fact panels and the product picture have arched tops. Dark mode has its own ornament colours.
> - Fixed product-card and product-page summaries that had picked up the checkout summary's box styling.
> - New tests in apps/storefront/tests/test_vine_frame.py. New milestone screenshots of the customer pages are in doc/shots/2026-11-01-vine-style.


### T80 regression-sweep-vine-style

- **Origin:** Filed by the Tasks Manager
- **Goal:** Found
- **Ran:**  to 2026-11-01 23:29 ()
- **Outcome:** obsolete
- **Usage:** not recorded
- **Tools:** not recorded (no transcript)

**Prompt**

> Regression sweep after the vine style
>
> Run the whole test suite in one test_run. T77 (8941ec0) changed templates/base.html, static/css/site.css, the storefront template tags and context processor, which every page uses. Report pass/fail counts. Fix failures caused by T77 only if the fix is small and clearly right; otherwise file each one as a finding. Don't change screenshots.


### T81 regression-sweep-vine-style

- **Origin:** Filed by the Tasks Manager
- **Goal:** Planning
- **Ran:** 2026-11-01 23:29 to 2026-11-01 23:38 (8m 40s)
- **Outcome:** done
- **Usage:** 1,721 input, 4,546 output, 449k cache read, 35k cache write (claude-haiku-5-5, claude-opus-5-5)
- **Tools:** 11 calls, 6 to Wing's MCP tools (wing-review 4, wing-testing 2)

**Prompt**

> Regression sweep after the vine style
>
> Run the whole test suite in one test_run. T77 (8941ec0) changed templates/base.html, static/css/site.css, the storefront template tags and context processor, which every page uses. Report pass/fail counts. Fix failures caused by T77 only if the fix is small and clearly right; otherwise file each one as a finding. Don't change screenshots.
>
> See \<project>/.TASKS/notes/regression-sweep-after-the-vine-style.md

**Judgement calls**

1. **Filed the failing test as a finding instead of fixing it**
   It wasn't caused by T77, and the task says to fix in place only T77-caused failures. This session is also in plan mode, which blocks edits.
   Alternatives: Fix the test now to use local calendar dates

**Verdict:** Check found issues; filed T82 fix-shipped-tab-test-dst

- T82 fix-shipped-tab-test-dst: Shipped-tab lateness test fails when run in the hour after a DST fall-back day ends

**Summary**

> Ran the full suite once, after T77 vine style (8941ec0): 834 tests, 832 passed, 1 failed, 1 skipped. No failures came from T77.
> - The one failure, OwnerPagesTests.test_shipped_tab_judges_lateness_by_the_ship_date, is a fragile test, not a regression. It builds "shipped yesterday" by subtracting 24 hours, and on the 25-hour DST fall-back day (run at Nov 1 23:38 EST) that lands on the same local date. Filed as T82 fix-shipped-tab-test-dst (18d295da).
> - Nothing was fixed in place and no screenshots were changed.


### T82 fix-shipped-tab-test-dst

- **Origin:** Found by T81 regression-sweep-vine-style
- **Goal:** Bug Fixes
- **Ran:** 2026-11-01 23:38 to 2026-11-01 23:40 (1m 32s)
- **Outcome:** done; committed [`2427b2c83ffd`](https://github.com/wingware-dev/teashop/commit/2427b2c83ffddcb27fb7783f011b79520088d264)
- **Usage:** 22 input, 2,792 output, 616k cache read, 5,645 cache write (claude-opus-5-5)
- **Tools:** 7 calls, 3 to Wing's MCP tools (wing-review 2, wing-testing 1)

**Prompt**

> Shipped-tab lateness test fails when run in the hour after a DST fall-back day ends
>
> apps/fulfillment/tests/test_views.py::OwnerPagesTests.test_shipped_tab_judges_lateness_by_the_ship_date makes "shipped yesterday" as `timezone.now() - timedelta(days=1)` (24 hours), but the view (apps/fulfillment/views.py:56) judges by `timezone.localdate(order.shipped_at)` in America/New_York. On a 25-hour DST fall-back day, 24 hours before a late-evening "now" is still the same calendar day, so the late order counts as shipped today, 3 days after ship_by rather than the 2 the test expects. Here "now" was Sun Nov 1 2026 23:38 EST, which is 04:38 UTC on Nov 2. Subtract 24h and you get Nov 1 00:38 EDT, which is still Nov 1 in local time. The product code is right; the test is fragile. The same pattern (`now - timedelta(days=4)`) for the on-time order could misfire the same way. Suggested fix: build shipped_at from local calendar dates, e.g. noon local time on `timezone.localdate() - timedelta(days=1)` (and `days=4`) made aware with `timezone.make_aware(datetime.combine(d, time(12)))`. Also use `timezone.localdate()` instead of `date.today()` for ship_by. Found by task T81 regression-sweep-vine-style (37123d24). It is not caused by T77's vine style (8941ec0), which doesn't touch fulfillment or owner pages. The test came in with 418808b.
>
> Evidence: Full run and a solo rerun both fail (reproducible alone at Sun Nov 1 2026 23:38 EST; it should pass again after local midnight):
>   test_views.py:60 in test_shipped_tab_judges_lateness_by_the_ship_date
>     self.assertIn("(2 days after)", rows[late]["status_text"])
>   AssertionError: '(2 days after)' not found in 'Shipped late: promised Thu Oct 29 (3 days after)'
> Test: apps/fulfillment/tests/test_views.py lines 48-61; view: apps/fulfillment/views.py:53-56 (timezone.localdate(order.shipped_at)); settings TIME_ZONE America/New_York (config/settings.py:203).
>
> Suggested next step: fix
>
> [Tasks Manager, 2026-11-01 23:38] Manager: Change only apps/fulfillment/tests/test_views.py, as suggested: build shipped_at from local calendar dates (noon local time) and use timezone.localdate() for ship_by. Also scan the other fulfillment tests for the same now - timedelta(days=N) pattern compared to local dates, and fix any you find. The T81 sweep is running read-only at the same time. Run apps/fulfillment/tests once at the end.
>
> See \<project>/.TASKS/notes/shipped-tab-lateness-test-fails-when-run-in-the-hour-afte.md

**Summary**

> The shipped-tab lateness test now sets shipped_at to noon local time on calendar days (via timezone.make_aware(datetime.combine(...))) and takes ship_by from timezone.localdate(), not 24-hour offsets from now and date.today(). It no longer fails on a 25-hour DST fall-back day. All 77 apps/fulfillment/tests pass, run at Sun Nov 1 2026 23:38 EST, inside the window where the test used to fail.


### T83 fulfillment-tests-localdate

- **Origin:** Filed by the Tasks Manager
- **Goal:** Bug Fixes
- **Ran:** 2026-11-01 23:40 to 2026-11-01 23:43 (2m 51s)
- **Outcome:** done; committed [`5eacc2cfb9d9`](https://github.com/wingware-dev/teashop/commit/5eacc2cfb9d92676ed62983107e3f4abbf6a2b61)
- **Usage:** 1,908 input, 5,910 output, 1.47M cache read, 11k cache write (claude-haiku-5-5, claude-opus-5-5)
- **Tools:** 26 calls, 5 to Wing's MCP tools (wing-review 3, wing-testing 2)

**Prompt**

> Use timezone.localdate() instead of date.today() in the fulfillment tests
>
> test_views.py, test_services.py and apps/fulfillment/testing.py (paid_order's default ship_by) use date.today(), which is the machine's time zone, while the code judges by timezone.localdate() in America/New_York. On a machine in another time zone (e.g. a UTC GitHub Actions runner) lateness tests near midnight could be off by a day. Switch them to timezone.localdate() and run apps/fulfillment/tests once. Test-only change.

**Messages from the Tasks Manager**

- 2026-11-01 23:42: , which arrived as you finished: Manager: no other writer is active. Please run apps/support/tests and apps/marketing/tests/test_posting.py together in one test_run, fix anything your change broke, then report again. Carry on with the task if this changes anything, and end with task_report again.

**Judgement calls**

1. **Also changed apps/fulfillment/tests/test_ui.py and the scale dates in testing.py** (report 1)
   test_ui.py's sample orders set ship_by from date.today() the same way, which risks the same off-by-one-day failure. The scale's seal and inspection dates are compared with timezone.localdate() by Scale.inspection_overdue. The task named only test_views.py, test_services.py and paid_order's default.
   Alternatives: Change only the files the task named

**Summary**

> The fulfillment tests and their builders now take today from timezone.localdate() (the shop's America/New_York date) instead of date.today() (the machine's), so lateness tests near midnight agree with the code on machines in other time zones. Test-only change; all 77 apps/fulfillment/tests pass, and so do the 75 support and marketing posting tests that use the builders.


## Tasks Manager

### Questions to the user

Q2. T2 phase1-infrastructure-skeleton (edd0e993) set the project's main entry point to 'Run dev server' (manage.py runserver on 127.0.0.1:8000). To start the site locally, use the toolbar's Debug button or Debug > Start / Continue. Before the first run, pick 'Migrate dev database' from the entry-point drop-down left of Run/Debug (or Debug > Debug Named Entry Point) to set up the database. (2026-11-01 18:19)

   **Answer:** Got it

Q3. Do you approve creating the hosting accounts so the real server can be set up? T14 provision-server (cbcf7761) needs a VPS (about $10-30/month) and Backblaze B2 backup storage (about $1-5/month), plus free plans for GitHub, Cloudflare, an uptime monitor, healthchecks.io and Sentry. The list and setup steps are in docs/ops/README.md. You would sign up and pay for the accounts yourself; a task then does the setup. Nothing else is blocked on this: development continues locally either way. (2026-11-01 18:19)

   **Answer:** Later, closer to launch

Q4. After the first deploy that includes T29 background-job-queue, run install-app.sh on the server again. That removes the old order-summary and subscription-reminder systemd timers, which the new job worker replaces. Until you do, the 6pm order summary may arrive twice. Nothing is deployed yet, so this is only a reminder for that deploy. (2026-11-01 20:43)

   **Answer:** Let's keep deployment notes; initially we're writing/testing everything here on dev.  Deployment is much later.

Q6. The AI agents (support now; marketing and ops next) run on a free offline stand-in until they get a Claude API key. Workers think the $100/month Claude subscription covers you using Claude yourself, not a program answering customers around the clock. That would mean a separate Anthropic API account, billed per use: about $20–100 a month at small volume, capped at $50 a month in the code by default. Please check Anthropic's current terms. Until you decide, everything stays on the stand-in. Do you want to open an API account and approve one short live test of the support agent? That would be about a dozen sample questions, well under $1. (2026-11-01 21:29)

   **Answer:** Later; keep the stand-in for now

### Decisions

| Time | Change | Task | Detail |
|---|---|---|---|
| 2026-11-01 17:19 | annotate_task | T1 see-file-teashop-txt | Added a note: Manager: This is a read-only assessment and report, not code yet. Read teashop.txt in the project root. Report back with: (a) a fuller version of the requirements, including things the user may have forgotten; (b) feasibility per capability (1)-(6) and for the agent automation, with bu |
| 2026-11-01 17:19 | queue_assign | T1 see-file-teashop-txt | Queued in Research: Teashop assessment |
| 2026-11-01 17:48 | propose_tasks | T2 phase1-infrastructure-skeleton | Filed as a Draft at your request |
| 2026-11-01 17:48 | propose_tasks | T3 ui-test-harness | Filed as a Draft at your request |
| 2026-11-01 17:48 | propose_tasks | T4 phase2-catalog-inventory-core | Filed as a Draft at your request |
| 2026-11-01 17:48 | propose_tasks | T5 phase3-storefront-design | Filed as a Draft at your request |
| 2026-11-01 17:48 | propose_tasks | T6 phase4-cart-checkout | Filed as a Draft at your request |
| 2026-11-01 17:48 | propose_tasks | T7 phase5-fulfillment-dashboard | Filed as a Draft at your request |
| 2026-11-01 17:48 | propose_tasks | T8 phase6-owner-dashboard-reporting | Filed as a Draft at your request |
| 2026-11-01 17:48 | propose_tasks | T9 phase7-purchasing-loss-tracking | Filed as a Draft at your request |
| 2026-11-01 17:48 | propose_tasks | T10 phase8-email-list | Filed as a Draft at your request |
| 2026-11-01 17:48 | propose_tasks | T11 phase9-support-agent | Filed as a Draft at your request |
| 2026-11-01 17:48 | propose_tasks | T12 phase10-marketing-agent | Filed as a Draft at your request |
| 2026-11-01 17:48 | propose_tasks | T13 phase11-ops-security-agent | Filed as a Draft at your request |
| 2026-11-01 17:50 | queue_assign | T2 phase1-infrastructure-skeleton | Queued in Foundation |
| 2026-11-01 18:19 | annotate_task | T3 ui-test-harness | Added a note: From T2 phase1-infrastructure-skeleton (edd0e993): build on apps/core/testing.py for signed-in pages (an owner with a TOTP device, verified login, current_token). Headless Chrome screenshots of the light theme (--blink-settings=preferredColorScheme=1) and the dark theme already work ag |
| 2026-11-01 18:19 | annotate_task | T4 phase2-catalog-inventory-core | Added a note: From T2 phase1-infrastructure-skeleton (edd0e993): follow docs/architecture.md. Put new apps under apps/ and add them to LOCAL_APPS in config/settings.py. Back-office views use apps.core.decorators.owner_required, and tests use apps.core.testing (make_owner, login_verified). Model chan |
| 2026-11-01 18:19 | annotate_task | T8 phase6-owner-dashboard-reporting | Added a note: From T2 phase1-infrastructure-skeleton (edd0e993): the owner dashboard already exists in apps/core (views.owner_dashboard, templates/core/owner_dashboard.html), with a placeholder 'Needs your attention' section and recent audit events. Extend it there or move it into a dashboard app. F |
| 2026-11-01 18:19 | annotate_task | T13 phase11-ops-security-agent | Added a note: From T2 phase1-infrastructure-skeleton (edd0e993): deploy/server/harden.sh creates the server accounts (admin with sudo, and deploy with Docker access). The agent's limited account and its sudo allow-list still need to be added there. Agent actions should run inside apps.audit.acting_a |
| 2026-11-01 18:19 | propose_tasks | T15 record-ops-events | Proposed as a Draft |
| 2026-11-01 18:19 | mark_ready | T15 record-ops-events | Made Ready as a follow-up of 'Phase 1: infrastructure skeleton (Django project, VPS har...': Completes the audit logging T2 phase1-infrastructure-skeleton (edd0e993) built. Its deploy and backup scripts don't record anything in it yet. |
| 2026-11-01 18:19 | annotate_task | T6 phase4-cart-checkout | Added a note: From T2 phase1-infrastructure-skeleton (edd0e993)'s follow-ups: add a Content-Security-Policy header, using django-csp since the project stays on Django 5.2 LTS. Cover the storefront's assets, and allow Stripe's script and frame domains. |
| 2026-11-01 18:19 | queue_assign | T3 ui-test-harness | Queued in Foundation |
| 2026-11-01 18:20 | queue_assign | T4 phase2-catalog-inventory-core | Queued in Inventory |
| 2026-11-01 18:25 | propose_tasks | T17 pin-ui-test-packages | Proposed as a Draft |
| 2026-11-01 18:25 | mark_ready | T17 pin-ui-test-packages | Made Ready as a follow-up of 'Harness for driving the website as a user would, with mil...': Locks the browser-test packages that T3 ui-test-harness (0223cfbe) added, matching how the project's other dependencies are locked. |
| 2026-11-01 18:25 | queue_assign | T15 record-ops-events | Queued in Foundation |
| 2026-11-01 18:31 | annotate_task | T8 phase6-owner-dashboard-reporting | Added a note: From T15 record-ops-events (29373a71): move the failed or overdue ops items out of owner_dashboard.html and into an attention provider registered in AuditConfig.ready(). apps.audit.ops.ops_status already computes needs_attention. Use the attention registry in apps/core/attention.py (fr |
| 2026-11-01 18:37 | annotate_task | T7 phase5-fulfillment-dashboard | Added a note: From T4 phase2-catalog-inventory-core (4d8a1a2b): packing uses catalog.services.pack(), which packs one package per order from a single lot, and label_for() gives the label facts. This task also needs to: - turn label_for() into a printable label (PDF or label-printer format); - warn b |
| 2026-11-01 18:37 | annotate_task | T9 phase7-purchasing-loss-tracking | Added a note: From T4 phase2-catalog-inventory-core (4d8a1a2b): suppliers, simple purchase orders with receipts (including partial deliveries) and stock adjustments with reasons already exist in apps/inventory. Samples and giveaways already count as marketing, not loss. Build reorder points, draft P |
| 2026-11-01 18:37 | propose_tasks | T19 regression-tests-foundation-inventory | Proposed as a Draft |
| 2026-11-01 18:37 | mark_ready | T19 regression-tests-foundation-inventory | Made Ready as a follow-up of 'Phase 1: infrastructure skeleton (Django project, VPS har...': T4 and T15 asked for one full run of the suite once both are committed, since both changed the dashboard view and template. |
| 2026-11-01 18:38 | queue_assign | T19 regression-tests-foundation-inventory | Queued in Research: Regression tests |
| 2026-11-01 18:38 | queue_assign | T5 phase3-storefront-design | Queued in Storefront |
| 2026-11-01 18:38 | queue_assign | T9 phase7-purchasing-loss-tracking | Queued in Inventory |
| 2026-11-01 18:38 | queue_assign | T17 pin-ui-test-packages | Queued in Foundation |
| 2026-11-01 18:40 | propose_tasks | T20 pin-pip-audit-ci | Proposed as a Draft |
| 2026-11-01 18:40 | mark_ready | T20 pin-pip-audit-ci | Made Ready as a follow-up of 'Pin the browser-test packages with hashes': Finishes T17 pin-ui-test-packages (a454368b)'s work: this is the last CI install without a version or hashes. |
| 2026-11-01 18:40 | queue_assign | T20 pin-pip-audit-ci | Queued in Foundation |
| 2026-11-01 18:41 | mark_carried | T21 pillow-vulnerable-pin | Being done by task T5 phase3-storefront-design (ea7f0526): The vulnerable Pillow pin is in T5 phase3-storefront-design (ea7f0526)'s uncommitted work, which I've told to fix it. |
| 2026-11-01 18:52 | annotate_task | T8 phase6-owner-dashboard-reporting | Added a note: From T9 phase7-purchasing-loss-tracking (ca29736e): this task also needs to (1) add per-order shipping charged, postage paid and Stripe fees, recorded by checkout, to the profit report in apps/purchasing, so margin is per order rather than landed cost only; and (2) send the daily remin |
| 2026-11-01 19:05 | mark_ready | T24 pass-label-settings-to-container | Made Ready as a follow-up of 'Phase 3: storefront design system and catalog pages': A bug in deploy config that T2 and T4 just wrote: labels on the server could never include the required packer address. |
| 2026-11-01 19:05 | queue_assign | T24 pass-label-settings-to-container | Queued in Foundation |
| 2026-11-01 19:05 | move_task | T24 pass-label-settings-to-container | Moved from Bug Fixes to goal 'Planning' |
| 2026-11-01 19:15 | annotate_task | T6 phase4-cart-checkout | Added a note: From T5 phase3-storefront-design (ea7f0526): - Product pages show sizes and prices, with an 'Online ordering opens soon' notice in the buy box (apps/storefront/templates/storefront/product.html). Replace that notice with the add-to-cart form. - The pages now have no inline scripts or s |
| 2026-11-01 19:15 | propose_tasks | T25 organic-wording-product-pages | Proposed as a Draft |
| 2026-11-01 19:15 | propose_tasks | T26 shrink-milestone-screenshots | Proposed as a Draft |
| 2026-11-01 19:15 | mark_ready | T25 organic-wording-product-pages | Made Ready as a follow-up of 'Phase 3: storefront design system and catalog pages': A labelling-compliance gap in the product pages T5 phase3-storefront-design (ea7f0526) built. |
| 2026-11-01 19:15 | mark_ready | T26 shrink-milestone-screenshots | Made Ready as a follow-up of 'Phase 3: storefront design system and catalog pages': T5 phase3-storefront-design (ea7f0526)'s milestone added 39 MB of screenshots to the repository, and each later milestone adds more. Fix it before the next milestone. |
| 2026-11-01 19:15 | queue_assign | T6 phase4-cart-checkout | Queued in Storefront |
| 2026-11-01 19:15 | queue_assign | T26 shrink-milestone-screenshots | Queued in Foundation |
| 2026-11-01 19:20 | tell_worker | T26 shrink-milestone-screenshots | Reopened it from Review: From the Manager: as you pointed out, committing recompressed copies of the existing screenshots adds about 27 MB to git history to save 12 MB in the checkout, which is a net loss. My task text asked for it, and that was a mistake. Please restore the existing PNGs under doc/ |
| 2026-11-01 19:50 | propose_tasks | T29 background-job-queue | Proposed as a Draft |
| 2026-11-01 19:50 | propose_tasks | T30 shared-rate-limit-cache | Proposed as a Draft |
| 2026-11-01 19:50 | propose_tasks | T31 subscription-card-update | Proposed as a Draft |
| 2026-11-01 19:50 | mark_ready | T29 background-job-queue | Made Ready as a follow-up of 'Phase 4: cart and checkout': T6 phase4-cart-checkout (e36d1a1d)'s emails have no automatic retry, and fulfillment, the email list and owner reminders all need queued sending. |
| 2026-11-01 19:50 | mark_ready | T30 shared-rate-limit-cache | Made Ready as a follow-up of 'Phase 4: cart and checkout': A bug in T6 phase4-cart-checkout (e36d1a1d)'s bot protection: the rate limit isn't shared between server processes. |
| 2026-11-01 19:50 | mark_ready | T31 subscription-card-update | Made Ready as a follow-up of 'Phase 4: cart and checkout': A gap in T6 phase4-cart-checkout (e36d1a1d)'s subscriptions: a customer with a failed renewal can't fix it online. |
| 2026-11-01 19:50 | propose_tasks | T33 regression-tests-after-checkout | Proposed as a Draft |
| 2026-11-01 19:50 | mark_ready | T33 regression-tests-after-checkout | Made Ready as a follow-up of 'Phase 4: cart and checkout': T6 asked for the other apps' browser and accessibility tests to be rerun, since it changed every page's header, footer, styles and security headers. |
| 2026-11-01 19:50 | queue_assign | T33 regression-tests-after-checkout | Queued in Research: Regression tests |
| 2026-11-01 19:54 | mark_ready | T34 compose-checkout-env-vars | Made Ready as a follow-up of 'Regression tests after the checkout phase': Breaks 2 deploy tests: T6 phase4-cart-checkout (e36d1a1d)'s checkout settings never reach the app container on the server. |
| 2026-11-01 19:54 | move_task | T34 compose-checkout-env-vars | Moved from Bug Fixes to goal 'Planning' |
| 2026-11-01 19:55 | mark_ready | T35 checkout-deploy-checks-break-settings | Made Ready as a follow-up of 'Regression tests after the checkout phase': Fails a production-settings test: T6 phase4-cart-checkout (e36d1a1d)'s new checks warn about settings the test never sets. |
| 2026-11-01 19:55 | move_task | T35 checkout-deploy-checks-break-settings | Moved from Bug Fixes to goal 'Planning' |
| 2026-11-01 19:55 | queue_assign | T34 compose-checkout-env-vars | Queued in Foundation |
| 2026-11-01 19:55 | queue_assign | T25 organic-wording-product-pages | Queued in Storefront |
| 2026-11-01 19:55 | queue_assign | T7 phase5-fulfillment-dashboard | Queued in Fulfillment |
| 2026-11-01 19:56 | queue_assign | T35 checkout-deploy-checks-break-settings | Queued in Foundation |
| 2026-11-01 19:58 | queue_assign | T30 shared-rate-limit-cache | Queued in Foundation |
| 2026-11-01 19:58 | annotate_task | T30 shared-rate-limit-cache | Added a note: Manager: use Django's DatabaseCache (no Redis; nothing new to run on the VPS). Run `createcachetable` wherever migrate runs: the deploy/install scripts, the "Migrate dev database" entry point and the test setup. Add a test showing two separate cache clients share the count. T7 (fulfill |
| 2026-11-01 19:59 | annotate_task | T31 subscription-card-update | Added a note: Manager: T7 (fulfillment) and T30 (rate-limit cache in apps/checkout/protection.py) are running at the same time. If you must change apps/checkout/emails.py, change only the payment-failed email's link and keep every function's call signature, because T29 will move these sends onto a j |
| 2026-11-01 19:59 | queue_assign | T31 subscription-card-update | Queued in Storefront |
| 2026-11-01 20:26 | propose_tasks | T41 net-refunds-from-tax-reports | Proposed as a Draft |
| 2026-11-01 20:26 | mark_ready | T41 net-refunds-from-tax-reports | Made Ready as a follow-up of 'Phase 5: fulfillment dashboard': Gaps T7's refunds and package reversal leave in existing reports |
| 2026-11-01 20:26 | propose_tasks | T42 net-returns-from-reorder-use | Proposed as a Draft |
| 2026-11-01 20:26 | mark_ready | T42 net-returns-from-reorder-use | Made Ready as a follow-up of 'Phase 5: fulfillment dashboard': Gaps T7's refunds and package reversal leave in existing reports |
| 2026-11-01 20:27 | annotate_task | T29 background-job-queue | Added a note: Manager: T7 phase5-fulfillment-dashboard (d598b6a8, committed ddec0b2) added more senders and timers. These are the shipping/tracking email, delay notices, `send_order_summary` with its 6pm systemd timer, and the T31 card-update link in the payment-failed email. Move these onto the job |
| 2026-11-01 20:27 | queue_assign | T29 background-job-queue | Queued in Jobs and email |
| 2026-11-01 20:27 | queue_assign | T41 net-refunds-from-tax-reports | Queued in Report corrections |
| 2026-11-01 20:31 | propose_tasks | T44 refund-records-tax | Proposed as a Draft |
| 2026-11-01 20:31 | mark_ready | T44 refund-records-tax | Made Ready as a follow-up of 'Net refunds out of sales-tax and nexus figures': Makes T41's refund netting exact for partial refunds |
| 2026-11-01 20:31 | queue_assign | T44 refund-records-tax | Queued in Report corrections |
| 2026-11-01 20:42 | annotate_task | T8 phase6-owner-dashboard-reporting | Added a note: Manager, from T29 background-job-queue (e7891f25): add the daily owner reminder as a schedule in the app's jobs.py, using `@jobs.job` plus `jobs.schedule(fn, daily_at="HH:MM")` as docs/jobs.md describes. Don't add a systemd timer. Send its email with `apps.checkout.emails.send_now` ins |
| 2026-11-01 20:42 | annotate_task | T10 phase8-email-list | Added a note: Manager, from T29 background-job-queue (e7891f25): queue email-list sends with `apps.jobs` (docs/jobs.md). Enqueue one job per recipient with a `key`, so each email retries on its own. Recurring work uses `jobs.schedule`, with no systemd units. Use a stand-in email backend in tests and |
| 2026-11-01 20:43 | queue_assign | T42 net-returns-from-reorder-use | Queued in Report corrections |
| 2026-11-01 20:43 | queue_assign | T8 phase6-owner-dashboard-reporting | Queued in Owner dashboard |
| 2026-11-01 20:43 | queue_assign | T10 phase8-email-list | Queued in Email list |
| 2026-11-01 21:02 | mark_ready | T51 ny-tax-table-calendar-quarters | Made Ready as a follow-up of 'Phase 6: owner dashboard and reporting': A bug T8's worker found in the tax report code it works with. A NY filing from that table would report the wrong figures. |
| 2026-11-01 21:06 | annotate_task | T11 phase9-support-agent | Added a note: Manager, from T8 phase6-owner-dashboard-reporting (836f1839, committing now): register an attention provider with kind="support" in apps/core/attention.py, using the kind/key/since fields, so the dashboard's reminder emails escalations at once. Queue the agent's emails and inbox pollin |
| 2026-11-01 21:07 | queue_assign | T51 ny-tax-table-calendar-quarters | Queued in Owner dashboard |
| 2026-11-01 21:07 | queue_assign | T11 phase9-support-agent | Queued in AI agents |
| 2026-11-01 21:09 | propose_tasks | T55 regression-sweep-shop-pages | Proposed as a Draft |
| 2026-11-01 21:09 | mark_ready | T55 regression-sweep-shop-pages | Made Ready as a follow-up of 'Phase 5: fulfillment dashboard': Regression sweep for the phases 5-8 stretch, per tests_at_task_end=new-only and the workers' tests_for_later |
| 2026-11-01 21:09 | propose_tasks | T56 regression-sweep-backend | Proposed as a Draft |
| 2026-11-01 21:09 | mark_ready | T56 regression-sweep-backend | Made Ready as a follow-up of 'Phase 5: fulfillment dashboard': Regression sweep for the phases 5-8 stretch, per tests_at_task_end=new-only and the workers' tests_for_later |
| 2026-11-01 21:31 | queue_assign | T55 regression-sweep-shop-pages | Queued in Research: Regression tests |
| 2026-11-01 21:31 | queue_assign | T56 regression-sweep-backend | Queued in Research: Regression tests |
| 2026-11-01 21:33 | annotate_task | T12 phase10-marketing-agent | Added a note: Manager, from T11 phase9-support-agent (4905724b, committed 1adcd07): build on apps/agents (docs/agents.md). It provides the AI client and stand-in, AGENTS_LIVE, the monthly cap, untrusted-input fences, output checks (health claims, refund or discount promises) and the audited tool loo |
| 2026-11-01 21:33 | annotate_task | T13 phase11-ops-security-agent | Added a note: Manager, from T11 phase9-support-agent (4905724b, committed 1adcd07): build on apps/agents (docs/agents.md) for the AI client and stand-in, the monthly cap, untrusted-input handling and the audited tool loop. The owner said (Q6) to keep the stand-in, so make no live AI calls. Server ch |
| 2026-11-01 21:38 | mark_ready | T60 compose-missing-phase6-env-vars | Made Ready as a follow-up of 'Regression tests for phases 5-8: backend apps': Bug from the T8 change that the regression run found, and it fails two deploy tests. Without the fix, your .env values for Wave, the attention deadlines and the estimated-tax rates never reach the containers. |
| 2026-11-01 21:38 | annotate_task | T60 compose-missing-phase6-env-vars | Added a note: Manager: also check that every variable that T10 (EMAIL_LIST\_\*) and T11 (AGENTS\_\*, SUPPORT\_\*) added to .env.example reaches the web and worker containers. Then run ComposeEnvironmentTests. Make no other changes. |
| 2026-11-01 21:38 | queue_assign | T60 compose-missing-phase6-env-vars | Queued in Foundation |
| 2026-11-01 21:39 | queue_assign | T12 phase10-marketing-agent | Queued in AI agents |
| 2026-11-01 21:39 | queue_assign | T13 phase11-ops-security-agent | Queued in Ops agent |
| 2026-11-01 22:01 | mark_ready | T61 fix-shellcheck-sc2164-deploy-scripts | Made Ready as a follow-up of 'Phase 11: ops and security agent': Found by T13's worker in the deploy scripts it works on. This warning fails CI's test job, and with it every deploy. |
| 2026-11-01 22:01 | mark_ready | T62 site-css-leaves-date | Made Ready as a follow-up of 'Phase 10: marketing agent and tea info section': Found by T12's worker on pages it built, where it currently works around the problem in marketing.css. The fix makes date, datetime-local and URL fields match the rest of the forms across the site. |
| 2026-11-01 22:03 | propose_tasks | T64 posts-attention-kind | Proposed as a Draft |
| 2026-11-01 22:03 | mark_ready | T64 posts-attention-kind | Made Ready as a follow-up of 'Phase 10: marketing agent and tea info section': T12's own limitation, plus the milestone screenshots T11 and T12 left undone (the owner wants milestones kept in doc/shots) |
| 2026-11-01 22:03 | propose_tasks | T65 milestone-shots-phase9-10 | Proposed as a Draft |
| 2026-11-01 22:03 | mark_ready | T65 milestone-shots-phase9-10 | Made Ready as a follow-up of 'Phase 10: marketing agent and tea info section': T12's own limitation, plus the milestone screenshots T11 and T12 left undone (the owner wants milestones kept in doc/shots) |
| 2026-11-01 22:03 | queue_assign | T61 fix-shellcheck-sc2164-deploy-scripts | Queued in Ops agent |
| 2026-11-01 22:03 | queue_assign | T62 site-css-leaves-date | Queued in Storefront |
| 2026-11-01 22:03 | queue_assign | T64 posts-attention-kind | Queued in AI agents |
| 2026-11-01 22:05 | queue_assign | T65 milestone-shots-phase9-10 | Queued in Storefront |
| 2026-11-01 22:05 | propose_tasks | T67 regression-sweep-phases-9-11 | Proposed as a Draft |
| 2026-11-01 22:05 | mark_ready | T67 regression-sweep-phases-9-11 | Made Ready as a follow-up of 'Phase 9: customer support agent': Regression sweep for the phases 9-11 stretch, per tests_at_task_end=new-only and the workers' tests_for_later |
| 2026-11-01 22:05 | queue_assign | T67 regression-sweep-phases-9-11 | Queued in Research: Regression tests |
| 2026-11-01 22:08 | mark_ready | T68 calendar-empty-day-style | Made Ready as a follow-up of 'Milestone screenshots for phases 9 and 10': A display bug that T65's screenshot review found on the marketing calendar that T12 built. |
| 2026-11-01 22:08 | annotate_task | T68 calendar-empty-day-style | Added a note: Manager: after the fix, replace only the two marketing-calendar desktop shots in doc/shots/2026-11-01-phase10-marketing/ (light and dark), with the same names. Don't re-take or recompress the other committed shots, because that only grows the git history. |
| 2026-11-01 22:09 | annotate_task | T70 agent-audit-attribution | Added a note: Manager decision: credit the agent only with actions it takes on purpose, meaning its tools' writes and the messages and drafts it sends. Lazy creation of settings singletons should be attributed to the system, for example by creating them before the agent context starts or by suspendi |
| 2026-11-01 22:09 | mark_ready | T70 agent-audit-attribution | Made Ready as a follow-up of 'Milestone screenshots for phases 9 and 10': The audit log credits the support agent from T11 with shop-settings changes it never made, which misleads anyone checking what the agents did. |
| 2026-11-01 22:09 | mark_ready | T69 health-claim-label-overlap | Made Ready as a follow-up of 'Milestone screenshots for phases 9 and 10': The health-claim check that T12's guardrails rely on gives a wrong label and repeats warnings for the same phrase. |
| 2026-11-01 22:13 | queue_assign | T70 agent-audit-attribution | Queued in AI agents |
| 2026-11-01 22:14 | queue_assign | T68 calendar-empty-day-style | Queued in AI agents |
| 2026-11-01 22:14 | queue_unassign | T68 calendar-empty-day-style | Taken out of AI agents |
| 2026-11-01 22:14 | queue_assign | T69 health-claim-label-overlap | Queued in Copy checks |
| 2026-11-01 22:14 | queue_assign | T68 calendar-empty-day-style | Queued in Storefront |
| 2026-11-01 22:18 | propose_tasks | T71 agent-guards-cover-queued-jobs | Proposed as a Draft |
| 2026-11-01 22:18 | mark_ready | T71 agent-guards-cover-queued-jobs | Made Ready as a follow-up of 'AI agents page: unrelated actions credited to support-age...': Closes a guardrail gap that T70's attribution change opened |
| 2026-11-01 22:18 | queue_assign | T71 agent-guards-cover-queued-jobs | Queued in AI agents |
| 2026-11-01 22:40 | annotate_task | T72 don-see-dashboard-set | Added a note: Manager: setup for teas, lots, packaging, boxes, scales and suppliers is only in the Django admin; the dashboard has no shortcuts to it. Do both: (1) add grouped dashboard shortcuts (attention.register_shortcut in each app's ready()) to the admin pages for catalog, receiving lots, stoc |
| 2026-11-01 22:40 | queue_assign | T72 don-see-dashboard-set | Queued in Dev data and setup links |
| 2026-11-01 22:45 | mark_ready | T73 shipped-tab-late-badge | Made Ready as a follow-up of 'I don't see where in the dashboard to set up inventory, s...': T72's worker found this bug with the new demo data. It wrongly flags orders that shipped on time as late, which could make you think you broke the FTC Mail Order Rule. |
| 2026-11-01 22:45 | queue_assign | T73 shipped-tab-late-badge | Queued in Fulfillment |
| 2026-11-01 22:46 | propose_tasks | T74 demo-package-dimensions | Proposed as a Draft |
| 2026-11-01 22:46 | mark_ready | T74 demo-package-dimensions | Made Ready as a follow-up of 'I don't see where in the dashboard to set up inventory, s...': Completes T72's sample data so the packing page's box suggestion works in the demo |
| 2026-11-01 22:47 | queue_assign | T74 demo-package-dimensions | Queued in Dev data and setup links |
| 2026-11-01 22:48 | annotate_task | T75 box-suggest-ignores-thick-package | Added a note: Manager: T74 is running at the same time and adds PackageDimensions to apps/storefront/demo_shop.py. Keep to apps/fulfillment/boxes.py and the fulfillment tests; don't edit demo_shop.py. Add a test with a long flat pouch plus a thicker tin that must not get the 1.5 in mailer. |
| 2026-11-01 22:49 | mark_ready | T75 box-suggest-ignores-thick-package | Made Ready as a follow-up of 'Sample package dimensions in load_demo_shop': Real bug in the packing page's box suggestion, found while T74 added package sizes; related to current work. |
| 2026-11-01 22:49 | queue_assign | T75 box-suggest-ignores-thick-package | Queued in Fulfillment |
| 2026-11-01 22:50 | tell_worker | T75 box-suggest-ignores-thick-package | Reopened it from Review: Manager: no other writer is active now. Please run the whole of apps/fulfillment/tests in one test_run, since the packing page and label purchase also use suggest(). Fix anything your change broke, then report again. |
| 2026-11-01 22:54 | annotate_task | T76 graphic-design-site-bit | Added a note: Manager: This is a mockup for the user to react to. Don't change the live templates or CSS yet. Build a standalone HTML page in doc/mockups/ (create it with create_tracked_file) that shows the storefront home page and a product page in the new style. Use hand-built inline SVG for the v |
| 2026-11-01 22:54 | queue_assign | T76 graphic-design-site-bit | Queued in Site design |
| 2026-11-01 23:08 | propose_tasks | T77 apply-vine-style-storefront | Proposed as a Draft |
| 2026-11-01 23:10 | annotate_task | T77 apply-vine-style-storefront | Added a note: Manager: The user chose Spring moss palette and Medium ornament density (review comment on T76). Keep everything else as in the mockup: Federant headings, Alegreya body, arched cards and pictures, the current vine weight. Drop the palette and density switches; they were for the mockup  |
| 2026-11-01 23:10 | mark_ready | T77 apply-vine-style-storefront | Made Ready as a follow-up of 'The graphic design of the site is a bit weak.  I was envi...': The user picked Spring moss / Medium in a review comment on T76. |
| 2026-11-01 23:10 | queue_assign | T77 apply-vine-style-storefront | Queued in Site design |
| 2026-11-01 23:29 | propose_tasks | T80 regression-sweep-vine-style | Proposed as a Draft |
| 2026-11-01 23:29 | mark_carried | T80 regression-sweep-vine-style | Being done by task T77 apply-vine-style-storefront (2ed211a5): Verifies T77 (committed 8941ec0), which changed the shared page frame used by every page; its worker ran only its new tests. |
| 2026-11-01 23:29 | propose_tasks | T81 regression-sweep-vine-style | Proposed as a Draft |
| 2026-11-01 23:29 | mark_ready | T81 regression-sweep-vine-style | Made Ready as a follow-up of 'Apply the chosen vine style to the live storefront': T77 changed the shared page frame, and its worker ran only its new tests. |
| 2026-11-01 23:29 | queue_assign | T81 regression-sweep-vine-style | Queued in Research: Regression tests |
| 2026-11-01 23:38 | mark_ready | T82 fix-shipped-tab-test-dst | Made Ready as a follow-up of 'Regression sweep after the vine style': Fragile test from T73 found by the regression sweep; small, clearly-right test fix. |
| 2026-11-01 23:38 | annotate_task | T82 fix-shipped-tab-test-dst | Added a note: Manager: Change only apps/fulfillment/tests/test_views.py, as suggested: build shipped_at from local calendar dates (noon local time) and use timezone.localdate() for ship_by. Also scan the other fulfillment tests for the same now - timedelta(days=N) pattern compared to local dates, an |
| 2026-11-01 23:38 | queue_assign | T82 fix-shipped-tab-test-dst | Queued in Fulfillment |
| 2026-11-01 23:40 | propose_tasks | T83 fulfillment-tests-localdate | Proposed as a Draft |
| 2026-11-01 23:40 | mark_ready | T83 fulfillment-tests-localdate | Made Ready as a follow-up of 'Shipped-tab lateness test fails when run in the hour afte...': Same time-zone fragility T82 fixed, in neighbouring tests; CI runs in UTC. |
| 2026-11-01 23:40 | queue_assign | T83 fulfillment-tests-localdate | Queued in Fulfillment |
| 2026-11-01 23:42 | tell_worker | T83 fulfillment-tests-localdate | Reopened it from Review: Manager: no other writer is active. Please run apps/support/tests and apps/marketing/tests/test_posting.py together in one test_run, fix anything your change broke, then report again. |

## Notable events

- 2026-11-01 18:41 **T5 phase3-storefront-design**: The Manager redirected the worker: From the Manager: a finding, T21 pillow-vulnerable-pin (5441d74e). The uncommitted requirements.txt pins `Pillow>=12,<13`, which resolves to pillow 12.3.0, and pip-audit reports three vulnerabilities in it (CVE-2026-96640, CVE-2026-96778, GHSA-78g4-xqwv-q3g8), a...
- 2026-11-01 18:42 **T9 phase7-purchasing-loss-tracking**: The Manager redirected the worker: From the Manager: T5 phase3-storefront-design (ea7f0526) is also editing apps/catalog/models.py right now, in the same working copy. Keep your changes there minimal and don't touch its fields. Watch for two catalog migrations with the same number (two leaf nodes...
- 2026-11-01 18:42 **T5 phase3-storefront-design**: The Manager redirected the worker: From the Manager: T9 phase7-purchasing-loss-tracking (ca29736e) is also editing apps/catalog/models.py right now, in the same working copy. Don't touch its fields. Watch for two catalog migrations with the same number (two leaf nodes). Before you finish, run `ma...
- 2026-11-01 18:52 **T5 phase3-storefront-design**: The Manager redirected the worker: From the Manager, a report from T9 phase7-purchasing-loss-tracking (ca29736e), which has finished: apps/core/urls.py no longer has the 'home' URL, but templates/base.html still links {% url 'core:home' %}. Every page using base.html (the owner dashboard, the inv...
- 2026-11-01 19:14 **T21 pillow-vulnerable-pin**: Ended obsolete
- 2026-11-01 19:20 **T26 shrink-milestone-screenshots**: The Manager redirected the worker: From the Manager: as you pointed out, committing recompressed copies of the existing screenshots adds about 27 MB to git history to save 12 MB in the checkout, which is a net loss. My task text asked for it, and that was a mistake. Please restore the existing PN...
- 2026-11-01 19:54 **T33 regression-tests-after-checkout**: Check found issues; filed T35 checkout-deploy-checks-break-settings and T34 compose-checkout-env-vars
- 2026-11-01 19:58 **T30 shared-rate-limit-cache**: The Manager redirected the worker: Manager: use Django's DatabaseCache (no Redis; nothing new to run on the VPS). Run `createcachetable` wherever migrate runs: the deploy/install scripts, the "Migrate dev database" entry point and the test setup. Add a test showing two separate cache clients shar...
- 2026-11-01 20:27 **T41 net-refunds-from-tax-reports**: The Manager redirected the worker: Manager: T29 (background jobs, apps/checkout/emails.py and timers) is running at the same time. Keep to the tax and nexus report code and its tests. Refund amounts reduce the period in which the refund was issued, as NY returns require; say so in the report's he...
- 2026-11-01 20:27 **T41 net-refunds-from-tax-reports**: The Manager redirected the worker: Manager: T29 (background jobs, apps/checkout/emails.py and timers) is running at the same time. Keep to the tax and nexus report code and its tests. Refund amounts reduce the period in which the refund was issued, as NY returns require; say so in the report's he...
- 2026-11-01 20:56 **T8 phase6-owner-dashboard-reporting**: The Manager redirected the worker: Manager: T10 phase8-email-list (9a988e61) has finished. It registers attention items that use your new kind/key/since fields on Attention (kinds "approvals" and "problems"), and it adds a dashboard shortcut "Email list and mailings". Keep those fields and kinds ...
- 2026-11-01 21:07 **T11 phase9-support-agent**: The Manager redirected the worker: Manager: T12 (marketing agent) and T13 (ops/security agent) come after you and will reuse what you build. Put the shared parts in one reusable app, for example apps/agents: the AI client interface with its stand-in, the monthly spending cap, the 'AI assistant' l...
- 2026-11-01 21:29 **T11 phase9-support-agent**: Question never answered: The support agent for the tea shop runs on an offline stand-in until it is given a Claude API key. My understanding is that a Claude Pro/Max subscription (the $100/month one used for Claude Code) covers a person using Claude, not a program answering customers around the c...
- 2026-11-01 21:37 **T56 regression-sweep-backend**: Check found issues; filed T60 compose-missing-phase6-env-vars
- 2026-11-01 21:58 **T12 phase10-marketing-agent**: The Manager redirected the worker: Manager: every variable you add to .env.example must also go in compose.yaml's app-environment block, because ComposeEnvironmentTests in apps/core/tests/test_deploy_scripts.py checks for it (T60 fixed misses like this). T13 is editing .env.example, settings and ...
- 2026-11-01 21:58 **T13 phase11-ops-security-agent**: The Manager redirected the worker: Manager: every variable you add to .env.example must also go in compose.yaml's app-environment block, because ComposeEnvironmentTests in apps/core/tests/test_deploy_scripts.py checks for it (T60 fixed misses like this). T12 is editing .env.example, settings and ...
- 2026-11-01 22:45 **T73 shipped-tab-late-badge**: The Manager redirected the worker: Manager: T72 is running at the same time. It adds dashboard shortcuts in each app's apps.py and a demo-data command. Keep to apps/fulfillment/views.py, its template and the fulfillment tests, and don't touch apps/fulfillment/apps.py.
- 2026-11-01 22:50 **T75 box-suggest-ignores-thick-package**: The Manager redirected the worker: Manager: no other writer is active now. Please run the whole of apps/fulfillment/tests in one test_run, since the packing page and label purchase also use suggest(). Fix anything your change broke, then report again.
- 2026-11-01 23:29 **T80 regression-sweep-vine-style**: Ended obsolete
- 2026-11-01 23:38 **T81 regression-sweep-vine-style**: Check found issues; filed T82 fix-shipped-tab-test-dst
- 2026-11-01 23:42 **T83 fulfillment-tests-localdate**: The Manager redirected the worker: Manager: no other writer is active. Please run apps/support/tests and apps/marketing/tests/test_posting.py together in one test_run, fix anything your change broke, then report again.

## Tasks not run

- T14 provision-server (pending): Approve and create the hosting accounts, then provision the server
- T16 practise-disaster-recovery (pending): Practise disaster recovery before launch
- T18 compare-milestone-screenshots (pending): Compare screenshots with the last milestone
- T22 phone-stock-count-page (pending): Phone-friendly stock count page
- T23 packaging-cost-per-package (pending): Packaging cost per package
- T27 design-agent-page-variants (pending): Design agent that proposes page variants
- T28 owner-logo-and-name (pending): Owner's logo and shop name
- T32 checkout-test-mode-run (pending): Run checkout against Stripe and EasyPost test mode
- T36 organic-wording-on-labels (pending): Organic wording on package labels
- T37 organic-chip-and-filter (pending): Organic chip on product cards and an organic filter
- T38 organic-over-exemption-limit (pending): Stop showing organic once over the exemption limit
- T39 atomic-rate-limit-increment (pending): Atomic rate-limit increment
- T40 renewal-failed-second-notice (pending): Email again when a retried renewal still fails
- T43 packing-slip (pending): Packing slip in the box
- T45 email-attempt-audit (pending): Per-attempt email failure in the audit log
- T46 job-worker-status-card (pending): Job worker status on the Operations card
- T47 checkout-email-opt-in (pending): Opt-in checkbox at checkout
- T48 ses-bounce-webhook (pending): Read SES bounces and complaints back automatically
- T49 privacy-policy-email-service (pending): Name the email service in the privacy policy
- T50 scheduled-mailing (pending): Schedule an approved mailing for a set time
- T52 report-csv-export (pending): CSV export of the reports
- T53 reports-same-date-basis (pending): Line up report costs and sales by the same date
- T54 wave-connection-trial (pending): Wave connection trial
- T57 support-spot-check (pending): Spot-check answers given alone
- T58 support-owner-faq (pending): Owner's FAQ and policy notes for the agent
- T59 support-agent-live-test (pending): Try the live support agent on real questions
- T63 ops-disk-trend-chart (pending): Ops page: show disk and update trends from the hourly readings
- T66 threads-and-token-refresh (pending): Threads and Pinterest token refresh
- T78 more-creatures-region-art (pending): Draw a few more creatures and per-region art
- T79 trim-milestone-screenshot-size (pending): Trim milestone screenshot size

## Other commits in the run's window

- [`30853735de93`](https://github.com/wingware-dev/teashop/commit/30853735de93a27006d28dacb621ee4bd5f8ccba) Initial prompt updates
- [`2cd941955edd`](https://github.com/wingware-dev/teashop/commit/2cd941955eddc5ffa5a027245e2932e77b4b0ecd) Main entry point for server

