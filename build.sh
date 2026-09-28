#!/usr/bin/env bash
#
# Profile-driven resume builder.
#
#   ./build.sh --profile jane                     build everything for a profile
#   ./build.sh --profile jane --document main     just one document
#   ./build.sh --profile jane --variant SSE       just one variant
#   ./build.sh --profile jane --format pdf        just one format
#   ./build.sh --list                             list available profiles
#   ./build.sh --check --profile jane             validate without building
#   ./build.sh --new alice                        scaffold a new profile
#   ./build.sh --app <application dir>           build one tailored application
#
#   ./build.sh --init-data [git url]              clone, or create, the resume-data repo
#   ./build.sh --data-pull                        fast-forward resume-data from GitHub
#   ./build.sh --data-push "<message>"            commit and push resume-data
#   ./build.sh --migrate-data                     move a pre-2.0 data/ to resume-data/
#
# All personal data lives in resume-data/: a separate, private git repo cloned
# next to this one and gitignored here. A profile is resume-data/profiles/<name>/
# holding meta/, resume.json and settings.json; an application dir holds the
# same two JSON files for one JD. Override the location with RESUME_DATA_DIR.
# Nothing about any individual person is hardcoded in this script.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="${RESUME_DATA_DIR:-$ROOT/resume-data}"
LEGACY_DATA_DIR="$ROOT/data"
DATA_GITIGNORE="$ROOT/templates/data.gitignore"
PROFILES_DIR="$DATA_DIR/profiles"
TEMPLATES_DIR="$ROOT/templates"
SCAFFOLD_DIR="$TEMPLATES_DIR/profile"
META_TEMPLATE="$ROOT/.claude/skills/create-resume/assets/meta.template.json"
RENDER="$ROOT/lib/render.py"
DIST_DIR="$DATA_DIR/dist"
FINAL_DIR="$DATA_DIR/final"
TIMESTAMP="$(date +"%Y%m%d_%H%M%S")"

PROFILE="${RESUME_PROFILE:-}"
ONLY_DOCUMENT=""
ONLY_VARIANT=""
ONLY_FORMAT=""
DO_LIST=0
DO_CHECK=0
NEW_PROFILE=""
APP_DIR=""
DATA_ACTION=""
DATA_ARG=""

die() { echo "error: $*" >&2; exit 1; }
info() { echo "  $*"; }

usage() { sed -n '3,24p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; }

while [ $# -gt 0 ]; do
    case "$1" in
        --profile)  PROFILE="${2:-}"; shift 2 ;;
        --document) ONLY_DOCUMENT="${2:-}"; shift 2 ;;
        --variant)  ONLY_VARIANT="${2:-}"; shift 2 ;;
        --format)   ONLY_FORMAT="${2:-}"; shift 2 ;;
        --new)      NEW_PROFILE="${2:-}"; shift 2 ;;
        --app)      APP_DIR="${2:-}"; shift 2 ;;
        --init-data)
            DATA_ACTION="init"; shift
            if [ $# -gt 0 ] && [ "${1#--}" = "$1" ]; then DATA_ARG="$1"; shift; fi ;;
        --data-pull)    DATA_ACTION="pull"; shift ;;
        --data-push)    DATA_ACTION="push"; DATA_ARG="${2:-}"; shift 2 || shift ;;
        --migrate-data) DATA_ACTION="migrate"; shift ;;
        --list)     DO_LIST=1; shift ;;
        --check)    DO_CHECK=1; shift ;;
        -h|--help)  usage; exit 0 ;;
        *)          die "unknown argument: $1 (try --help)" ;;
    esac
done

command -v python3 >/dev/null || die "python3 is required"

# ------------------------------------------------------------ data repo

