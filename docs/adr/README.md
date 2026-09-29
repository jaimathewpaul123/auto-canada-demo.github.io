# Architecture decision records

One file per decision that crosses more than one file, had a real alternative, or
would be costly to reverse. Files are numbered `NNNN-kebab-title.md` and never
renumbered. Each has Context, Assumptions, Decision, Consequences and Alternatives
considered. Assumptions is mandatory: it lists what must stay true for the decision
to hold, so a later reader can tell when to revisit it. To reverse a decision, add a
new ADR that supersedes the old one rather than editing it. List every ADR in
[../DECISIONS.md](../DECISIONS.md).
