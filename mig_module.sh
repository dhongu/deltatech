#!/bin/sh
# Migrează un modul Odoo între două versiuni majore (implicit 19.0 → 20.0), după
# fluxul OCA: https://github.com/OCA/maintainer-tools/wiki/Migration-to-version-20.0
#
#   1. branch <to>-mig-<modul> din origin/<to>
#   2. replay istoric: git format-patch origin/<to>..origin/<from> -- <modul> | git am -3 --keep
#   3. pre-commit run -a  → commit „[IMP] <modul>: pre-commit auto fixes”
#   4. rescriere automată cu upgrade_code din Odoo (<from>.1 … <to>) + owl3-migration (pentru 20.0)
#   5. bump version în manifest: <from>.x.y.z → <to>.x.y.z
#
# Pașii 4–5 rămân ca diff necomis, pentru review + adaptare manuală; commit-ul final
# este „[MIG] <modul>: Migration to <to>”.
#
# Utilizare (din rădăcina repo-ului suitei):
#   sh mig_module.sh <modul> [--from 19.0] [--to 20.0] [--push] [--no-upgrade-code]
#
# Variabile de mediu:
#   ODOO_DIR  directorul cu sursa Odoo <to> (implicit: se caută ../odoo, ../../odoo, ...)
#   PYTHON    interpretorul (implicit: .venv/bin/python de lângă ODOO_DIR, altfel python3)
#   UPGRADE_CODE_SKIP  scripturi upgrade_code de sărit, separate prin virgulă
#             (implicit în mig_upgrade_code.py: 19.3-00-account-groups)
#
# Tot corpul e într-o funcție: shell-ul o citește integral înainte de `git checkout`,
# care poate înlocui chiar acest fișier în working tree.

main() {
    module=""
    from="19.0"
    to="20.0"
    push=0
    upgrade_code=1
    while [ $# -gt 0 ]; do
        case "$1" in
            --from) from="$2"; shift 2 ;;
            --to) to="$2"; shift 2 ;;
            --push) push=1; shift ;;
            --no-upgrade-code) upgrade_code=0; shift ;;
            -h|--help) sed -n '2,25p' "$0"; exit 0 ;;
            -*) echo "Eroare: opțiune necunoscută $1"; exit 1 ;;
            *) module="${1%/}"; shift ;;
        esac
    done

    if [ -z "$module" ]; then
        echo "Eroare: Trebuie să furnizezi numele modulului ca argument"
        exit 1
    fi

    root=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "Eroare: nu ești într-un repo git"; exit 1; }
    cd "$root" || exit 1
    branch="$to-mig-$module"

    if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
        echo "Eroare: working tree-ul are modificări necomise în $root."
        echo "Comite/stash-uiește-le sau lucrează într-un worktree separat:"
        echo "  git worktree add ../$(basename "$root")-$branch origin/$to"
        exit 1
    fi

    git fetch -q origin "$from" "$to" || { echo "Eroare: git fetch origin $from $to a eșuat"; exit 1; }

    if git rev-parse -q --verify "refs/heads/$branch" >/dev/null; then
        echo "Eroare: branch-ul $branch există deja. Șterge-l (git branch -D $branch) dacă vrei să reiei."
        exit 1
    fi
    if [ -z "$(git ls-tree "origin/$from" -- "$module")" ]; then
        echo "Eroare: modulul $module nu există pe origin/$from"
        exit 1
    fi
    if [ -n "$(git ls-tree "origin/$to" -- "$module")" ]; then
        echo "Atenție: modulul $module există deja pe origin/$to — se aplică doar commit-urile lipsă."
    fi

    git checkout -q -b "$branch" "origin/$to" || exit 1
    git branch -q --unset-upstream 2>/dev/null

    patches=$(git format-patch --keep-subject --stdout "origin/$to..origin/$from" -- "$module")
    if [ -z "$patches" ]; then
        echo "Atenție: Nu există patch-uri pentru modulul $module între origin/$to și origin/$from"
        exit 0
    fi

    echo "Aplicăm patch-urile pentru modulul $module ($from → $to)..."
    if ! git format-patch --keep-subject --stdout "origin/$to..origin/$from" -- "$module" | git am -3 --keep; then
        echo "Eroare: A eșuat aplicarea patch-urilor!"
        echo "Rezolvă conflictele, apoi: git add <fișiere> && git am --continue"
        echo "(poți încerca și --ignore-whitespace; pentru anulare: git am --abort)"
        echo "După aceea rulează din nou pașii rămași: pre-commit, upgrade_code, bump versiune."
        exit 1
    fi

    # formatare într-un singur commit, separat de adaptările de migrare
    pre-commit run -a >/dev/null 2>&1
    git add -A
    git commit -q -m "[IMP] $module: pre-commit auto fixes" --no-verify && echo "Commit: [IMP] $module: pre-commit auto fixes"

    if [ "$upgrade_code" = 1 ]; then
        run_upgrade_code
    fi

    manifest="$module/__manifest__.py"
    if [ -f "$manifest" ]; then
        sed -i.bak -E "s/([\"'])version([\"'][[:space:]]*:[[:space:]]*[\"'])$from\./\1version\2$to./" "$manifest" && rm -f "$manifest.bak"
        grep -E "[\"']version[\"']" "$manifest" | sed 's/^ */Versiune: /'
    fi

    if [ "$push" = 1 ]; then
        git push --set-upstream origin "$branch"
    fi

    echo
    echo "Replay-ul pentru $module s-a finalizat pe branch-ul $branch."
    echo "Diff necomis (upgrade_code + versiune): git status / git diff"
    echo "După adaptarea manuală: git commit -am \"[MIG] $module: Migration to $to\""
}

run_upgrade_code() {
    odoo_dir="$ODOO_DIR"
    if [ -z "$odoo_dir" ]; then
        # urcă din repo (sau din repo-ul principal, dacă rulăm într-un worktree)
        common=$(cd "$(git rev-parse --git-common-dir)" && pwd)
        for start in "$root" "$(dirname "$common")"; do
            d="$start"
            while [ "$d" != "/" ]; do
                d=$(dirname "$d")
                if [ -f "$d/odoo/odoo/cli/upgrade_code.py" ]; then odoo_dir="$d/odoo"; break 2; fi
            done
        done
    fi
    helper="$(dirname "$odoo_dir")/scripts/mig_upgrade_code.py"
    if [ -z "$odoo_dir" ] || [ ! -f "$helper" ]; then
        echo "Atenție: nu găsesc Odoo $to / scripts/mig_upgrade_code.py (setează ODOO_DIR) — sar peste upgrade_code."
        return
    fi
    py="$PYTHON"
    [ -z "$py" ] && [ -x "$(dirname "$odoo_dir")/.venv/bin/python" ] && py="$(dirname "$odoo_dir")/.venv/bin/python"
    [ -z "$py" ] && py=python3

    # rulează scripturile oficiale într-un sandbox (modul + dependențe), aduce înapoi doar modulul
    "$py" "$helper" --module-dir "$root/$module" --from "$from" --to "$to" --odoo-dir "$odoo_dir" \
        ${UPGRADE_CODE_SKIP:+--skip "$UPGRADE_CODE_SKIP"} 2>&1 | grep -vE '^(updated|deleted): /'
    return 0
}

main "$@"