is_data_repo() { git -C "$DATA_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1 \
    && [ "$(git -C "$DATA_DIR" rev-parse --show-toplevel)" = "$(cd "$DATA_DIR" && pwd -P)" ]; }
has_remote() { [ -n "$(git -C "$DATA_DIR" remote 2>/dev/null)" ]; }

case "$DATA_ACTION" in
    migrate)
        [ -d "$LEGACY_DATA_DIR" ] || die "nothing to migrate: $LEGACY_DATA_DIR does not exist"
        [ -e "$DATA_DIR" ] && die "$DATA_DIR already exists; merge by hand"
        mv "$LEGACY_DATA_DIR" "$DATA_DIR"
        echo "Moved data/ -> $(basename "$DATA_DIR")/"
        echo "Next: ./build.sh --init-data   (make it a git repo)"
        exit 0 ;;
    init)
        if [ -n "$DATA_ARG" ]; then
            [ -e "$DATA_DIR" ] && die "$DATA_DIR already exists; move it aside to clone"
            git clone "$DATA_ARG" "$DATA_DIR"
            echo "Cloned $DATA_ARG -> $DATA_DIR"
            exit 0
        fi
        mkdir -p "$DATA_DIR/profiles" "$DATA_DIR/applications"
        is_data_repo && die "$DATA_DIR is already a git repo"
        git -C "$DATA_DIR" init -q -b main
        cp "$DATA_GITIGNORE" "$DATA_DIR/.gitignore"
        git -C "$DATA_DIR" add -A
        git -C "$DATA_DIR" commit -q -m "Initial resume data" || true
        echo "Initialized git repo in $DATA_DIR"
        echo "Next: gh repo create <you>/resume-data --private --source \"$DATA_DIR\" --push"
        exit 0 ;;
    pull)
        is_data_repo || { echo "resume-data is not a git repo; skipping pull" >&2; exit 0; }
        has_remote || { echo "resume-data has no remote; skipping pull" >&2; exit 0; }
        git -C "$DATA_DIR" fetch -q
        if ! git -C "$DATA_DIR" merge --ff-only -q '@{u}' 2>/dev/null; then
            echo "error: resume-data has diverged from its remote (changes on two machines)." >&2
            echo "Inspect with: git -C \"$DATA_DIR\" log --oneline HEAD...@{u}" >&2
            exit 3
        fi
        echo "resume-data is up to date"
        exit 0 ;;
    push)
        [ -n "$DATA_ARG" ] || die "--data-push needs a commit message"
        is_data_repo || die "resume-data is not a git repo (run ./build.sh --init-data)"
        git -C "$DATA_DIR" add -A
        if git -C "$DATA_DIR" diff --cached --quiet; then
            echo "resume-data: nothing to commit"
        else
            git -C "$DATA_DIR" commit -q -m "$DATA_ARG"
            echo "resume-data: committed \"$DATA_ARG\""
        fi
        if has_remote; then
            git -C "$DATA_DIR" push -q
            echo "resume-data: pushed"
        else
            echo "warning: resume-data has no remote; commit kept locally" >&2
        fi
        exit 0 ;;
esac

# A pre-2.0 install keeps data in data/. Refuse to silently start a new,
# empty resume-data/ next to it.
if [ -z "${RESUME_DATA_DIR:-}" ] && [ -d "$LEGACY_DATA_DIR" ] && [ ! -e "$DATA_DIR" ]; then
    die "found data/ from a pre-2.0 install. Run ./build.sh --migrate-data, then ./build.sh --init-data"
fi

# Page count straight from the pdflatex log, so no poppler dependency.
page_count() {
    # The log wraps at 79 columns, so join lines before matching.
    tr -d '\n' < "$1" 2>/dev/null \
        | sed -n 's/.*Output written on .*(\([0-9][0-9]*\) pages*,.*/\1/p'
}

# ------------------------------------------------------------- application

if [ -n "$APP_DIR" ]; then
    [ -d "$APP_DIR" ] || die "no such application dir: $APP_DIR"
    APP_DIR="$(cd "$APP_DIR" && pwd)"
    command -v pdflatex >/dev/null \
        || die "pdflatex is required for application builds (install MacTeX / TeX Live)"
    python3 "$RENDER" check --profile-dir "$APP_DIR" >/dev/null || exit 1

    IFS=$'\t' read -r doc variant basename _ \
        < <(python3 "$RENDER" plan --profile-dir "$APP_DIR" | head -1)
    work="$APP_DIR/.build"
    mkdir -p "$work"
    python3 "$RENDER" render \
        --profile-dir "$APP_DIR" --document "$doc" --variant "$variant" \
        --templates-dir "$TEMPLATES_DIR" \
        --out-tex "$work/resume.tex" --out-txt "$APP_DIR/resume.txt"
    if ! ( cd "$work" && pdflatex -interaction=nonstopmode -halt-on-error resume.tex >/dev/null ); then
        grep -m5 -A3 '^!' "$work/resume.log" >&2 || true
        die "pdflatex failed (full log: $work/resume.log)"
    fi
    cp "$work/resume.pdf" "$APP_DIR/$basename.pdf"
    echo "pdf: $APP_DIR/$basename.pdf"
    echo "txt: $APP_DIR/resume.txt"
    echo "pages: $(page_count "$work/resume.log")"
    exit 0
fi

# ------------------------------------------------------------------ profiles

list_profiles() {
    find "$PROFILES_DIR" -mindepth 1 -maxdepth 1 -type d ! -name '_*' \
        -exec basename {} \; 2>/dev/null | sort
}

if [ "$DO_LIST" -eq 1 ]; then
    echo "Profiles in $PROFILES_DIR:"
    found=0
    while read -r name; do
        [ -z "$name" ] && continue
        found=1
        desc="$(python3 -c "
import json,sys
try:
    s=json.load(open('$PROFILES_DIR/$name/settings.json'))
    docs=','.join(d['id'] for d in s.get('documents',[]))
    vars=','.join(v['id'] for v in s.get('variants',[]))
    print(f'documents: {docs} | variants: {vars}')
except Exception as e:
    print('(unreadable settings.json)')
" 2>/dev/null)"
        printf '  %-16s %s\n' "$name" "$desc"
    done < <(list_profiles)
    [ "$found" -eq 0 ] && echo "  (none yet -- create one with: ./build.sh --new <name>)"
    exit 0
fi

