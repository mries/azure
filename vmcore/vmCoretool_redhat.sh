: <<'COMMENT'
MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
COMMENT

#!/bin/bash
# =============================================================================
# vmcore-analysis.sh
# Red Hat VMcore Analysis Helper
#
# Checks for required tools, installs kernel debug packages, locates vmlinux,
# and launches the crash utility against a specified vmcore.
# Must be run as root on a Red Hat compatible system with the same kernel
# version as the system that generated the vmcore.
# markusries01@gmail.com
# =============================================================================

set -euo pipefail

LOGFILE="/var/log/vmcore-analysis.log"
mkdir -p "$(dirname "$LOGFILE")"
exec > >(tee -a "$LOGFILE") 2>&1

# -----------------------------------------------------------------------------
# Colours
# -----------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()    { echo -e "${CYAN}[INFO]${NC}  $*"; }
ok()      { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; }
section() { echo -e "\n${CYAN}========== $* ==========${NC}"; }

# -----------------------------------------------------------------------------
# Root check
# -----------------------------------------------------------------------------
if [[ $EUID -ne 0 ]]; then
    error "This script must be run as root (sudo)."
    exit 1
fi

# =============================================================================
# STEP 1 — Check / install required packages
# =============================================================================
section "Step 1: Checking Required Packages"

REQUIRED_PACKAGES=("crash" "kexec-tools")
MISSING=()

for pkg in "${REQUIRED_PACKAGES[@]}"; do
    if rpm -q "$pkg" &>/dev/null; then
        ok "$pkg is installed."
    else
        warn "$pkg is NOT installed."
        MISSING+=("$pkg")
    fi
done

if [[ ${#MISSING[@]} -gt 0 ]]; then
    info "Installing missing packages: ${MISSING[*]}"
    dnf install -y "${MISSING[@]}" || {
        error "Failed to install required packages. Exiting."
        exit 1
    }
    ok "Required packages installed."
fi

# =============================================================================
# STEP 2 — Gather input: kernel version and vmcore path
# =============================================================================
section "Step 2: Gather Input"

# Kernel version
echo ""
read -rp "Enter the kernel version of the crashed system (e.g. 5.14.0-284.11.1.el9_2.x86_64): " KERNEL_VERSION
KERNEL_VERSION="${KERNEL_VERSION// /}"

if [[ -z "$KERNEL_VERSION" ]]; then
    error "Kernel version cannot be empty."
    exit 1
fi
info "Kernel version: $KERNEL_VERSION"

# VMcore path
echo ""
read -rp "Enter the full path to the vmcore file (e.g. /var/crash/2024-01-15-10:30/vmcore): " VMCORE_PATH

if [[ -z "$VMCORE_PATH" ]]; then
    error "VMcore path cannot be empty."
    exit 1
fi

if [[ ! -f "$VMCORE_PATH" ]]; then
    error "VMcore file not found at: $VMCORE_PATH"
    exit 1
fi
ok "VMcore found: $VMCORE_PATH"

# =============================================================================
# STEP 3 — Install kernel-debuginfo for the specified kernel version
# =============================================================================
section "Step 3: Installing kernel-debuginfo for $KERNEL_VERSION"

DEBUGINFO_PKG="kernel-debuginfo-${KERNEL_VERSION}"

if rpm -q "$DEBUGINFO_PKG" &>/dev/null; then
    ok "$DEBUGINFO_PKG is already installed."
else
    info "Attempting to install $DEBUGINFO_PKG from debug repositories..."

    # Try standard debug repos first, then fallback to broader search
    if dnf --enablerepo="*debug*" install -y "$DEBUGINFO_PKG" 2>/dev/null; then
        ok "$DEBUGINFO_PKG installed successfully."
    else
        warn "Standard debug repos did not find the package. Trying debuginfo-install..."
        if debuginfo-install -y "kernel-${KERNEL_VERSION}" 2>/dev/null; then
            ok "kernel-debuginfo installed via debuginfo-install."
        else
            error "Could not automatically install kernel-debuginfo for $KERNEL_VERSION."
            echo ""
            echo "  You may need to manually enable the correct repository."
            echo "  For RHEL: subscription-manager repos --enable=rhel-*-debug-rpms"
            echo "  For CentOS Stream / Rocky / Alma: enable the appropriate *-debuginfo repo"
            echo ""
            exit 1
        fi
    fi
fi

# =============================================================================
# STEP 4 — Locate vmlinux
# =============================================================================
section "Step 4: Locating vmlinux"

VMLINUX_PATH="/usr/lib/debug/lib/modules/${KERNEL_VERSION}/vmlinux"

if [[ -f "$VMLINUX_PATH" ]]; then
    ok "vmlinux found: $VMLINUX_PATH"
else
    info "Searching for vmlinux under /usr/lib/debug..."
    FOUND=$(find /usr/lib/debug -name "vmlinux" 2>/dev/null | head -1)
    if [[ -n "$FOUND" ]]; then
        warn "vmlinux not at expected path. Found at: $FOUND"
        VMLINUX_PATH="$FOUND"
    else
        error "vmlinux not found. Ensure kernel-debuginfo-${KERNEL_VERSION} is installed."
        exit 1
    fi
fi

# =============================================================================
# STEP 5 — Launch crash and run diagnostic commands
# =============================================================================
section "Step 5: Launching crash"

info "vmlinux : $VMLINUX_PATH"
info "vmcore  : $VMCORE_PATH"
echo ""
info "The following commands will run automatically inside crash:"
echo ""
echo "    sys    — System information"
echo "    uname  — Kernel version"
echo "    mod    — Loaded kernel modules"
echo "    bt     — Backtrace / panic reason"
echo "    exit"
echo ""
echo "Output is logged to: $LOGFILE"
echo ""

# Build the crash command script
CRASH_CMDS=$(cat <<'CRASH_EOF'
sys
uname
mod
bt
exit
CRASH_EOF
)

info "Running crash — this may take a moment..."
echo ""

echo "$CRASH_CMDS" | crash "$VMLINUX_PATH" "$VMCORE_PATH" || {
    error "crash exited with an error. Review output above and check $LOGFILE."
    exit 1
}

# =============================================================================
# Done
# =============================================================================
section "Analysis Complete"
ok "VMcore analysis finished. Full output saved to $LOGFILE"
echo ""
info "Next steps:"
echo "  - Review 'bt' output for the panic reason and call stack"
echo "  - Review 'mod' output for any suspicious or third-party kernel modules"
echo "  - Cross-reference 'sys' and 'uname' to confirm the correct debug symbols were used"
echo "  - For deeper analysis, re-run crash interactively:"
echo ""
echo "    crash $VMLINUX_PATH $VMCORE_PATH"
echo ""
