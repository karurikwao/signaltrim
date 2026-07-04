'use strict';

// Strip the `tools:` field from a Claude-Code-style subagent frontmatter so
// the file is valid for opencode, whose schema rejects the YAML array form
// (`tools: [Read, Grep, Bash]`) with:
//
//   Configuration is invalid at .../agents/signalteam-reviewer.md
//   ↳ Expected object | undefined, got ["Read","Grep","Bash"] tools
//
// opencode allows `tools` to be a map (`{read: true, grep: true}`) or
// omitted entirely. Omitting falls back to opencode's default tool set,
// which is what the signalteam subagent prompts already self-restrict against
// in their body ("Read-only locator", "No `Bash` available", etc.), so
// dropping the array form is safe.

const TOOLS_FIELD_RE = /^tools[ \t]*:/;
const CONTINUATION_RE = /^[ \t]/;
const FRONTMATTER_RE = /^(---\r?\n)([\s\S]*?)(\r?\n---(?:\r?\n|$))/;

function stripOpencodeAgentTools(content) {
  if (typeof content !== 'string') return content;
  const match = content.match(FRONTMATTER_RE);
  if (!match) return content;

  const out = [];
  let dropping = false;
  let changed = false;
  for (const line of match[2].split(/\r?\n/)) {
    if (dropping) {
      if (CONTINUATION_RE.test(line)) continue;
      dropping = false;
    }
    if (TOOLS_FIELD_RE.test(line)) {
      dropping = true;
      changed = true;
      continue;
    }
    out.push(line);
  }
  if (!changed) return content;

  const eol = match[1].includes('\r\n') ? '\r\n' : '\n';
  return match[1] + out.join(eol) + match[3] + content.slice(match[0].length);
}

module.exports = { stripOpencodeAgentTools };
