# E18 Protocol — External BFCL tool-calling pilot

## Goal

Test BRS outside code generation on structured tool/function calls that could be executed by an agent.

## External benchmark

E18 uses public BFCL v4 data from the Berkeley Function Calling Leaderboard.

Selected categories:

- `simple_python`: one relevant tool, argument extraction;
- `multiple`: select the correct tool among several candidates;
- `irrelevance`: abstain when no available tool should be called.

The benchmark questions, function schemas, and possible-answer labels come from BFCL. The BRS project does not author the task content.

## Model

- generation: `gpt-4o-mini`
- repair: `gpt-4o-mini`

The same model is used for generation and repair.

## Sample

30 cases total:

- 10 deterministic spaced cases from simple_python;
- 10 deterministic spaced cases from multiple;
- 10 deterministic spaced cases from irrelevance.

One model generation per case.

## Artifact contract

The model returns JSON in this normalized shape:

```json
{
  "calls": [
    {
      "name": "tool_name",
      "arguments": {}
    }
  ]
}
```

For BFCL irrelevance cases the correct output is:

```json
{"calls":[]}
```

## Paired design

For every case:

1. load the external BFCL question and tool schemas;
2. generate one candidate;
3. freeze the raw candidate;
4. evaluate RAW against the frozen external label/contract;
5. pass the same artifact to BRS;
6. if a mandatory check fails, allow one repair attempt;
7. fully revalidate;
8. record RELEASE/BLOCK and final external correctness.

## Checks

- JSON root/object contract;
- `calls` is a list;
- call count is compatible with the selected BFCL category;
- function name exists in the provided tool documentation;
- required arguments and basic BFCL schema types are valid;
- external BFCL possible-answer match;
- irrelevance cases require zero calls.

## External-label oracle

For simple/multiple categories, E18 compares the predicted function name and arguments against BFCL's public `possible_answer` data.

For irrelevance, BFCL defines the expected behavior as no function call.

This pilot uses an internal adapter over BFCL labels rather than the full official leaderboard scoring CLI. If E18 shows useful headroom, a follow-up can integrate the complete BFCL evaluator.

## Repair evidence

BRS receives localized failure evidence from the contract/oracle. It may include expected tool name/argument variants for a failed BFCL label check.

Therefore E18 is a **validator-feedback repair** experiment, not a zero-feedback tool-use benchmark.

## Primary outcomes

- raw external-label pass rate;
- post-BRS pass rate;
- RAW FAIL → BRS PASS;
- RAW PASS → BRS FAIL;
- defect detection;
- repair success;
- unresolved BLOCKs;
- unsafe releases;
- release/oracle mismatch;
- token overhead.

## Limitations

- 30-case pilot only;
- external data/labels but internal adapter;
- one model/provider;
- one repair attempt;
- repair receives localized validation evidence;
- no claim of official BFCL leaderboard comparability.
