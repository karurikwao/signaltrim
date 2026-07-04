#!/usr/bin/env node
// signalteam model overrides — patch installed agent frontmatter from env vars.
//
// Called by signaltrim-activate.js early in SessionStart so users can pin
// per-agent models without shadow-copying entire agent files.
//
// Env vars:
//   SIGNALTEAM_REVIEWER_MODEL    → agents/signalteam-reviewer.md
//   SIGNALTEAM_BUILDER_MODEL     → agents/signalteam-builder.md
//   SIGNALTEAM_INVESTIGATOR_MODEL → agents/signalteam-investigator.md
//
// Rules:
//   - Unset / blank → no-op.
//   - Values containing newlines or control characters → ignored.
//   - Existing `model:` line in frontmatter → replaced in-place.
//   - No `model:` line → inserted after `tools:` (or before closing `---`).
//   - File missing / outside plugin layout → silent no-op.
//   - All filesystem errors → silent fail.

const fs = require('fs');
const path = require('path');

const AGENT_ENV_MAP = [
  { envVar: 'SIGNALTEAM_REVIEWER_MODEL',     file: path.join('agents', 'signalteam-reviewer.md') },
  { envVar: 'SIGNALTEAM_BUILDER_MODEL',      file: path.join('agents', 'signalteam-builder.md') },
  { envVar: 'SIGNALTEAM_INVESTIGATOR_MODEL', file: path.join('agents', 'signalteam-investigator.md') },
];

function hasAgentsDir(root) {
  try {
    return fs.statSync(path.join(root, 'agents')).isDirectory();
  } catch (e) {
    return false;
  }
}

// Return the plugin root directory given the hooks directory path.
//
// Shipped plugin layout invokes hooks from <plugin_root>/src/hooks, while old
// standalone installs used <plugin_root>/hooks. Prefer CLAUDE_PLUGIN_ROOT when
// Claude provides it, then probe both nearby layouts for the agents/ directory.
function resolvePluginRoot(hookDir, env) {
  const envArg = env || process.env;
  const candidates = [];

  if (envArg.CLAUDE_PLUGIN_ROOT) {
    candidates.push(path.resolve(envArg.CLAUDE_PLUGIN_ROOT));
  }

  const resolvedHookDir = path.resolve(hookDir);
  candidates.push(
    path.resolve(resolvedHookDir, '..'),
    path.resolve(resolvedHookDir, '..', '..')
  );

  const seen = new Set();
  for (const candidate of candidates) {
    if (seen.has(candidate)) continue;
    seen.add(candidate);
    if (hasAgentsDir(candidate)) return candidate;
  }

  return candidates[0];
}

// Patch the YAML frontmatter of `content` to set `model: <modelValue>`.
// Returns the patched string, or the original if no frontmatter or already identical.
// Rejects `modelValue` strings that contain newlines or control characters.
function patchFrontmatterModel(content, modelValue) {
  // Reject blank or unsafe model strings
  if (!modelValue || /[\x00-\x1f\x7f]/.test(modelValue)) return content;

  // Must begin with YAML frontmatter delimiter
  if (!content.startsWith('---')) return content;

  // Find the closing ---
  const closeIdx = content.indexOf('\n---', 3);
  if (closeIdx === -1) return content;

  const fmRaw = content.slice(0, closeIdx);           // opening --- through last fm line
  const after  = content.slice(closeIdx);             // \n--- onward (body)

  // Preserve original line ending so we don't create mixed CRLF/LF on Windows
  const nl = fmRaw.includes('\r\n') ? '\r\n' : '\n';

  const modelLine = 'model: ' + modelValue;
  const modelRe   = /^model:[ \t]*.*$/m;

  if (modelRe.test(fmRaw)) {
    // Replace existing model: line
    const patched = fmRaw.replace(modelRe, modelLine);
    if (patched === fmRaw) return content;            // already identical
    return patched + after;
  }

  // Insert after tools: line when present; else before closing ---
  const toolsMatch = fmRaw.match(/^tools:[ \t]*.*$/m);
  if (toolsMatch) {
    const toolsEnd = fmRaw.indexOf(toolsMatch[0]) + toolsMatch[0].length;
    return fmRaw.slice(0, toolsEnd) + nl + modelLine + fmRaw.slice(toolsEnd) + after;
  }

  // Append before closing delimiter
  return fmRaw + nl + modelLine + after;
}

// Apply all env-var overrides to agent files under `pluginRoot`.
// `env` defaults to process.env; pass an object in tests.
function applyOverrides(pluginRoot, env) {
  const envArg = env || process.env;
  for (const { envVar, file } of AGENT_ENV_MAP) {
    const raw = envArg[envVar];
    if (!raw || !raw.trim()) continue;

    const modelValue = raw.trim();
    if (/[\x00-\x1f\x7f]/.test(modelValue)) continue;

    const agentPath = path.join(pluginRoot, file);
    let content;
    try {
      content = fs.readFileSync(agentPath, 'utf8');
    } catch (e) {
      continue; // missing file or wrong layout → silent no-op
    }

    const patched = patchFrontmatterModel(content, modelValue);
    if (patched === content) continue;

    try {
      fs.writeFileSync(agentPath, patched, 'utf8');
    } catch (e) {
      // Silent fail — never block session start
    }
  }
}

module.exports = { resolvePluginRoot, patchFrontmatterModel, applyOverrides, AGENT_ENV_MAP };
