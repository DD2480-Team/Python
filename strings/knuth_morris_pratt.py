from __future__ import annotations

import doctest


def kmp(pattern: str, text: str) -> bool:
    """
    The Knuth-Morris-Pratt Algorithm for finding a pattern within a piece of text
    with complexity O(n + m)

    1) Preprocess pattern to identify any suffixes that are identical to prefixes

        This tells us where to continue from if we get a mismatch between a character
        in our pattern and the text.

    2) Step through the text one character at a time and compare it to a character in
        the pattern updating our location within the pattern if necessary
    >>> pattern = "abc1abc12"
    >>> text1 = "alskfjaldsabc1abc1abc12k23adsfabcabc"
    >>> print(kmp(pattern, text1))
    True
    >>> text2 = "alskfjaldsk23adsfabcabc"
    >>> print(kmp(pattern, text2))
    False
    >>> pattern = "ABABX"
    >>> text = "ABABZABABYABABX"
    >>> print(kmp(pattern, text))
    True
    >>> pattern = "AAAB"
    >>> text = "ABAAAAAB"
    >>> print(kmp(pattern, text))
    True
    >>> pattern = "abcdabcy"
    >>> text = "abcxabcdabxabcdabcdabcy"
    >>> print(kmp(pattern, text))
    True
    """

    # 1) Construct the failure array
    failure = get_failure_array(pattern)

    # 2) Step through text searching for pattern
    i, j = 0, 0  # index into text, pattern
    while i < len(text):
        if pattern[j] == text[i]:
            if j == (len(pattern) - 1):
                return True
            j += 1

        # if this is a prefix in our pattern
        # just go back far enough to continue
        elif j > 0:
            j = failure[j - 1]
            continue
        i += 1
    return False


def get_failure_array(pattern: str) -> list[int]:
    """
    Calculates the new index we should go to if we fail a comparison
    :param pattern:
    :return:
    >>> pattern = "aabaabaaa"
    >>> get_failure_array(pattern)
    [0, 1, 0, 1, 2, 3, 4, 5, 2]
    >>> pattern = "abcdbeabc"
    >>> get_failure_array(pattern)
    [0, 0, 0, 0, 0, 0, 1, 2, 3]
    """
    failure = [0]
    i = 0
    j = 1
    while j < len(pattern):
        if pattern[i] == pattern[j]:
            i += 1
        elif i > 0:
            i = failure[i - 1]
            continue
        j += 1
        failure.append(i)
    return failure


if __name__ == "__main__":
    doctest.testmod()
