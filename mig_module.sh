#!/bin/sh

module=$1
# Verifică dacă modulul a fost furnizat
if [ -z "$module" ]; then
    echo "Eroare: Trebuie să furnizezi numele modulului ca argument"
    exit 1
fi
git fetch
git checkout -b 19.0-mig-$module

# Verifică dacă există patch-uri de aplicat
patches=$(git format-patch --keep-subject --stdout origin/19.0..origin/18.0 -- $module)
if [ -z "$patches" ]; then
    echo "Atenție: Nu există patch-uri pentru modulul $module între origin/19.0 și origin/18.0"
    exit 0
fi

# Aplicăm patch-urile cu verificarea erorilor
echo "Aplicăm patch-urile pentru modulul $module..."
if ! git format-patch --keep-subject --stdout origin/19.0..origin/18.0 -- $module | git am -3 --keep; then
    echo "Eroare: A eșuat aplicarea patch-urilor!"
    echo "Pentru a anula modificările, rulează: git am --abort"
    exit 1
fi

# ... existing code ...
pre-commit run -a  # to run black, isort and prettier (ignore pylint errors at this stage)
git add -A
git commit -m "[IMP] $module: pre-commit stuff"  --no-verify  # it is important to do all formatting in one commit the first time

echo "Migrarea pentru modulul $module s-a finalizat cu succes!"

git push --set-upstream origin 19.0-mig-$module
