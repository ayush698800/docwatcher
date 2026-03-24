#!/bin/bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-$(command -v python)}"

echo "Installing DocDrift pre-commit hook..."
cat > .git/hooks/pre-commit <<EOF
#!/bin/bash
set -euo pipefail
"${PYTHON_BIN}" -m docwatcher.cli precommit
EOF

chmod +x .git/hooks/pre-commit
echo "Done. DocDrift will now run before every commit."
