# Layer 14 — AI-Assisted Coding & Process

Use this file when generating code with an AI agent, adding LLM features, writing tests, or setting team process. Git mechanics and CI gates live in [07-cicd-version-control.md](07-cicd-version-control.md); this layer is how you keep AI-assisted work honest.

## Reviewing AI-Generated Code and Hallucinated APIs/packages

**Why it matters:** Models invent confident code. Hallucinated APIs/packages (an OCR of this topic once read "Hallucinated Reading Traces") include import names that do not exist, methods that never shipped, and flags copied from another language. Installing a typo-package can be a Supply Chain Attack (layer 8).

**Checklist for the agent**

- Reviewing AI-Generated Code is mandatory before merge: authz, validation, error paths, tests, migrations, and secrets. Read the diff; do not approve on the model's summary alone.
- Verify every new import against the official registry and docs (`npm view`, PyPI, Go module proxy). If the package was not already in the lockfile, treat it as untrusted.
- Confirm APIs against current documentation or types — not the model's memory. Run the compiler and tests.
- Watch for copy-pasted secrets, disabled TLS, swallowed exceptions, and `// TODO: add auth`.
- Prefer small, reviewable diffs. If a generation is large, split or regenerate with a narrower task.

**Common vibe-coding mistakes:** `npm i` a name that "looks official"; assuming a method exists because the model used it; skipping review because "tests passed" when the tests were also generated and empty.

