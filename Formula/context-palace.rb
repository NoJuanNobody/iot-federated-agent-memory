class ContextPalace < Formula
  desc "Federated SQLite WAL Context Lake, Bitemporal Belief Revision & Textual TUI Memory Palace"
  homepage "https://github.com/NoJuanNobody/context-palace"
  url "https://github.com/NoJuanNobody/context-palace/archive/refs/heads/main.tar.gz"
  version "2.0.0"
  license "MIT"

  depends_on "python@3.13"
  depends_on "sqlite"

  def install
    libexec.install Dir["*"]
    (bin/"context-palace").write <<~EOS
      #!/bin/bash
      export PYTHONPATH="#{libexec}:$PYTHONPATH"
      exec "#{Formula["python@3.13"].opt_bin}/python3" -m context_palace.cli "$@"
    EOS
    chmod 0755, bin/"context-palace"
  end

  test do
    assert_match "context-palace", shell_output("#{bin}/context-palace --help")
  end
end
