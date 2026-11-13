# syntax=docker/dockerfile:1.7
#
# TinCan server image with a dev toolchain ready on first launch for the
# space exec sandbox / terminal: Homebrew (Linuxbrew), Node LTS (npm, npx),
# Rust (rustup, cargo, rustc), build-essential, git, curl, wget, unzip,
# pkg-config, libssl-dev, python3-pip and python3-venv.
#
# Xcode / iOS tooling (xcodebuild, simctl, Swift-for-iOS) only runs on macOS
# and is intentionally not attempted here.

ARG PYTHON_IMAGE=python:3.11-slim-trixie
ARG NODE_IMAGE=node:26.13.1-trixie-slim
ARG RUST_IMAGE=rust:1.100.0-slim-trixie
ARG HOMEBREW_VERSION=7.0.13

# ---- toolchain sources (cached as separate layers) --------------------------
FROM ${NODE_IMAGE} AS node
FROM ${RUST_IMAGE} AS rust

# ---- runtime image -----------------------------------------------------------
FROM ${PYTHON_IMAGE}
ARG HOMEBREW_VERSION

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    RUSTUP_HOME=/usr/local/rustup \
    CARGO_HOME=/usr/local/cargo \
    HOMEBREW_PREFIX=/home/linuxbrew/.linuxbrew \
    HOMEBREW_CELLAR=/home/linuxbrew/.linuxbrew/Cellar \
    HOMEBREW_REPOSITORY=/home/linuxbrew/.linuxbrew/Homebrew \
    HOMEBREW_NO_AUTO_UPDATE=1 \
    HOMEBREW_NO_ANALYTICS=1 \
    HOMEBREW_NO_ENV_HINTS=1 \
    HOMEBREW_NO_INSTALL_CLEANUP=1

# System build tools (one cached layer; apt lists removed afterwards).
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential git curl wget unzip pkg-config libssl-dev \
      python3-pip python3-venv ca-certificates procps file locales \
 && rm -rf /var/lib/apt/lists/*

# Node LTS (node, npm, npx) from the official image. (Node 25+ no longer
# bundles corepack; `npm i -g corepack` if pnpm/yarn shims are needed.)
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -sf ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
 && ln -sf ../lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx

# Rust via rustup (cargo, rustc, rustup) from the official image.
COPY --from=rust /usr/local/rustup /usr/local/rustup
COPY --from=rust /usr/local/cargo /usr/local/cargo
RUN chmod -R a+rX /usr/local/rustup /usr/local/cargo

# Homebrew on Linux, owned by a non-root "linuxbrew" user (pinned tag,
# shallow clone). `brew config` runs once here so portable Ruby is already
# vendored and `brew` works offline on first launch.
RUN useradd --create-home --shell /bin/bash linuxbrew \
 && mkdir -p /home/linuxbrew/.linuxbrew/bin \
 && git clone --depth 1 --branch "${HOMEBREW_VERSION}" https://github.com/Homebrew/brew /home/linuxbrew/.linuxbrew/Homebrew \
 && ln -s ../Homebrew/bin/brew /home/linuxbrew/.linuxbrew/bin/brew \
 && chown -R linuxbrew:linuxbrew /home/linuxbrew \
 && su linuxbrew -c "/home/linuxbrew/.linuxbrew/bin/brew --version && /home/linuxbrew/.linuxbrew/bin/brew config >/dev/null" \
 && rm -rf /home/linuxbrew/.cache/Homebrew

# Homebrew refuses to run as root outside some CI/containers. The server runs
# as root (Railway volumes are root-owned), so this shim drops to the
# linuxbrew user when invoked as root and otherwise calls brew directly.
COPY scripts/brew-shim.sh /usr/local/bin/brew
RUN chmod 0755 /usr/local/bin/brew

ENV PATH=/usr/local/bin:/usr/local/cargo/bin:/home/linuxbrew/.linuxbrew/bin:/home/linuxbrew/.linuxbrew/sbin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin

WORKDIR /app

RUN pip install --no-cache-dir pynacl cryptography "webauthn==3.0.1"

COPY . .

# Fail the build early if any tool is missing.
RUN node -v && npm -v && npx -v && cargo --version && rustc --version \
 && brew --version && git --version && python3 -m venv --help >/dev/null

ENV PORT=8080
EXPOSE 8080

CMD ["python3", "server.py"]
