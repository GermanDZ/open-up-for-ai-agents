"""Reference OpenAI-compatible driver for harness-optional OpenUP (T-072).

A plain Python agentic loop that drives an OpenUP procedure end-to-end against
any OpenAI-compatible chat-completions endpoint, consuming the T-071 neutral
procedure pack directly. Stdlib-only (no runtime dependency).

Modules:
  tiers  — resolve a procedure's `tier:` to a model via tier-map.yaml (driver column)
  tools  — the six-tool surface (read_file, write_file, edit_file, glob, grep, exec)
  llm    — urllib OpenAI-compatible chat-completions client
  loop   — the agentic loop + deterministic gate enforcement + sentinel handling
"""
