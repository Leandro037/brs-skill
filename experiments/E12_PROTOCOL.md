# E12 Protocol — Paired Python code validation with hidden tests

## Goal

Evaluate BRS on generated Python code using the exact same raw candidate before and after BRS validation/repair.

## Design

For each task:

1. generate one Python function;
2. freeze the raw code;
3. evaluate it with hidden unit tests;
4. pass that exact raw code to BRS;
5. if syntax/safety/tests fail, allow one localized OpenAI repair;
6. rerun the complete hidden test suite;
7. compare raw vs final behavior.

## Safety restrictions

Generated code is rejected before execution if it contains:

- imports;
- calls to eval, exec, compile, open, input, or __import__.

Execution occurs in a short-lived subprocess with a timeout.

## Primary outcomes

- raw hidden-test pass rate;
- BRS final hidden-test pass rate;
- detected defects;
- successful repairs;
- unsafe releases;
- repair calls and repair tokens.

## Interpretation boundary

Tasks are synthetic programming exercises. Hidden tests are deterministic and frozen before result inspection. E12 evaluates functional code repair in this benchmark only.
