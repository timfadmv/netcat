# Security protocol

How security work is done and recorded in this repository, so that a reader can tell what was
**development**, what was **practice** and what was a **vulnerability fix**.

## 1. Baseline

The tag `baseline-v0.1` marks the state of the application before the vulnerability work started. It
contains known, unfixed vulnerabilities on purpose, so every proof of concept can be reproduced against it:

```bash
git checkout baseline-v0.1
```

Everything before the tag is ordinary development. Work after it follows this protocol.

## 2. Commit types

Commits follow Conventional Commits. Three kinds of security work are marked explicitly:

| Subject starts with | Meaning |
|---|---|
| `fix(security):` | remediation of a finding in the application |
| `test(security):` | a regression test that reproduces a finding (red before the fix, green after) |
| `training(<topic>):` | practice: reproducing an attack, a proof of concept, an experiment, deliberately vulnerable code. Not part of the product |

All other types (`feat`, `fix`, `docs`, `ci`, `build`, `chore`, `refactor`, `test`) are normal development.

Security commits carry trailers at the end of the message:

```
Finding: F-001
CWE: CWE-79
Severity: Medium
```

`training` commits also carry `Practice: <what was practised>`.

Find the commits by kind:

```bash
git log --oneline --grep='^training'                  # practice
git log --oneline --grep='^fix(security)'             # remediation
git log --oneline --grep='^test(security)'            # regression tests
git log --oneline --grep='Finding: F-001'             # everything about one finding
git log --oneline --invert-grep --grep='^training'    # everything except practice
```

## 3. Branches and pull requests

- `fix/F-001-<short-name>`: remediation of one finding (may contain `training`, `test` and `fix` commits)
- `training/<topic>`: practice only, never contains a fix
- one finding per pull request; the pull request template asks for the type and the evidence

## 4. Life cycle of a finding

| Step | What is recorded |
|---|---|
| 1. Register | an issue from the *Security finding* template with a stable id (`F-001`, `F-002`, ...) |
| 2. Reproduce | steps and expected result of the proof of concept, run against `baseline-v0.1` |
| 3. Triage | CWE, CVSS 3.1 vector and score, and the preconditions that lower or raise the real risk |
| 4. Test | a failing regression test (`test(security):`) |
| 5. Fix | the smallest change that closes the cause (`fix(security):`), not only the symptom |
| 6. Verify | the new test passes, the proof of concept no longer works, the other checks still pass |
| 7. Document | `docs/security/F-001-<name>.md`: root cause, fix, verification, residual risk |
| 8. Close | the issue is closed by the pull request |

## 5. Severity

CVSS 3.1 base score, then adjusted for the context of this application (a tool meant for a local
machine, without authentication). The adjustment and its reason are written down in the finding.

| Score | Severity |
|---|---|
| 9.0 - 10.0 | Critical |
| 7.0 - 8.9 | High |
| 4.0 - 6.9 | Medium |
| 0.1 - 3.9 | Low |

## 6. Findings

The register of findings is kept in the issue tracker (label `security`). Each closed finding has a
document in `docs/security/`.
