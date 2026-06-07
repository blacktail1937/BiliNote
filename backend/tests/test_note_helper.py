import importlib.util
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "app" / "utils" / "note_helper.py"
spec = importlib.util.spec_from_file_location("note_helper", MODULE_PATH)
if spec is None or spec.loader is None:
    raise ImportError("note_helper module spec not found")
note_helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(note_helper)


class TestNoteHelper(unittest.TestCase):
    def test_prepend_source_link_adds_header_at_top(self):
        source_url = "https://www.bilibili.com/video/BV1xx411c7mD"
        markdown = "## 标题\n\n内容"

        result = note_helper.prepend_source_link(markdown, source_url)

        self.assertTrue(result.startswith(f"> 来源链接：{source_url}\n\n"))
        self.assertIn("## 标题", result)

    def test_prepend_source_link_does_not_duplicate_when_header_exists(self):
        source_url = "https://www.youtube.com/watch?v=abc123"
        markdown = f"> 来源链接：{source_url}\n\n## 标题\n\n内容"

        result = note_helper.prepend_source_link(markdown, source_url)

        self.assertEqual(result, markdown)


    # --- replace_content_markers tests ---

    def test_replace_normal_mmss_with_brackets(self):
        result = note_helper.replace_content_markers(
            "细节见 *Content-[06:20] 处",
            "BV1xx411c7mD", "bilibili"
        )
        self.assertIn("[原片 @ 06:20]", result)
        self.assertIn("t=380", result)

    def test_replace_normal_mmss_without_brackets(self):
        result = note_helper.replace_content_markers(
            "细节见 Content-06:20 处",
            "BV1xx411c7mD", "bilibili"
        )
        self.assertIn("[原片 @ 06:20]", result)
        self.assertIn("t=380", result)

    def test_replace_normalizes_overflow_minutes(self):
        result = note_helper.replace_content_markers(
            "片段 *Content-[62:52] 处",
            "BV1xx411c7mD", "bilibili"
        )
        self.assertIn("[原片 @ 1:02:52]", result)
        self.assertIn("t=3772", result)

    def test_replace_normalizes_120_minutes(self):
        result = note_helper.replace_content_markers(
            "*Content-[120:00]",
            "BV1xx411c7mD", "bilibili"
        )
        self.assertIn("[原片 @ 2:00:00]", result)
        self.assertIn("t=7200", result)

    def test_replace_normalizes_overflow_minutes_no_brackets(self):
        result = note_helper.replace_content_markers(
            "Content-62:52",
            "BV1xx411c7mD", "bilibili"
        )
        self.assertIn("[原片 @ 1:02:52]", result)
        self.assertIn("t=3772", result)

    def test_replace_preserves_explicit_hours(self):
        result = note_helper.replace_content_markers(
            "*Content-[1:02:52]",
            "BV1xx411c7mD", "bilibili"
        )
        self.assertIn("[原片 @ 1:02:52]", result)
        self.assertIn("t=3772", result)

    def test_replace_explicit_hours_no_brackets(self):
        result = note_helper.replace_content_markers(
            "Content-1:02:52",
            "BV1xx411c7mD", "bilibili"
        )
        self.assertIn("[原片 @ 1:02:52]", result)
        self.assertIn("t=3772", result)

    def test_replace_zero_time(self):
        result = note_helper.replace_content_markers(
            "Content-[00:00]",
            "BV1xx411c7mD", "bilibili"
        )
        self.assertIn("[原片 @ 00:00]", result)
        self.assertIn("t=0", result)

    def test_replace_youtube_platform(self):
        result = note_helper.replace_content_markers(
            "Content-[06:20]",
            "abc123xyz", "youtube"
        )
        self.assertIn("[原片 @ 06:20]", result)
        self.assertIn("youtube.com/watch?v=abc123xyz", result)
        self.assertIn("t=380s", result)

    def test_replace_youtube_overflow_minutes(self):
        result = note_helper.replace_content_markers(
            "Content-[62:52]",
            "abc123xyz", "youtube"
        )
        self.assertIn("[原片 @ 1:02:52]", result)
        self.assertIn("t=3772s", result)

    def test_replace_douyin_platform(self):
        result = note_helper.replace_content_markers(
            "Content-[06:20]",
            "123456789", "douyin"
        )
        self.assertIn("[原片 @ 06:20]", result)
        self.assertIn("douyin.com/video/123456789", result)
        self.assertNotIn("t=", result)

    def test_replace_douyin_overflow_minutes(self):
        result = note_helper.replace_content_markers(
            "Content-[62:52]",
            "123456789", "douyin"
        )
        self.assertIn("[原片 @ 1:02:52]", result)

    def test_replace_unknown_platform(self):
        result = note_helper.replace_content_markers(
            "Content-[06:20]",
            "some_id", "bilibili"
        )
        self.assertIn("[原片 @ 06:20]", result)

    def test_replace_bilibili_multipart_video_id(self):
        result = note_helper.replace_content_markers(
            "Content-[06:20]",
            "BV1xx411c7mD_p2", "bilibili"
        )
        self.assertIn("[原片 @ 06:20]", result)
        self.assertIn("?p=2&t=380", result)
        self.assertNotIn("/?t=", result)

    def test_replace_bilibili_multipart_with_overflow(self):
        result = note_helper.replace_content_markers(
            "Content-[62:52]",
            "BV1xx411c7mD_p3", "bilibili"
        )
        self.assertIn("[原片 @ 1:02:52]", result)
        self.assertIn("?p=3&t=3772", result)

    def test_replace_multiple_markers_in_one_text(self):
        result = note_helper.replace_content_markers(
            "开头 Content-[00:00]，中间 Content-[06:20]，结尾 Content-[62:52]",
            "BV1xx411c7mD", "bilibili"
        )
        self.assertIn("[原片 @ 00:00]", result)
        self.assertIn("[原片 @ 06:20]", result)
        self.assertIn("[原片 @ 1:02:52]", result)
        self.assertEqual(result.count("[原片 @"), 3)

    def test_replace_no_marker_returns_unchanged(self):
        text = "这是一段普通文本，没有时间标记"
        result = note_helper.replace_content_markers(text, "BVxxx")
        self.assertEqual(result, text)

    def test_replace_asterisk_prefix_handled(self):
        result = note_helper.replace_content_markers(
            "*Content-[06:20]* 和 Content-[06:20]",
            "BV1xx411c7mD", "bilibili"
        )
        self.assertEqual(result.count("[原片 @ 06:20]"), 2)


    # --- prepend_toc tests ---

    def test_toc_generates_from_headings(self):
        md = "## 简介\n\n内容\n\n## 方法\n\n步骤\n\n## 总结"
        result = note_helper.prepend_toc(md)
        self.assertIn("## 目录", result)
        self.assertIn("[简介](#简介)", result)
        self.assertIn("[方法](#方法)", result)
        self.assertIn("[总结](#总结)", result)
        self.assertTrue(result.startswith("## 目录"))

    def test_toc_less_than_two_headings_skipped(self):
        md = "## 简介\n\n内容"
        result = note_helper.prepend_toc(md)
        self.assertEqual(result, md)

    def test_toc_no_headings_skipped(self):
        md = "纯文本内容"
        result = note_helper.prepend_toc(md)
        self.assertEqual(result, md)

    def test_toc_empty_string(self):
        self.assertEqual(note_helper.prepend_toc(""), "")

    def test_toc_strips_content_markers_from_display(self):
        md = "## AI 发展史 *Content-[01:23]\n\n内容\n\n## AI 未来 *Content-[05:00]"
        result = note_helper.prepend_toc(md)
        self.assertIn("[AI 发展史]", result)
        self.assertNotIn("*Content-", result.split("---")[0])
        self.assertIn("[AI 未来]", result)

    def test_toc_slug_matches_rehype_slug_format(self):
        md = "## Hello World\n\n内容\n\n## AI 风口的舆论炒作与现实"
        result = note_helper.prepend_toc(md)
        self.assertIn("(#hello-world)", result)
        self.assertIn("(#ai-风口的舆论炒作与现实)", result)

    def test_toc_deduplicates_identical_headings(self):
        md = "## 结果\n\n内容\n\n## 结果\n\n更多"
        result = note_helper.prepend_toc(md)
        self.assertIn("(#结果)", result)
        self.assertIn("(#结果-1)", result)


if __name__ == "__main__":
    unittest.main()
