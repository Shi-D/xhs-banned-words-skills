"""运行：python3 -m unittest discover tests"""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / "tools" / "xhs_check.py"
WORDLISTS = ROOT / "wordlists"


def check(text, *args):
    out = subprocess.run(
        [sys.executable, str(CHECKER), "--wordlist-dir", str(WORDLISTS), "--format", "json", "--text", text, *args],
        capture_output=True, text=True, encoding="utf-8",
    )
    return [h["matched"] for h in json.loads(out.stdout)["hits"]], out


class CheckerTest(unittest.TestCase):
    def test_extreme_words(self):
        hits, _ = check("这是全网第一的面霜，最好用")
        self.assertIn("全网第一", hits)
        self.assertIn("最好", hits)
        self.assertNotIn("第一", hits)  # 被更长的“全网第一”覆盖

    def test_exceptions(self):
        hits, _ = check("第一次用，最近很喜欢，最好别熬夜")
        self.assertEqual(hits, [])

    def test_split_variants(self):
        hits, _ = check("有问题加微 信，或者 v·x 找我，绿泡泡也行")
        self.assertTrue(any("微" in h for h in hits))
        self.assertTrue(any(h.lower().startswith("v") for h in hits))
        self.assertIn("绿泡泡", hits)

    def test_fullwidth(self):
        hits, _ = check("ＶＸ联系，１００％有效")
        self.assertTrue(hits)

    def test_phone_number(self):
        hits, _ = check("电话13812345678")
        self.assertIn("13812345678", hits)

    def test_industry_filter(self):
        hits, _ = check("年化收益8%，稳赚不赔", "--industry", "beauty")
        self.assertNotIn("年化收益8%", hits)
        hits, _ = check("年化收益8%，稳赚不赔", "--industry", "finance")
        self.assertIn("年化收益8%", hits)

    def test_exit_code(self):
        _, out = check("保证见效")
        self.assertEqual(out.returncode, 1)
        _, out = check("今天天气不错")
        self.assertEqual(out.returncode, 0)

    def test_all_wordlists_parse(self):
        out = subprocess.run([sys.executable, str(CHECKER), "--wordlist-dir", str(WORDLISTS), "--list-industries"],
                             capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(out.stderr, "")  # 无无效正则警告
        self.assertEqual(len(out.stdout.strip().splitlines()), len(list(WORDLISTS.glob("*.txt"))))

    def test_industry_examples_clean_after_rewrite(self):
        sys.path.insert(0, str(ROOT / "tools"))
        from build import INDUSTRIES
        for key, cfg in INDUSTRIES.items():
            before, after = cfg["example"]
            with self.subTest(industry=key):
                self.assertTrue(check(before, "--industry", key)[0])
                self.assertEqual(check(after, "--industry", key)[0], [])


if __name__ == "__main__":
    unittest.main()