if [ -n "$NEW_PROFILE" ]; then
    target="$PROFILES_DIR/$NEW_PROFILE"
    [ -e "$target" ] && die "profile already exists: $target"
    [ -d "$SCAFFOLD_DIR" ] || die "missing scaffold: $SCAFFOLD_DIR"
    mkdir -p "$target/meta/inbox" "$DATA_DIR/applications/$NEW_PROFILE"
    cp "$SCAFFOLD_DIR"/*.json "$target/"
    [ -f "$META_TEMPLATE" ] && cp "$META_TEMPLATE" "$target/meta/meta.json"
    echo "Created profile: resume-data/profiles/$NEW_PROFILE"
    echo "Next:"
    echo "  1. Fill resume-data/profiles/$NEW_PROFILE/meta/meta.json, or drop an old resume /"
    echo "     LinkedIn export into meta/inbox/ and run /create-resume"
    echo "  2. /create-resume <job description>   (or no args for a general resume)"
    exit 0
fi

# Fall back to the only profile present, if there is exactly one.
if [ -z "$PROFILE" ]; then
    count="$(list_profiles | wc -l | tr -d ' ')"
    if [ "$count" = "1" ]; then
        PROFILE="$(list_profiles)"
    else
        die "--profile is required (see ./build.sh --list)"
    fi
fi

PROFILE_DIR="$PROFILES_DIR/$PROFILE"
[ -d "$PROFILE_DIR" ] || die "no such profile: $PROFILE (see ./build.sh --list)"

python3 "$RENDER" check --profile-dir "$PROFILE_DIR" || exit 1
[ "$DO_CHECK" -eq 1 ] && exit 0

# --------------------------------------------------------------- toolchain

HAVE_PDF=0
HAVE_DOCX=""
command -v pdflatex >/dev/null && HAVE_PDF=1
if command -v textutil >/dev/null; then HAVE_DOCX="textutil"
elif command -v pandoc >/dev/null; then HAVE_DOCX="pandoc"; fi

make_docx() {
    local src="$1" dest="$2"
    case "$HAVE_DOCX" in
        textutil) textutil -convert docx "$src" -output "$dest" ;;
        pandoc)   pandoc "$src" -f markdown -t docx -o "$dest" ;;
    esac
}

# ------------------------------------------------------------------- build

mkdir -p "$DIST_DIR"
echo "Building profile '$PROFILE'"

built=0
skipped_pdf=0
skipped_docx=0

while IFS=$'\t' read -r doc variant basename formats; do
    [ -z "${doc:-}" ] && continue
    [ -n "$ONLY_DOCUMENT" ] && [ "$ONLY_DOCUMENT" != "$doc" ] && continue
    [ -n "$ONLY_VARIANT" ]  && [ "$ONLY_VARIANT"  != "$variant" ] && continue

    out_dir="$FINAL_DIR/$variant"
    mkdir -p "$out_dir"

    stem="${basename}_${TIMESTAMP}"
    tex="$DIST_DIR/$stem.tex"
    txt="$DIST_DIR/$stem.txt"

    echo "[$doc / $variant] -> $basename"
    python3 "$RENDER" render \
        --profile-dir "$PROFILE_DIR" \
        --document "$doc" --variant "$variant" \
        --templates-dir "$TEMPLATES_DIR" \
        --out-tex "$tex" --out-txt "$txt"

    want() {
        [ -n "$ONLY_FORMAT" ] && { [ "$ONLY_FORMAT" = "$1" ] && return 0 || return 1; }
        case ",$formats," in *",$1,"*) return 0 ;; *) return 1 ;; esac
    }

    if want pdf; then
        if [ "$HAVE_PDF" -eq 1 ]; then
            ( cd "$DIST_DIR" && pdflatex -interaction=nonstopmode -halt-on-error \
                -jobname="$stem" "$stem.tex" >/dev/null )
            cp "$DIST_DIR/$stem.pdf" "$out_dir/$basename.pdf"
            info "pdf  -> final/$variant/$basename.pdf ($(page_count "$DIST_DIR/$stem.log") pages)"
        else
            skipped_pdf=1
        fi
    fi

    if want docx; then
        if [ -n "$HAVE_DOCX" ]; then
            make_docx "$txt" "$out_dir/$basename.docx"
            info "docx -> final/$variant/$basename.docx"
        else
            skipped_docx=1
        fi
    fi

    # The plain-text rendering is a useful ATS-paste artifact in its own right.
    cp "$txt" "$out_dir/$basename.txt"
    info "txt  -> final/$variant/$basename.txt"

    built=$((built + 1))
done < <(python3 "$RENDER" plan --profile-dir "$PROFILE_DIR")

find "$DIST_DIR" -maxdepth 1 \( -name '*.aux' -o -name '*.log' -o -name '*.out' \
    -o -name '*.fls' -o -name '*.fdb_latexmk' -o -name '*.synctex.gz' \) -delete 2>/dev/null || true

[ "$built" -eq 0 ] && die "no build targets matched those filters"
[ "$skipped_pdf" -eq 1 ] && echo "warning: pdflatex not found -- PDFs skipped" >&2
[ "$skipped_docx" -eq 1 ] && echo "warning: neither textutil nor pandoc found -- DOCX skipped" >&2

echo "Done: $built document(s) built into $FINAL_DIR/"
