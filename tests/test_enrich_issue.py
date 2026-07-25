import unittest

from scripts import comment_parts


class FakeComment:
    def __init__(self, body):
        self.body = body


class FakeIssue:
    def __init__(self, bodies=None):
        self.comments = [FakeComment(body) for body in (bodies or [])]

    def create_comment(self, body):
        self.comments.append(FakeComment(body))

    def get_comments(self):
        return list(self.comments)


class MultipartCommentTests(unittest.TestCase):
    def test_split_comment_text_preserves_all_content(self):
        text = ("First paragraph.\n\n" + ("A" * 59000) + "\n" + ("B" * 59000))

        parts = comment_parts.split_comment_text(text)

        self.assertGreater(len(parts), 1)
        self.assertEqual("".join(parts), text)
        self.assertTrue(all(len(part) <= comment_parts.COMMENT_CONTENT_LIMIT for part in parts))

    def test_build_comment_parts_numbers_and_bounds_each_comment(self):
        text = "\n\n".join(f"Paragraph {index}: " + ("x" * 1000) for index in range(120))

        marker = "<!-- policy-hawk:test-current-markdown -->"
        bodies = comment_parts.build_comment_parts(
            text,
            marker,
            heading="Current Version (Markdown)",
        )

        self.assertGreater(len(bodies), 1)
        for index, body in enumerate(bodies, start=1):
            self.assertIn(f"Part {index} of {len(bodies)}", body)
            self.assertIn(
                comment_parts.COMMENT_PART_MARKER.format(part=index, total=len(bodies)),
                body,
            )
            self.assertLessEqual(len(body), comment_parts.COMMENT_LIMIT)

    def test_post_comment_parts_is_idempotent_and_resumes_missing_part(self):
        text = "\n\n".join(f"Paragraph {index}: " + ("x" * 1000) for index in range(120))
        marker = "<!-- policy-hawk:test-current-markdown -->"
        expected = comment_parts.build_comment_parts(text, marker, heading="Current")
        issue = FakeIssue()

        comment_parts.post_comment_parts(issue, text, marker, heading="Current")
        comment_parts.post_comment_parts(issue, text, marker, heading="Current")
        self.assertEqual([comment.body for comment in issue.comments], expected)

        issue.comments.pop(1)
        comment_parts.post_comment_parts(issue, text, marker, heading="Current")
        self.assertEqual(len(issue.comments), len(expected))
        self.assertCountEqual([comment.body for comment in issue.comments], expected)

    def test_diff_parts_each_have_complete_markdown_wrappers(self):
        text = "\n".join("+ changed line " + ("x" * 1000) for _ in range(120))

        bodies = comment_parts.build_comment_parts(
            text,
            "<!-- policy-hawk:test-diff -->",
            heading="Diff",
            fenced_language="diff",
            collapsible=True,
        )

        self.assertGreater(len(bodies), 1)
        for body in bodies:
            self.assertEqual(body.count("```diff"), 1)
            self.assertEqual(body.count("```"), 2)
            self.assertEqual(body.count("<details>"), 1)
            self.assertEqual(body.count("</details>"), 1)

    def test_legacy_truncated_comment_is_repaired_but_complete_one_is_not(self):
        marker = "<!-- policy-hawk:test-legacy -->"
        text = "Complete replacement text."

        truncated_issue = FakeIssue([f"{marker}\nold text\n\n...(truncated)"])
        comment_parts.post_comment_parts(truncated_issue, text, marker, heading="Current")
        self.assertEqual(len(truncated_issue.comments), 2)
        self.assertIn(text, truncated_issue.comments[-1].body)

        complete_issue = FakeIssue([f"{marker}\ncomplete legacy text"])
        comment_parts.post_comment_parts(complete_issue, text, marker, heading="Current")
        self.assertEqual(len(complete_issue.comments), 1)


if __name__ == "__main__":
    unittest.main()
