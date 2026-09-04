# Contributing

## Golden rule

If a change requires a new field, endpoint, or response shape, update
`docs/dashboard.md` and `kuartal/api/schemas.py` first, in the same PR,
before implementing code that depends on it. Mock data, the API, and the
dashboard must remain consistent with the contract.

## Changelog

Every change must be documented in `CHANGELOG.md`. Add an entry under
`[Unreleased]` for every feature, fix, change, test, or documentation update.

## Branching

- `master` - always buildable.
- `feat/<short-name>` - one feature or fix per branch.

## Commit style

`<type>(<scope>): <what changed>` - e.g. `feat(storage): add watchlist
persistence`, `fix(api): handle missing ticker`, `test(compute): add
growth cases`.

## Before opening a PR

- [ ] `pytest`
- [ ] Update `CHANGELOG.md`
- [ ] If the contract changed: update schemas, mock data, and consumers
- [ ] Keep external API and LLM integrations isolated behind their interfaces

## Code ownership

| Area                                                                    | Owner         |
| ----------------------------------------------------------------------- | ------------- |
| `kuartal/pipeline`, `kuartal/sectors`, `kuartal/storage`, `kuartal/llm` | Backend       |
| `kuartal/api`, `dashboard/`                                             | Dashboard/API |
| `docs/` and shared contracts                                            | Shared        |

## Reporting an issue with the plan itself

If a roadmap item in `docs/kuartal-todo.md` is no longer appropriate,
update or remove it with a brief reason rather than silently skipping it.
