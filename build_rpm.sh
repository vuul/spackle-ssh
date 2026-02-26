#!/usr/bin/env bash
#
# build_rpm.sh — Create a source tarball and build the Spackle RPM
#
# Usage: ./build_rpm.sh
# Requires: rpmbuild (dnf install rpm-build), and the project files in the current directory.
#
# Output: ~/rpmbuild/RPMS/noarch/spackle-2.0-1.<dist>.noarch.rpm
#         ~/rpmbuild/SRPMS/spackle-2.0-1.<dist>.src.rpm
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VERSION="2.0"
TARBALL="spackle-${VERSION}.tar.gz"
RPMBUILD_DIR="${HOME}/rpmbuild"

# Ensure rpmbuild directories exist
mkdir -p "${RPMBUILD_DIR}/SOURCES" "${RPMBUILD_DIR}/SPECS"

# Create source tarball with top-level dir spackle-2.0
echo "==> Creating ${TARBALL} ..."
(
  cd "$SCRIPT_DIR"
  # Include icon path even if empty so %prep can run; add files that exist
  LIST="spackle.py spackle.desktop"
  [ -d src ] && LIST="$LIST src"
  tar czf "${RPMBUILD_DIR}/SOURCES/${TARBALL}" --transform "s,^,spackle-${VERSION}/," $LIST
)

# Copy spec into SPECS
cp "$SCRIPT_DIR/spackle.spec" "${RPMBUILD_DIR}/SPECS/"

# Build RPM and SRPM
echo "==> Building RPM ..."
rpmbuild -ba "${RPMBUILD_DIR}/SPECS/spackle.spec"

echo ""
echo "==> Done. Packages:"
ls -la "${RPMBUILD_DIR}/RPMS/noarch/spackle-"*.rpm 2>/dev/null || true
ls -la "${RPMBUILD_DIR}/SRPMS/spackle-"*.rpm 2>/dev/null || true
