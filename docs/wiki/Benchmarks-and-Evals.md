# Benchmarks and Evals

SignalTrim makes a narrow public claim: it reduces output tokens in measured prompts. It does not claim that every full session is cheaper.

## Public Number

The README currently reports a 65% average output-token reduction across 10 benchmark prompts.

The honest caveat:

- Output tokens can shrink.
- Input tokens do not vanish.
- Reasoning tokens do not vanish.
- Rule text has overhead.
- Already-terse workflows can be net-negative.

Full discussion:

```text
docs/HONEST-NUMBERS.md
```

## Benchmark Harness

Path:

```text
benchmarks/
```

Important files:

| File | Purpose |
|---|---|
| `benchmarks/prompts.json` | Prompt set. |
| `benchmarks/run.py` | Benchmark runner. |
| `benchmarks/requirements.txt` | Python deps. |
| `benchmarks/results/` | Output location. |

## Evals

Path:

```text
evals/
```

Important files:

| File | Purpose |
|---|---|
| `evals/measure.py` | Measurement utilities. |
| `evals/llm_run.py` | LLM-backed eval helper. |
| `evals/plot.py` | Plotting helper. |
| `evals/snapshots/results.json` | Snapshot data. |
| `evals/prompts/en.txt` | Prompt source. |

## Compression Fixtures

Compression fixtures live at:

```text
tests/signaltrim-compress/
```

They are used by:

```bash
python tests/verify_repo.py
```

## Verification Commands

```bash
python tests/verify_repo.py
python -m unittest discover -s tests -p "test_*.py"
npm test
node tests/test_mcp_shrink.js
npm pack --dry-run --json
```

## How To Interpret Results

Good SignalTrim benchmark results should show:

- Smaller output.
- No lost commands, paths, URLs, or code.
- No hidden input-token claim.
- Reproducible data committed near the claim.

Bad benchmark results:

- Cherry-picked only.
- No raw prompt data.
- No caveat about input tokens.
- No regression tests.

