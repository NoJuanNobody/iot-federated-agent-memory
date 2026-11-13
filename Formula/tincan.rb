class Tincan < Formula
  desc "TinCan 2.2 Zero-Account Ed25519/X25519 Blind Relay CLI, WebRTC Media & Mesh OS"
  homepage "https://iot-federated-agent-memory-production.up.railway.app/mesh"
  url "https://iot-federated-agent-memory-production.up.railway.app/install.sh"
  version "2.2.0"
  license "MIT"

  depends_on "python@3.13"

  def install
    bin.install "install.sh" => "tincan-bootstrap"
    chmod 0755, bin/"tincan-bootstrap"
    (bin/"tincan").write <<~EOS
      #!/bin/bash
      if [ ! -x "$HOME/.local/bin/tincan" ]; then
        TINCAN_RELAY="https://iot-federated-agent-memory-production.up.railway.app" "#{bin}/tincan-bootstrap"
      fi
      exec "$HOME/.local/bin/tincan" "$@"
    EOS
    chmod 0755, bin/"tincan"
  end

  def caveats
    <<~EOS
      TinCan 2.2 CLI is linked to:
        https://iot-federated-agent-memory-production.up.railway.app

      Quickstart:
        tincan whoami
        tincan start
        tincan brew list
    EOS
  end

  test do
    assert_predicate bin/"tincan", :exist?
  end
end
