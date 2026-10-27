#!/usr/bin/env bash
# JM Comment: Install and verify the local tools required for the Ray AI Platform assignment.
#
# Supported OS: Ubuntu and Debian, amd64/x86_64 or arm64/aarch64.
# Installs: Git, Python 3/pip/venv, build tools, Docker Engine/Buildx/Compose,
# AWS CLI v2, Terraform, kubectl, Helm, jq, curl, unzip and make.
#
# Run:
#   chmod +x install-prerequisites-linux.sh
#   ./install-prerequisites-linux.sh
#
# Optional:
#   KUBECTL_VERSION=v1.34.0 ./install-prerequisites-linux.sh
#   ADD_USER_TO_DOCKER_GROUP=1 ./install-prerequisites-linux.sh
#
# Notes:
# - Run as a normal user with sudo privileges, not as root.
# - Docker group membership grants root-equivalent access; it is opt-in.
# - This installs local tools only; it does not provision AWS resources or EKS.
# - Review this script before running it on a work/production machine.

set -Eeuo pipefail
export DEBIAN_FRONTEND=noninteractive

log()  { printf '\n[INFO] %s\n' "$*"; }
warn() { printf '\n[WARN] %s\n' "$*" >&2; }
die()  { printf '\n[ERROR] %s\n' "$*" >&2; exit 1; }
trap 'rc=$?; echo "[ERROR] Command failed (exit ${rc}) at line ${LINENO}: ${BASH_COMMAND}" >&2; exit "$rc"' ERR

[[ "${EUID}" -ne 0 ]] || die "Do not run as root. Run as your normal user; the script uses sudo."
command -v sudo >/dev/null 2>&1 || die "sudo is required."
sudo -v
[[ -r /etc/os-release ]] || die "Cannot identify Linux distribution."
# shellcheck disable=SC1091
source /etc/os-release

OS_ID="${ID:-unknown}"
OS_VERSION="${VERSION_ID:-unknown}"
ARCH="$(dpkg --print-architecture 2>/dev/null || true)"
[[ -n "$ARCH" ]] || die "Could not detect package architecture."

case "$OS_ID" in
  ubuntu)
    REPO_OS="ubuntu"
    REPO_CODENAME="${UBUNTU_CODENAME:-${VERSION_CODENAME:-}}"
    ;;
  debian)
    REPO_OS="debian"
    REPO_CODENAME="${VERSION_CODENAME:-}"
    ;;
  *)
    die "Unsupported distribution: ${PRETTY_NAME:-$OS_ID}. This script supports Ubuntu/Debian only. Do not use their repositories on Fedora, RHEL, Amazon Linux, Kali, Mint, or other derivatives."
    ;;
esac

case "$ARCH" in
  amd64)
    AWSCLI_ARCH="x86_64"; KUBECTL_ARCH="amd64"; HELM_ARCH="amd64"
    ;;
  arm64)
    AWSCLI_ARCH="aarch64"; KUBECTL_ARCH="arm64"; HELM_ARCH="arm64"
    ;;
  *)
    die "Unsupported architecture ${ARCH}; supported: amd64 and arm64."
    ;;
esac
[[ -n "$REPO_CODENAME" ]] || die "Could not determine distribution codename."

log "Detected ${PRETTY_NAME:-$OS_ID $OS_VERSION}, architecture=${ARCH}, codename=${REPO_CODENAME}"
log "Installing base packages."
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg unzip jq git make \
  python3 python3-pip python3-venv python3-dev build-essential coreutils

# HashiCorp's official APT repository for Terraform.
log "Configuring HashiCorp's official APT repository."
sudo install -d -m 0755 /usr/share/keyrings
curl -fsSL https://apt.releases.hashicorp.com/gpg \
  | sudo gpg --dearmor --yes -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
sudo chmod 0644 /usr/share/keyrings/hashicorp-archive-keyring.gpg
printf 'deb [arch=%s signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com %s main\n' \
  "$ARCH" "$REPO_CODENAME" | sudo tee /etc/apt/sources.list.d/hashicorp.list >/dev/null

