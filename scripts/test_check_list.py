"""The list check, run as a pull request would run it: on a copy of the repository with one commit as
the base and the request's changes on top. Run with: python3 -m unittest discover -s scripts"""
import json
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "check_list.py"
LOGO_BASE = "https://raw.githubusercontent.com/ninemm-pro/app-tokens/main/token-logo/"
LISTED = "0x15D38573d2feeb82e7ad5187aB8c1D52810B1f07"
NEW = "0x0F382a88aCDAAAd1599601a387c86861B43a893f"


def png(width, height):
    """A blank PNG of this size: enough for the check, which reads only its header and length."""
    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))
    rows = b"".join(b"\x00" + b"\x00" * width * 3 for _ in range(height))
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b"")


def entry(address, symbol, logo=True):
    return {"chainId": 369, "address": address, "name": f"{symbol} token", "symbol": symbol, "decimals": 18, "logoURI": f"{LOGO_BASE}{address}.png" if logo else "https://example.com/x.png"}


class ListCheck(unittest.TestCase):
    def setUp(self):
        self.repo = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.repo)
        (self.repo / "scripts").mkdir()
        shutil.copy(SCRIPT, self.repo / "scripts" / "check_list.py")
        (self.repo / "token-logo").mkdir()
        # The base already holds an entry whose logo was never added, as the copied list does.
        self.write_list([entry(LISTED, "USDC", logo=False)])
        self.git("init", "-q", "-b", "main")
        self.git("add", ".")
        self.git("-c", "user.name=test", "-c", "user.email=test@example.com", "commit", "-q", "-m", "base")

    def git(self, *args):
        subprocess.run(["git", *args], cwd=self.repo, check=True, timeout=60)

    def write_list(self, tokens):
        (self.repo / "9mm-tokenlist.json").write_text(json.dumps({"name": "9mm", "tokens": tokens}, indent=2))

    def add_logo(self, address, data):
        (self.repo / "token-logo" / f"{address}.png").write_bytes(data)

    def check(self):
        run = subprocess.run([sys.executable, "scripts/check_list.py", "main"], cwd=self.repo, capture_output=True, text=True, timeout=60)
        return run.returncode, run.stdout

    def test_a_complete_request_passes_though_an_older_entry_has_no_logo(self):
        self.write_list([entry(LISTED, "USDC", logo=False), entry(NEW, "HB-4000")])
        self.add_logo(NEW, png(128, 128))
        self.assertEqual(self.check(), (0, "The lists pass.\n"))

    def test_a_request_with_no_logo_at_all_passes(self):
        # The owner may list a token before its project sends a logo (12 October 2026); it shows a lettered badge.
        bare = {key: value for key, value in entry(NEW, "HB-4000").items() if key != "logoURI"}
        self.write_list([entry(LISTED, "USDC", logo=False), bare])
        self.assertEqual(self.check(), (0, "The lists pass.\n"))

    def test_a_request_without_its_logo_file_fails(self):
        self.write_list([entry(LISTED, "USDC", logo=False), entry(NEW, "HB-4000")])
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertIn("logo file token-logo/", out)

    def test_a_logo_that_is_too_small_or_not_square_fails(self):
        self.write_list([entry(LISTED, "USDC", logo=False), entry(NEW, "HB-4000")])
        self.add_logo(NEW, png(64, 64))
        self.assertIn("at least 128x128", self.check()[1])
        self.add_logo(NEW, png(200, 128))
        self.assertIn("must be square", self.check()[1])

    def test_a_logo_that_is_not_a_png_fails(self):
        self.write_list([entry(LISTED, "USDC", logo=False), entry(NEW, "HB-4000")])
        self.add_logo(NEW, b"\xff\xd8\xff\xe0 a jpeg")
        self.assertIn("not a PNG", self.check()[1])

    def test_an_address_already_listed_fails(self):
        self.write_list([entry(LISTED, "USDC", logo=False), entry(LISTED.lower(), "USDC2")])
        self.add_logo(LISTED.lower(), png(128, 128))
        self.assertIn("already on the list", self.check()[1])

    def test_another_chain_or_a_bad_address_fails(self):
        other = {**entry(NEW, "HB-4000"), "chainId": 1}
        self.write_list([entry(LISTED, "USDC", logo=False), other, entry("0x1234", "BAD")])
        out = self.check()[1]
        self.assertIn("chainId must be 369", out)
        self.assertIn("address must be 0x and 40 hex digits", out)

    def test_a_list_that_is_not_json_fails(self):
        (self.repo / "9mm-tokenlist.json").write_text('{"tokens": [')
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertIn("not a valid token list", out)


if __name__ == "__main__":
    unittest.main()
