#!/bin/bash
echo "Installing DocDrift pre-commit hook..."
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
source "$(dirname "$0")/../../venv/Scripts/activate"
python -m docwatcher.cli precommit
EOF
chmod +x .git/hooks/pre-commit
echo "Done. DocDrift will now run before every commit."