# Docker's official APT repository using the current deb822 .sources format.
log "Configuring Docker's official APT repository."
if [[ -f /etc/apt/sources.list.d/docker.list ]] \
  && grep -q 'download.docker.com/linux/' /etc/apt/sources.list.d/docker.list; then
  sudo rm -f /etc/apt/sources.list.d/docker.list
fi
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL "https://download.docker.com/linux/${REPO_OS}/gpg" -o /tmp/docker-archive-keyring.asc
sudo install -m 0644 /tmp/docker-archive-keyring.asc /etc/apt/keyrings/docker.asc
rm -f /tmp/docker-archive-keyring.asc
sudo tee /etc/apt/sources.list.d/docker.sources >/dev/null <<EOF
Types: deb
URIs: https://download.docker.com/linux/${REPO_OS}
Suites: ${REPO_CODENAME}
Components: stable
Architectures: ${ARCH}
Signed-By: /etc/apt/keyrings/docker.asc
EOF

# Helm's Debian repository. Verify the published signing-key fingerprint before trusting it.
log "Configuring Helm's APT repository."
HELM_KEY_TMP="$(mktemp)"
curl -fsSL https://packages.buildkite.com/helm-linux/helm-debian/gpgkey -o "$HELM_KEY_TMP"
HELM_KEY_FINGERPRINT="$(gpg --show-keys --with-colons "$HELM_KEY_TMP" \
  | awk -F: '$1 == "fpr" { print $10; exit }')"
EXPECTED_HELM_FINGERPRINT="DDF78C3E6EBB2D2CC223C95C62BA89D07698DBC6"
if [[ "$HELM_KEY_FINGERPRINT" != "$EXPECTED_HELM_FINGERPRINT" ]]; then
  rm -f "$HELM_KEY_TMP"
  die "Helm repository key fingerprint mismatch; refusing to trust the repository."
fi
gpg --dearmor < "$HELM_KEY_TMP" > /tmp/helm-archive-keyring.gpg
sudo install -m 0644 /tmp/helm-archive-keyring.gpg /usr/share/keyrings/helm.gpg
rm -f "$HELM_KEY_TMP" /tmp/helm-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/helm.gpg] https://packages.buildkite.com/helm-linux/helm-debian/any/ any main" \
  | sudo tee /etc/apt/sources.list.d/helm-stable-debian.list >/dev/null

log "Refreshing package metadata."
sudo apt-get update

# Avoid silently removing existing container runtimes. If conflicts are present,
# ask the operator before removing packages; Docker data directories are not deleted.
CONFLICTS=()
for pkg in docker.io docker-compose docker-compose-v2 docker-doc docker-buildx podman-docker containerd runc; do
  if dpkg-query -W -f='${Status}' "$pkg" 2>/dev/null | grep -q 'install ok installed'; then
    CONFLICTS+=("$pkg")
  fi
