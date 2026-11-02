# somnus:metadata:v2
# somnus:
#   schema: "somnus://metadata/core/2.0.0"
#   id: "urn:somnus:artifact:01a19a67-7cd0-708b-83f3-6fdd0a3b1a1e"
#   revision: 1
#   title: "Module entry point so python -m somnus behaves like the somnus script"
#   classification:
#     category: "engineering"
#     type: "source-code"
#     role: "informative"
#     scope: "component"
#     tags: []
#   lifecycle:
#     status: "draft"
#   authority:
#     standing: "candidate"
#     scopes:
#       - target_ref: "urn:somnus:artifact:01a19a67-7cd0-708b-83f3-6fdd0a3b1a1e"
#         aspects: ["content"]
#   time: {}
#   names:
#     slug: "module-entry-point-so-python-m-somnus-behaves-like-the-somnus-script"
#   knowledge:
#     coverage: "artifact"
#     subjects: ["urn:somnus:artifact:01a19a67-7cd0-708b-83f3-6fdd0a3b1a1e"]
#   access:
#     visibility: "internal"
#     allowed_uses: ["archive", "search", "reason"]
#   ingestion:
#     disposition: "candidate"
#     body_role: "source"
# somnus:end
"""Module entry point so `python -m somnus` behaves like the `somnus` script."""

import sys

from somnus.cli import main

if __name__ == "__main__":
    sys.exit(main())
