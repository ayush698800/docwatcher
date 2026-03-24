import unittest

from docwatcher.doc_scanner import chunk_markdown


class ChunkMarkdownTests(unittest.TestCase):
    def test_splits_sections_and_preserves_headings(self):
        content = "# Intro\nHello\n## Usage\nRun this\n"

        chunks = chunk_markdown(content, "README.md")

        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[0].heading, "Intro")
        self.assertEqual(chunks[0].content, "Hello")
        self.assertEqual(chunks[1].heading, "Usage")
        self.assertEqual(chunks[1].content, "Run this")


if __name__ == "__main__":
    unittest.main()