done
if (( ${#CONFLICTS[@]} > 0 )); then
  printf '\nPotential Docker CE conflicts found: %s\n' "${CONFLICTS[*]}" >&2
  warn "Removing packages may affect existing containers. The script does not intentionally delete Docker images or volumes."
  [[ -t 0 ]] || die "Non-interactive execution with conflicting packages. Review them manually and rerun."
  read -r -p "Remove these packages and continue? [y/N] " ANSWER
  case "$ANSWER" in
    y|Y|yes|YES) sudo apt-get remove -y "${CONFLICTS[@]}" ;;
    *) die "Cancelled to avoid changing the existing container runtime." ;;
  esac
fi

log "Installing Terraform, Docker Engine, Buildx, Compose plugin and Helm."
sudo apt-get install -y terraform docker-ce docker-ce-cli containerd.io \
  docker-buildx-plugin docker-compose-plugin helm

log "Enabling and starting Docker."
sudo systemctl enable --now docker

TMP_DIR="$(mktemp -d)"
cleanup() { rm -rf "$TMP_DIR"; }
trap cleanup EXIT

# AWS CLI v2 from AWS's official Linux installer.
log "Installing AWS CLI v2."
curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-${AWSCLI_ARCH}.zip" \
  -o "${TMP_DIR}/awscliv2.zip"
unzip -q "${TMP_DIR}/awscliv2.zip" -d "$TMP_DIR"
if [[ -x /usr/local/aws-cli/v2/current/bin/aws ]]; then
  sudo "${TMP_DIR}/aws/install" --update
elif command -v aws >/dev/null 2>&1; then
  warn "An aws command already exists; attempting to update the standard AWS CLI installation."
  sudo "${TMP_DIR}/aws/install" --update
else
  sudo "${TMP_DIR}/aws/install"
fi

# kubectl: stable by default, checksum-verified; override to match chosen EKS version.
if [[ -z "${KUBECTL_VERSION:-}" ]]; then
  KUBECTL_VERSION="$(curl -fsSL https://dl.k8s.io/release/stable.txt)"
fi
[[ "$KUBECTL_VERSION" =~ ^v[0-9]+\.[0-9]+\.[0-9]+([+-][a-zA-Z0-9.-]+)?$ ]] \
  || die "Invalid KUBECTL_VERSION '${KUBECTL_VERSION}'. Example: v1.34.0"
log "Installing kubectl ${KUBECTL_VERSION}."
curl -fsSL "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/${KUBECTL_ARCH}/kubectl" \
  -o "${TMP_DIR}/kubectl"
curl -fsSL "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/${KUBECTL_ARCH}/kubectl.sha256" \
  -o "${TMP_DIR}/kubectl.sha256"
printf '%s  %s\n' "$(cat "${TMP_DIR}/kubectl.sha256")" "${TMP_DIR}/kubectl" \
  | sha256sum --check --status || die "kubectl checksum validation failed."
sudo install -o root -g root -m 0755 "${TMP_DIR}/kubectl" /usr/local/bin/kubectl

# Optional only: docker group access is effectively root access.
if [[ "${ADD_USER_TO_DOCKER_GROUP:-0}" == "1" ]]; then
  warn "Adding ${USER} to docker group grants root-equivalent access."
  sudo groupadd -f docker
  sudo usermod -aG docker "$USER"
  warn "Log out and back in before running Docker without sudo."
fi

log "Verifying all required commands and Docker service."
for cmd in git python3 pip3 terraform docker aws kubectl helm jq make; do
  command -v "$cmd" >/dev/null 2>&1 || die "Required command missing after installation: ${cmd}"
done
sudo systemctl is-active --quiet docker || die "Docker service is not active."

printf '\n%-20s %s\n' "OS:" "${PRETTY_NAME:-$OS_ID $OS_VERSION}"
printf '%-20s %s\n' "Git:" "$(git --version)"
printf '%-20s %s\n' "Python:" "$(python3 --version)"
printf '%-20s %s\n' "pip:" "$(python3 -m pip --version)"
printf '%-20s %s\n' "Terraform:" "$(terraform version | head -n 1)"
printf '%-20s %s\n' "Docker:" "$(docker --version)"
printf '%-20s %s\n' "Compose:" "$(docker compose version)"
printf '%-20s %s\n' "Buildx:" "$(docker buildx version)"
printf '%-20s %s\n' "AWS CLI:" "$(aws --version 2>&1)"
printf '%-20s %s\n' "kubectl:" "$(kubectl version --client -o yaml | sed -n 's/^  gitVersion: //p' | head -n 1)"
printf '%-20s %s\n' "Helm:" "$(helm version --short)"
printf '%-20s %s\n' "jq:" "$(jq --version)"
printf '%-20s %s\n' "make:" "$(make --version | head -n 1)"

log "Running Docker smoke test. This may download the small hello-world image."
sudo docker run --rm hello-world

cat <<'EOF'

SUCCESS: Required local tools installed and basic checks passed.

