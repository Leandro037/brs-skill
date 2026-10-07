# E15 Protocol — Real-world AI portfolio agent

## Goal

Move BRS from synthetic artifacts to a user-facing application where AI-generated edits can affect a real landing page.

## Artifact

A complete professional portfolio JSON document rendered by an interactive landing page.

## User flow

1. user loads the landing;
2. user requests a content change in natural language;
3. the model proposes a complete updated portfolio artifact;
4. BRS validates the candidate;
5. repair is allowed only for failed portfolio checks;
6. after repair, all checks are rerun;
7. UI applies the update only after RELEASE.

## Mandatory checks

- root artifact is an object;
- required top-level sections exist;
- hero contains non-empty title/subtitle/eyebrow/CTAs;
- stats is a non-empty list of value/label objects;
- projects contains at least 3 valid project cards;
- experience contains at least 2 structured entries;
- skills contains at least 5 non-empty strings;
- contact contains title/body and valid http(s) links;
- no empty project or experience titles;
- URL-bearing fields use http(s) or local anchors;
- safety gate requires zero mandatory failures.

## Repair policy

One repair attempt.

The repair model receives only the failed checks plus the current artifact and must return a full JSON artifact.

## Release rule

The browser only applies AI edits after BRS returns RELEASE.

## Research boundary

E15 is a real application integration test. It is not yet a controlled comparative experiment. A later E15-B should generate a frozen edit suite and compare raw model proposals against BRS-mediated proposals.
