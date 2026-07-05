# Concepts and Modes

SignalTrim changes reply style, not task semantics.

The agent should still solve the same problem, preserve exact technical artifacts, and use normal clear prose when compression could create risk.

## Core Behavior

SignalTrim removes:

- Pleasantries.
- Hedging.
- Repetitive setup language.
- Obvious transition phrases.
- Long explanations when a compact technical statement is enough.

SignalTrim preserves:

- Code blocks.
- Inline code.
- Commands.
- File paths.
- URLs.
- Error messages.
- API names.
- Identifiers.
- Security warnings where ambiguity matters.

## Modes

| Mode | Behavior |
|---|---|
| `lite` | Full sentences, filler removed. Good for general work. |
| `full` | Default. Fragments allowed. Articles dropped where clear. |
| `ultra` | Maximum terseness while preserving meaning. |
| `wenyan-lite` | Classical Chinese style, light compression. |
| `wenyan-full` | Classical Chinese style, balanced compression. |
| `wenyan-ultra` | Classical Chinese style, maximum compression. |
| `off` | Normal agent style. |

## Commands

```text
/signaltrim
/signaltrim lite
/signaltrim full
/signaltrim ultra
/signaltrim off
```

Specialized commands:

```text
/signaltrim-commit
/signaltrim-review
/signaltrim-stats
/signaltrim-compress <file>
/signaltrim-init
```

## Language Preservation

SignalTrim should preserve the user's language. If the user writes in Spanish, Portuguese, French, or another language, the reply should compress in that language rather than silently switching to English.

## Auto-Clarity Rule

SignalTrim should drop back to normal clear prose for:

- Security warnings.
- Irreversible actions.
- Multi-step sequences where terse fragments could be misread.
- User confusion or repeated questions.
- Legal, medical, financial, or other high-stakes clarity.

After the clear section, SignalTrim can resume compact style.

Advanced mode examples: [docs/ADVANCED-MODES.md](https://github.com/karurikwao/signaltrim/blob/main/docs/ADVANCED-MODES.md).

## Good Output Example

Normal:

```text
The reason your component is re-rendering is likely because you are creating a new object reference on every render.
```

SignalTrim:

```text
New object ref each render. Inline object prop = new ref = re-render. Wrap in `useMemo`.
```

## Bad Output Example

Bad:

```text
Auth broken. Fix token thing.
```

Why bad:

- Loses the exact failure.
- Does not identify expiry logic.
- Too terse to be useful.

Better:

```text
Bug in auth middleware. Token expiry check uses `<` instead of `<=`.
```
