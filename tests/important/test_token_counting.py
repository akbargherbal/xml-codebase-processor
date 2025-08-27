import pytest
import time
import tiktoken
from xml_directory_processor import count_tokens


@pytest.mark.important
class TestTokenCounting:
    """Test token counting accuracy - Important Priority"""

    def test_token_count_exact_values(self):
        """Test token counting with exact expected values using tiktoken"""
        encoding = tiktoken.get_encoding("cl100k_base")

        test_cases = [
            ("hello world", len(encoding.encode("hello world"))),
            ("", 0),
            ("a", 1),
            (
                "def function():\n    pass",
                len(encoding.encode("def function():\n    pass")),
            ),
        ]

        for text, expected in test_cases:
            tokens = count_tokens(text)
            assert (
                tokens == expected
            ), f"Token count {tokens} != expected {expected} for text: {repr(text)}"

    def test_unicode_token_counting_exact(self):
        """Test Unicode token counting with exact values"""
        encoding = tiktoken.get_encoding("cl100k_base")

        unicode_cases = ["café", "résumé", "naïve", "🎉🎊", "Hello, 世界! 🌍"]

        for text in unicode_cases:
            expected = len(encoding.encode(text))
            tokens = count_tokens(text)
            assert (
                tokens == expected
            ), f"Unicode text '{text}' got {tokens} tokens, expected {expected}"

    @pytest.mark.slow
    def test_token_counting_large_text(self):
        """Test token counting performance and accuracy on large text"""
        large_text = "word " * 10000
        encoding = tiktoken.get_encoding("cl100k_base")
        expected = len(encoding.encode(large_text))

        start_time = time.time()
        tokens = count_tokens(large_text)
        end_time = time.time()

        assert end_time - start_time < 1.0
        assert tokens == expected

    def test_token_counting_edge_cases(self):
        """Test token counting with edge case inputs"""
        encoding = tiktoken.get_encoding("cl100k_base")

        edge_cases = ["\n\n\n", "   \t  ", "🚀" * 100, "a" * 100000]
        for case in edge_cases:
            expected = len(encoding.encode(case))
            tokens = count_tokens(case)
            assert tokens == expected, f"Edge case failed: {repr(case)}"
