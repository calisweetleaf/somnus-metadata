# Complete v2 integration audit

Audit date: 2026-11-06. The supplied core 2.2.0 branch ZIP and plugin 1.3.0 ZIP are the comparison inputs. Toolkit source is 2.2.1; metadata core remains 2.0.0. PyPI still serves 2.2.0 until the correction is published.

| Supplied material | Disposition |
| --- | --- |
| All runtime modules | Integrated, including the separate heartbeat module and filename routing corrections from PR #10 |
| Cross-platform test repairs on main | Preserved; these are newer than the supplied ZIP |
| Five configuration envelopes | Migrated from sidecars into .coveragerc, .devcontainer/devcontainer.json, .gitattributes, .gitignore and .importlinter through the toolkit, preserving identity and host content |
| docs/WHERE-WE-ARE.md | Restored and updated to current release status |
| D20 decision | Ratification on main preserved |
| Source/package version and handoffs | Updated for the unpublished 2.2.1 correction |
| Private plugin 1.3.0 | Every tracked file matches the supplied plugin ZIP by Git blob hash; all 28 tests pass |
| Nested extraction folders | None tracked in either remote repository; the offline laptop's untracked working tree has not been inspected |

## Issue and pull request disposition

Issues #2, #3, #4 and #6 were already resolved in the implementation and contract, and are closed. Issue #5 is addressed by splitting the legacy migration mapper along its field families. A deterministic differential experiment compared 3,000 inputs against the original mapper: ordered payloads and errors matched, and neither version mutated its caller's input. The full unit suite also passes.

Wiki PR #9 was closed without merging: it targets a pre-D20 snapshot and removes existing metadata envelopes. Its branch remains available. The inactive Factory integration is manual-dispatch only so it no longer fails every main push on an expired subscription.

## Publication and local machine boundary

The corrective wheel and source distribution must pass strict Twine checks and installed-package acceptance before upload. Publication requires the existing authorized PyPI publisher; this cloud environment has no publishing credentials. The connected laptop is offline. No claim is made that its nested extraction folders, installed package, native plugin registrations, or global watcher have been repaired in this cloud session.

Once the laptop is reachable, inspect the original checkout with `git status` and compare nested ZIP directories before moving anything. Preserve untracked work. Install the published correction and the plugin through their documented lifecycles; verify installed/enabled records and live MCP behavior. A source merge is separate from those machine operations.

See [current handoff](WHERE-WE-ARE.md) and [release procedure](../runbooks/package-release.md).
