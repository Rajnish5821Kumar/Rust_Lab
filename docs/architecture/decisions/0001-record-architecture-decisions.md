# 1. Record architecture decisions

- Status: Accepted
- Date: 2026-09-28

## Context

DevVault will be built in phases over a long period. Choices made early (database access
style, auth design, repository layout) constrain later work, and the reasons behind them
are easy to forget.

## Decision

Record significant decisions as short Architecture Decision Records in this directory,
numbered sequentially, using the sections Context, Decision and Consequences. An ADR that
is superseded is kept and marked as such, with a link to the new record.

## Consequences

- New contributors (and a future me) can see why things are the way they are.
- Writing an ADR takes a few minutes per significant decision.
