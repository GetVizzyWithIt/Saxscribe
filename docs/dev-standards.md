# Development standards

These are the standards every project is held to. They describe outcomes, not a
required language, framework or tool. Choose the stack that fits the project at
hand, and judge each standard by its purpose.

The aim behind all of them: any project can be understood, run, changed and
maintained by someone new, whether that is a person or a fresh Claude session,
without guessing.

## How to use these

- Each standard says what to do, why it matters, and how to meet it. The why is
  the test. If following the letter of a standard would defeat its purpose for
  this project, say so, explain the trade-off, and record the decision.
- Prefer what is simple and widely understood over what is clever.
- When a choice is specific to this project, name the options, recommend one
  with reasons, and let the owner decide.
- This file is kept in sync from Dev Buddy. To change a standard, change it
  there; edits made to this copy are replaced by the next sync.

## The standards

### 1. README opens with copy-paste commands

- **Why:** Anyone, including a new Claude session, can open, update and test the project without guessing.
- **How:** Put the commands to install, run and test the project first, one per line with no inline # comments. Explain anything unusual in plain words after the block.
- **Applies to:** Every project with code

### 2. One-step setup script that ends with a health check

- **Why:** Setting up a new machine is one command, and you know it worked.
- **How:** Use whatever fits the stack: a shell script, a make target or a package script. If something is missing it should stop and say what, not fail halfway.
- **Applies to:** Every project with code

### 3. Runtime version pinned

- **Why:** Every machine and CI run the same version, so 'works on mine' bugs don't happen.
- **How:** Pin the language version in the file your ecosystem reads (.nvmrc, engines, .python-version or similar). Pick a version that is still supported.
- **Applies to:** Every project with code

### 4. Lockfile committed

- **Why:** Installs are repeatable; a dependency can't change under you.
- **How:** Commit the lockfile your package manager writes. If the ecosystem has none, pin exact versions.
- **Applies to:** Every project with code

### 5. CLAUDE.md with working rules and current state

- **Why:** Every Claude session starts from the same rules and knows where the project stands.
- **How:** Cover what the project is, where things live, how to run and test it, the rules for working in it, and where it stands now. Rewrite it when it drifts from reality.
- **Applies to:** Every project with code

### 6. Tests on core logic

- **Why:** Changes can be checked automatically instead of by hand.
- **How:** Test the logic that would hurt most if it broke quietly. Whether the tests catch real mistakes matters more than a coverage number.
- **Applies to:** Every project with code

### 7. CI runs tests on every PR

- **Why:** Nothing merges without the tests passing, even when you're reviewing on your phone.
- **How:** Run the same checks a person runs locally, such as lint, types, tests and build. Keep it fast enough that nobody is tempted to skip it.
- **Applies to:** Every project with code

### 8. One PR per change, nothing straight to main

- **Why:** Every change gets a review and a record of why it was made.
- **How:** Keep each PR to one change a reviewer can follow in one sitting, and say what changed and why in its description.
- **Applies to:** Every project with code

### 9. Branch names follow claude/<type>-<what>

- **Why:** You can tell what a branch does without opening it.
- **How:** Types are add, fix, change, remove, rename, docs and chore, followed by at most five lowercase words joined by hyphens.
- **Applies to:** Every project with code

### 10. Decision log in docs/decisions/

- **Why:** Why something was built a certain way survives after the conversation ends.
- **How:** Write one short file whenever you choose between real options: what was chosen, what was ruled out, and why.
- **Applies to:** Every project with code

### 11. Project glossary or data dictionary

- **Why:** Names mean one thing everywhere: in code, docs and conversations with Claude.
- **How:** Define the words that mean something specific here and, for data, what each field holds. Use the same names in code, screens and docs.
- **Applies to:** Every project with code

### 12. Secrets and machine files out of git

- **Why:** Keys and personal settings never leak through the repo.
- **How:** Keep keys in local env files or the host's settings. Commit an example file with blank values so others know what is needed.
- **Applies to:** Every project with code

### 13. Current copy of the standards in the repo

- **Why:** Every project, and every Claude session in it, works from the same up-to-date rules.
- **How:** Keep docs/dev-standards.md exactly as Dev Buddy publishes it and point to it from CLAUDE.md. Merge the sync PR when it arrives; change a standard in Dev Buddy, never in the copy.
- **Applies to:** Every project with code

### 14. Private repo, or public by decision

- **Why:** Nothing is public by accident.
- **How:** Start private. Make a repo public only on purpose, and write down why.
- **Applies to:** Every project, including ideas

### 15. Security alerts on, none serious left open

- **Why:** You hear about a vulnerable package or a leaked key the day GitHub finds it.
- **How:** Turn on dependency alerts and secret scanning. Fix critical and high alerts promptly; judge lower ones by whether the affected code is actually used.
- **Applies to:** Every project with code

### 16. Schema changes through migrations

- **Why:** Database changes are repeatable and reviewable, and real data is safe.
- **How:** Use the database tool's migration system so every schema change is a reviewed file. Never change a live schema by hand.
- **Applies to:** Web app

### 17. Deploys from main automatically

- **Why:** What's live is exactly what's merged.
- **How:** Connect the host to the main branch so that merging is deploying. Use preview deploys for PRs if the host offers them.
- **Applies to:** Web app

### 18. Framework versions still get security fixes

- **Why:** Stay on a supported version, and upgrade on purpose in its own PR.
- **How:** Stay on versions that still get security fixes. Make major upgrades on purpose, in their own PR, after reading the upgrade guide.
- **Applies to:** Web app
