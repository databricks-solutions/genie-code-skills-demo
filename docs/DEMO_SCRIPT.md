# Genie Code Skills Demo Script

A four-stage demo that progressively adds skills, instructions, and MCP to show how Genie Code output improves at each step.

**Catalog:** `genie_code_skills_demo`
**Schema:** `demo_data`
**Raw data:** `/Volumes/genie_code_skills_demo/demo_data/raw_data/`

---

## Prerequisites

Before running the demo:

1. Sample data has been generated (run the data gen notebook or DAB job)
2. You have access to the `genie_code_skills_demo` catalog on the workspace
3. An SDP pipeline exists (or create one in the UI) to run the generated SQL against

---

## Stage 1: Baseline (No Skills, No Instructions, No MCP)

**Goal:** Show that Genie Code produces functional but ungoverned pipeline code out of the box.

### Setup

- No skills uploaded to the workspace
- No `.assistant_instructions.md` file
- No MCP connections enabled in Genie Code

### Prompts

Open Genie Code in Agent mode inside a pipeline and run these prompts:

**Prompt 1a:**

> Build me a bronze table from `/Volumes/genie_code_skills_demo/demo_data/raw_data/customers/` as source

**Prompt 1b:**

> Build me a bronze table from `/Volumes/genie_code_skills_demo/demo_data/raw_data/date_dimensions/` as source

**Prompt 1c:**

> Now build a silver table using the bronze customer table

### What to observe

Point out what's **missing** from the generated code:

- [ ] No `bronze_` / `silver_` layer prefix in table names
- [ ] No `COMMENT` clause on the table
- [ ] No `TBLPROPERTIES` (`quality`, `owner`, `domain`)
- [ ] No `audit_timestamp` or `source_system` columns
- [ ] No column descriptions or PII annotations
- [ ] No data quality `CONSTRAINT` clauses on silver
- [ ] Inconsistent naming (may use PascalCase or camelCase)

> **Talking point:** "Genie Code generates working SQL, but without governance guardrails the output won't pass a code review. Let's fix that."

---

## Stage 2: Add Skills

**Goal:** Show that uploading skills to the workspace immediately improves code quality.

### Setup

Upload the three skill files from `skills/data_eng/` to your workspace. Each skill needs its own folder with a `SKILL.md` file:

```
Workspace/.assistant/skills/
  table-governance/
    SKILL.md          ← content from skills/data_eng/table-governance.md
  sdp-basics/
    SKILL.md          ← content from skills/data_eng/sdp-basics.md
  pii-management/
    SKILL.md          ← content from skills/data_eng/pii-management.md
```

Or upload to user level at `/Users/{username}/.assistant/skills/` for a personal demo.

### Prompts

Start a **new** Genie Code session (to clear context from Stage 1):

**Prompt 2a:**

> Build me a bronze table from `/Volumes/genie_code_skills_demo/demo_data/raw_data/customers/` as source — use @sdp-basics and @table-governance as standards

**Prompt 2b:**

> Now build a silver table from the bronze customer table — apply @sdp-basics, @table-governance and @pii-management

### What to observe

Compare side-by-side with Stage 1 output:

- [x] Table name uses `bronze_customers` / `silver_customers` convention
- [x] `COMMENT` clause present with layer-appropriate description
- [x] `TBLPROPERTIES` with `quality`, `owner`, `domain`
- [x] `audit_timestamp` and `source_system` as last columns
- [x] PII columns annotated with `-- [PII: EMAIL - HIGH]` style comments
- [x] `contains_pii` and `pii_columns` in TBLPROPERTIES for customer table
- [x] Data quality `CONSTRAINT` clauses on silver table
- [x] Consistent `lowercase_snake_case` naming

> **Talking point:** "Same prompt, dramatically different output. The skills encode our standards once and Genie Code applies them every time."

---

## Stage 3: Add Instructions

**Goal:** Show that custom instructions make skills automatic — no need to `@mention` them in every prompt.

### Setup

Keep the skills from Stage 2 in place. Add a user-level instructions file:

1. Copy `local_deployment/instructions_to_use/user_instructions_skills.md`
2. Upload as `/Users/{username}/.assistant_instructions.md` in your workspace

### Prompts

Start a **new** Genie Code session:

**Prompt 3a:**

> Build me a bronze table from `/Volumes/genie_code_skills_demo/demo_data/raw_data/accounts/` as source

**Prompt 3b:**

> Build a silver table from the bronze accounts table

### What to observe

- [x] **No `@skill` mentions needed** — instructions tell Genie Code to apply skills automatically
- [x] All the same governance standards applied as Stage 2
- [x] Instructions act as a routing layer: "for any pipeline table, apply these skills"

> **Talking point:** "With instructions in place, every developer gets governed code by default. No one has to remember which skills to invoke."

---

## Stage 4: MCP (Centralized Standards from GitHub)

**Goal:** Show that skills can be served from a central GitHub repo via MCP — no local skill files needed in the workspace. The governance team maintains standards in version control and every workspace picks them up automatically.

### Setup

1. **Delete the local skills** from the workspace:
   - Remove `Workspace/.assistant/skills/table-governance/`
   - Remove `Workspace/.assistant/skills/sdp-basics/`
   - Remove `Workspace/.assistant/skills/pii-management/`
   - (Or remove from `/Users/{username}/.assistant/skills/` if uploaded there)

2. **Add the MCP connection** to Genie Code:
   - Open Genie Code settings
   - Add MCP server → select `genie-code-skills-mcp` connection
   - Enable these tools:
     - `get_file_contents`
     - `search_code`

3. **Switch instructions to MCP**:
   - Replace your `.assistant_instructions.md` with the content from `local_deployment/instructions_to_use/user_instructions_mcp.md`
   - Upload as `/Users/{username}/.assistant_instructions.md`

### Prompts

Start a **new** Genie Code session:

**Prompt 4a:**

> Build me a bronze table from `/Volumes/genie_code_skills_demo/demo_data/raw_data/products/` as source

**Prompt 4b:**

> Build a silver table from the bronze products table

**Prompt 4c (bonus):**

> Build a gold summary table that joins silver customers, silver accounts, and silver products to show total account balances by product type and customer region

### What to observe

- [x] Genie Code **fetches skills from GitHub** via MCP (you'll see it call `get_file_contents`)
- [x] Same governance standards applied — identical quality to Stages 2 and 3
- [x] **No local skill files needed** in the workspace
- [x] Standards are version-controlled in GitHub — update the repo, all workspaces get the changes

> **Talking point:** "The governance team maintains standards in a single GitHub repo. Every workspace, every developer, every pipeline gets the same rules — automatically, via MCP. No manual file copying, no drift between teams."

---

## Summary Slide

| Stage | Skills | Instructions | MCP | Result |
|-------|--------|-------------|-----|--------|
| 1. Baseline | -- | -- | -- | Functional but ungoverned code |
| 2. Skills | Workspace | -- | -- | Governed code (manual `@skill` invocation) |
| 3. Skills + Instructions | Workspace | User-level | -- | Governed code (automatic, no `@` needed) |
| 4. MCP | GitHub | User-level (MCP) | GitHub MCP | Governed code (centralized, version-controlled) |

---

## Tips

- **Side-by-side comparison:** Keep Stage 1 output visible while running later stages to highlight the difference
- **Pipeline UI:** Run the generated SQL in an actual SDP pipeline to show it works end-to-end
- **Live editing:** If time allows, edit a skill in GitHub and show that the next Genie Code session picks up the change via MCP
- **Workspace vs user skills:** For a team demo, upload skills at workspace level so everyone sees them; for a personal demo, user level is fine