**Quick verification:** every added dependency exists and is the intended project; `npm ci` / lockfile is consistent; a human (or this skill's layer checklists) has gone through the diff.

## RAG, Streaming LLM Responses, and Evaluating LLM Output (evals)

**Why it matters:** If you ship LLM features, "it sounded good in the demo" is not quality control. RAG, streaming, and evals are how you make the feature inspectable.

**Checklist for the agent**

- **RAG:** retrieve from a corpus you actually control, cite sources, and bound the context. Do not let the model invent citations. Separate "I found this" from "I guessed this." Watch prompt injection in retrieved documents (treat docs as untrusted).
- **Streaming LLM Responses:** stream tokens to the UI with a cancel path, backpressure, and timeouts. Do not block a web worker forever. Sanitize streamed HTML. Authenticate and rate-limit these endpoints (they are expensive).
- **Evaluating LLM Output (evals):** keep a set of prompts and expected properties (contains citation, no PII leak, refuses a jailbreak, structured JSON parses). Run them in CI or a scheduled job when you change the prompt, model, or retriever. Log traces for failures.
- Budget tokens and set max output length. Do not send secrets or raw PII to a third-party model unless the contract and policy allow it.

**Common vibe-coding mistakes:** RAG that always "answers" even when retrieval is empty; streaming into `innerHTML`; no evals; a system prompt that claims "never hallucinate" as the only control.

**Quick verification:** a question whose answer is not in the corpus is refused or marked unknown; cancel stops the stream; a small eval suite fails if you break citations.

## Writing Good Bug Reports

**Why it matters:** A bug report that says "it doesn't work" wastes hours. Writing Good Bug Reports is also how you hand work to another person or to an agent without a long chat.

**Checklist for the agent**

- Include: expected vs actual, steps to reproduce, environment (browser, OS, app version, tenant), timestamps, and a Correlation ID or screenshot/log excerpt with PII stripped.
- Severity and how many users. Note whether it is a regression (used to work in version X).
- One issue per report. If you already have a hypothesis, label it as a hypothesis.

**Common vibe-coding mistakes:** a screenshot of a whole desktop with cookies visible; no version; mixing five bugs.

**Quick verification:** a stranger can follow the steps and see the same failure.

## Code Comments & Refactoring and Premature Abstraction

**Why it matters:** Code Comments & Refactoring should make the next change safer. Premature Abstraction (a "flexible" plugin core for two call sites) does the opposite.

**Checklist for the agent**

- Comment *why*, not a restatement of the code. Document invariants, workarounds, and links to tickets or ADRs.
- Refactor with tests in place, in a separate commit or PR from the feature when the diff would hide the behavior change.
- Add an abstraction when you have a third real use or a painful duplication that is already well-tested — not "we might need other providers someday."
- Delete dead code. Do not leave a parallel "clean" architecture next to the working messy one.

**Common vibe-coding mistakes:** a 12-layer folder tree for three endpoints; comments that repeat the function name; a refactor in the same PR as a payment change with no tests.

**Quick verification:** the PR description says what behavior is unchanged; tests cover the refactored path; no unused generic interface with a single implementor unless it is an explicit boundary (e.g. a vendor SDK).

## Agent instructions files / READMEs and Architecture Decision Records

**Why it matters:** Agent instructions files / READMEs (including `AGENTS.md`; an OCR of this topic once read "AGNI READMEs") tell humans and models how to work the repo. Architecture Decision Records (ADRs) capture *why* a decision was made so it is not relitigated or silently reversed.

**Checklist for the agent**

- Keep a README that can boot the app: prerequisites, Command Line Basics, env vars, tests, and lint. Link to deeper docs.
- Add `AGENTS.md` (or the host's equivalent) with: stack, commands, conventions, "never do" (do not hit prod, do not commit secrets), and where secrets live. Keep it short enough to actually be read.
- Write an ADR when you pick a database, an auth approach, a queue, or a "we will not do X." One or two pages: context, decision, consequences. Store `docs/adr/0001-….md`.
- Update these files when the decision changes. Stale agent instructions are worse than none.

**Common vibe-coding mistakes:** a README that only says "TODO"; 4,000 words of agent rules nobody updates; architecture that lives only in a chat thread.

**Quick verification:** a clean machine (or a new agent session) can follow the README to run tests; at least one ADR exists for a hard-to-reverse choice.

## Automated Testing, Unit vs Integration vs E2E Tests, TDD, Smoke Tests, and Regression Testing

**Why it matters:** Automated Testing is how you change the app next month without fear. The types answer different questions.

**Checklist for the agent**

- **Unit vs Integration vs E2E Tests:** unit tests are fast and precise for pure logic; integration tests hit the database or HTTP API (still usually in-process or docker-compose); E2E drives a browser or real client for a few critical journeys. Do not make every test an E2E test.
- **TDD:** for tricky logic (billing, permissions, parsers), write the failing test first. Even if you do not practice TDD everywhere, no production path should land untested because "the model wrote it carefully."
- **Smoke Tests:** a short post-deploy list (health, login, a read, a write) that you run against staging/prod. This is also a good pre-launch gate script.
- **Regression Testing:** every fixed bug should add a test that would have failed before the fix. Keep a list of critical flows that must stay green.

**Common vibe-coding mistakes:** 90% coverage of getters and 0% of authz; E2E for every unit; tests that always `expect(true)`; no test for the bug you just fixed.

**Quick verification:** `npm test` / `pytest` / equivalent in CI; a smoke script against staging; a regression test exists for a recent bug.

## Load Testing

**Why it matters:** Load Testing is how you learn the first bottleneck before your users do. It is not a single huge request from your laptop.

**Checklist for the agent**

- Model realistic scenarios (login, list, write) with a ramp. Watch p95 latency, errors, and saturation (CPU, pool, locks) — see layers 11–12.
- Include permissioned endpoints and heavy ones (search, exports, AI). Watch the database, not only the web tier.
- Run against a production-like environment, not the local SQLite file, and clean up the data you create.
- Combine with Rate Limiting so a test or a customer cannot unexpectedly become a self-DDoS.

**Common vibe-coding mistakes:** "it worked for me with 5 tabs"; load testing production by surprise; ignoring lock waits because RPS looked fine.

**Quick verification:** a recorded test (k6, Locust, vegeta, etc.) and a short report of the first bottleneck.

## Code Coverage, Mocking, Test Fixtures, and Flaky Tests

**Why it matters:** These are the hygiene of a suite you can trust. A green build that is flaky or mocked into fiction is worse than a smaller honest suite.

**Checklist for the agent**

- **Code Coverage:** use it to find *untested critical paths*, not to chase 100%. Do not write tests that only bump the number. Enforce a floor if it helps, but review exclusions.
- **Mocking:** mock at the edges (HTTP, clock, email, payments). Do not mock the system under test until the test asserts nothing real. Prefer a test database for data logic.
- **Test Fixtures:** build factories or builders, not a 2,000-line shared `setup.sql` that every test mutates unpredictably. Isolate data (transactions, unique IDs).
- **Flaky Tests:** quarantine or fix immediately (time, order, leftover data, real network, animation). A retry in CI is a temporary bandage with a ticket, not a strategy.

**Common vibe-coding mistakes:** 100% coverage of a file that never hits the database; mocking the ORM so a wrong query still passes; `sleep(2000)` to "wait for the UI"; ignoring a test that fails every fifth run.

**Quick verification:** rerun the suite twice locally and in CI; look at coverage of `authz` and payment modules; grep tests for `sleep` and blanket `mock`.

## Technical Debt, Reading Documentation, and Command Line Basics

**Why it matters:** Technical Debt is a list of deferred work with a cost, not an insult. Reading Documentation and Command Line Basics are how you stop guessing.

**Checklist for the agent**

- Track debt (ticket, ADR, or `# tech-debt` with context): what is painful, why it was deferred, and what "good" would be. Pay it down when you are in the area or when it starts eating the error budget.
- **Reading Documentation:** official docs first (framework, cloud, OWASP, Postgres). Confirm versions. Do not rely only on a model summary of an API that changes monthly.
- **Command Line Basics:** the README should show how to install, run, test, lint, and migrate. Agents and humans should use the same commands. Know `git`, the package manager, and how to set env vars without pasting secrets into the shell history if you can avoid it.

**Common vibe-coding mistakes:** "we'll refactor later" with no ticket; implementing from a blog for the wrong major version; undocumented make targets that only work on one laptop.

**Quick verification:** a new contributor (or a fresh agent) can follow the README to run tests without a chat thread; there is a visible debt list, even if short.
