# Suggestions for the framework (not part of the homework module)

These files were drafted while designing the homework module, then taken out
of it (D-044): they are templates for **formats**, and formats belong to the
framework, not to homework. They are kept here only so the work isn't lost.

| File | Format | Note |
|---|---|---|
| `templates/assessment/item-numeric.md` | `numeric` | Uses `tolerance` / `measurement_units`, which the homework module adds as optional fields |
| `templates/assessment/item-multiple-select.md` | `multiple-select` | |
| `templates/assessment/item-true-false.md` | `true-false` | |

Today `classkit scaffold item --format` accepts only `multiple-choice` and
`open`, so the framework has no templates for these formats yet. If Chen wants
them, they can move to `templates/assessment/` as a framework change. Before
that, each should default to `usage: [in-class-quiz]`, like the framework's
multiple-choice template.
