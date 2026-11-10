# Bias checks

Adopted for Saxscribe by Austin on 2026-11-10 ([ADR-0040](../decisions/0040-adopt-bias-checks.md)). Applies alongside the [development standards](../development-standards.md).

In this project: decision records follow check 7 (the [template](../decisions/_template.md) has "Options considered" and "Case against"). Check 9 uses the default of three experiments in a row; the experiment log is [evaluation/log.md](../evaluation/log.md).

Every builder has habits, and so does every owner. These standards make both
visible so choices are made on purpose. They apply to whoever does the work:
Claude, another tool or a person. Like the build standards, each one says what
to do, why, and how. The why is the test: if a check would defeat its purpose
on a given project, say so and move on.

Keep checks light. A check is a sentence or two, not a report. Scale it to the
choice. A choice is "big" when undoing it would take more than a day's work or
touch real data: a new project, stack, database, data model, dependency the
code leans on, rewrite or model experiment. Small choices need no check; big
ones get all of them.

## Checks on the builder's own habits

### 1. Name the options before picking a stack

- **Why:** AI tools default to what is most common in their training
  (TypeScript, React, Next.js, Python, Postgres, Tailwind) or to whatever the
  project already uses. Often right, not always.
- **How:** For a new project, language, framework, database or major library,
  list two or three real options, including a simpler one (plain HTML, a
  script, SQLite, no new dependency). Recommend one and say whether the reason
  is fit or habit. Matching the owner's other projects is a valid reason; say
  that it is the reason.
- **Applies to:** Every project with code

### 2. Build the simplest thing that works

- **Why:** Builders over-engineer: extra layers, options, error handling,
  files and dependencies nobody asked for. Each one is more to understand and
  maintain.
- **How:** Build what was asked. Before adding a dependency, abstraction,
  setting or file, name the problem it solves today. List what you left out so
  the owner can ask for it.
- **Applies to:** Every project with code

### 3. Design from the people who use it, not from a template

- **Why:** First drafts look alike: centred cards, soft shadows, indigo or
  slate colours, emoji icons. Safe, tidy and generic.
- **How:** Before designing a screen, name who uses it, on what device, and
  the first thing they do there. Ask for references or propose some. When the
  look matters, show two or three directions and let the owner pick.
- **Applies to:** Projects with a screen

### 4. Prove it, don't claim it

- **Why:** "Done", "fixed" and "tests pass" get said more readily than they
  are true.
- **How:** Back each claim with evidence: test output, a screenshot, a run, a
  score before and after, a link. Say plainly what was not checked.
- **Applies to:** Every project with code

### 5. Check facts that move

- **Why:** What a tool remembers about versions, APIs, prices and best
  practice goes out of date, and it sounds just as sure when it is wrong.
- **How:** For anything version- or date-sensitive, read the installed docs
  or the official source before relying on memory, and name the source. Say
  when you are unsure instead of guessing.
- **Applies to:** Every project

## Checks on the owner's thinking

### 6. Question the ask before building it

- **Why:** Builders lean toward building and toward agreeing with how the
  owner framed the problem.
- **How:** Before non-trivial work, read what the project has already tested
  and decided (decision records, experiment logs). Then say in a sentence
  whether the ask is already answered there, whether there is a reason not to
  build it, a simpler way, or something that already exists. Then follow the
  owner's call.
- **Applies to:** Every project, including ideas

### 7. Argue against the plan before it's hard to undo

- **Why:** Agreement is cheap, and a plan is easiest to change before work
  starts.
- **How:** For big choices, give the strongest case against the plan and what
  would make it fail, whoever proposed it. Make it specific enough to be
  proven wrong: "this breaks when X" beats "there may be risks". Every decision
  record has an "Options considered" and a "Case against" section.
- **Applies to:** Every project, including ideas

### 8. Name blind spots and untested assumptions

- **Why:** The owner wants to be made better, not agreed with. Patterns are
  easy to miss from inside: an assumption never tested, a risk never raised, a
  goal drifting, a preference treated as a requirement, effort kept going
  because of what's already spent.
- **How:** When you see one, say it once, plainly, with the evidence, and
  suggest the cheapest way to test it (a measurement, a prototype, a look at
  the data). Don't repeat it after the owner has decided.
- **Applies to:** Every project, including ideas

### 9. Stop when experiments stop paying

- **Why:** Each experiment that ties or loses feels like it's one tweak away
  from winning. Without a rule, compute and time keep going in.
- **How:** After three experiments in a row that don't beat the current best,
  pause. Before spending more, measure the ceiling (how good the result can
  get) or say what makes the next attempt different. A project may set its own
  number in its CLAUDE.md, with the reason.
- **Applies to:** Projects that run experiments

## Checks on the checker

### 10. Check yourself, then get outside eyes

- **Why:** The reviewer has biases too: toward its usual defaults, toward
  earlier sessions' conclusions, and toward what the owner seems to want. When
  one tool writes the standards, the code and the reviews, its habits become
  the house style without anyone choosing them.
- **How:** Before recommending, ask what you would say if the owner had
  proposed the opposite, and say when a pick matches your usual default. Treat
  earlier analysis, including your own, as one input. For big choices, also
  get a review from a fresh session, a different tool, a person or an outside
  source, and name who reviewed it.
- **Applies to:** Every project, including ideas

### 11. Look back at past calls

- **Why:** Checks only improve if someone sees whether they were right.
- **How:** When a decision record is a few months old, or a choice gets
  reversed, note in one line whether the case against it came true. Patterns
  across projects go to the standards project.
- **Applies to:** Every project, including ideas

## How to answer a big choice

Use the same shape every time, so it can be checked at a glance:

- **Facts:** what the repo, data or official source says, with where.
- **Recommendation:** what you'd do and why, plus the strongest case against it.
- **Not checked:** what you didn't look at or couldn't verify.

Only the owner decides.

## Asking for a check

Any of these phrases asks for a check on demand:

- "Give me options first."
- "Simplest version, no new dependencies."
- "Argue against this."
- "What am I not seeing?"
- "Show me it works."
- "Get a fresh opinion on this."
