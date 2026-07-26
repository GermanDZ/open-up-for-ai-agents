"""Standalone driver for ONE task-def, outside any phase/cycle/iteration
context (T-134). Reuses ``plan_iteration.render_task_instruction`` for the
instruction and ``loop.run``'s ``system_prompt=``/``model=`` seam (T-089) for
the sub-run — the same machinery ``cycle.py``'s internal ``run_task()`` uses
— called directly so this probe never touches ``process-map.yaml``'s real
activity wiring.

Deliberately NOT ``cycle.py``'s ``_task_system_prompt()``: that shell explicitly
forbids any tool call after ``write_file`` (T-124's convergence contract for
markdown authoring). This probe's task needs exactly one more call — ``exec``,
to run the code it just wrote — so it gets its own sibling prompt instead.
"""

from . import loop, plan_iteration

_CODE_TASK_SYSTEM_PROMPT = (
    "You are an OpenUP authoring agent performing a single code-writing task. "
    "Produce exactly the one file the instruction names.\n"
    "Converge in exactly two tool calls: (1) ONE write_file call for the "
    "source file, (2) ONE exec call that runs it and shows the expected "
    "marker in stdout. If the exec call fails or the marker is missing, you "
    "may write_file + exec again to fix it, but stop and emit "
    "`OPENUP-TASK: DONE` the moment one exec call succeeds with the marker "
    "present — do not re-run a command that already succeeded."
)


def run_probe_task(root, task_def, model, env=None, max_iterations=20,
                   interactive=False, _completion=None):
    """Drive ``task_def`` as one standalone sub-run under ``root``.

    Returns ``loop.run``'s exit code (0 == clean completion + gates passed).
    """
    instruction = plan_iteration.render_task_instruction(
        root, task_def,
        objectives=["Confirm the driver can author and execute working code"])
    return loop.run(dir=str(root), procedure=task_def.get("name") or "probe-code-artifact",
                    env=env, max_iterations=max_iterations, interactive=interactive,
                    instruction=instruction, system_prompt=_CODE_TASK_SYSTEM_PROMPT,
                    model=model, _completion=_completion)
