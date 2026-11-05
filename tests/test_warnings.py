import subprocess
import sys


def test_the_pkg_resources_warning_is_kept_out_of_the_log():
    code = "import saxscribe, warnings; warnings.warn('pkg_resources is deprecated as an API.', UserWarning)"
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    assert "pkg_resources" not in out.stderr
