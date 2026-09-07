#!/usr/bin/env python3
"""
FreeCode — AI-Powered Python Practice Environment
===================================================

A sleek, LeetCode-style desktop app (built with tkinter, no extra installs
required) that:

  * Generates brand-new, randomized coding problems for a topic you choose
    (Arrays, Strings, Hash Tables, Linked Lists, Trees, Recursion, Dynamic
    Programming, Sorting & Searching, Math, Stack & Queue).
  * Lets you write and run real Python solutions right in the app, checked
    against freshly generated test cases.
  * Includes a built-in chat assistant — just type things like
    "give me a hard dynamic programming problem" or "array problem" and
    it'll generate and load one for you. You can also ask it for a "hint"
    or the "solution".

Run it with:

    python3 free_code.py

Requires only the Python standard library (tkinter ships with most Python
installs).
"""

import copy
import contextlib
import io
import json
import math
import random
import string
import time
import traceback

# ---------------------------------------------------------------------------
# Color palette / theme  (dark, "sleek" look)
# ---------------------------------------------------------------------------

BG = "#1e1e2e"
SURFACE = "#282a3a"
EDITOR_BG = "#181825"
GUTTER_BG = "#20212f"
TEXT = "#cdd6f4"
SUBTEXT = "#9399b2"
ACCENT = "#89b4fa"
ACCENT_HOVER = "#74a8f7"
GREEN = "#a6e3a1"
GREEN_HOVER = "#8fd68a"
RED = "#f38ba8"
YELLOW = "#f9e2af"
MAUVE = "#cba6f7"

# ---------------------------------------------------------------------------
# Linked list / tree helpers used by generated problems
# ---------------------------------------------------------------------------


class ListNode:
    """A node in a singly linked list."""

    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class TreeNode:
    """A node in a binary tree."""

    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def build_linked_list(values):
    head = None
    tail = None
    for v in values:
        node = ListNode(v)
        if head is None:
            head = node
            tail = node
        else:
            tail.next = node
            tail = node
    return head


def build_linked_list_with_cycle(values, cycle_pos):
    """Builds a linked list from `values`, then (if cycle_pos >= 0) makes the
    tail point back to the node at index `cycle_pos` to create a cycle."""
    nodes = [ListNode(v) for v in values]
    for i in range(len(nodes) - 1):
        nodes[i].next = nodes[i + 1]
    if nodes and cycle_pos is not None and cycle_pos >= 0:
        nodes[-1].next = nodes[cycle_pos]
    return nodes[0] if nodes else None


def linked_list_to_list(node):
    out = []
    seen = set()
    while node is not None:
        if id(node) in seen:
            out.append("<cycle>")
            break
        seen.add(id(node))
        out.append(node.val)
        node = node.next
    return out


def build_tree(values):
    """Builds a binary tree from a level-order list where None marks a
    missing child (LeetCode style)."""
    if not values or values[0] is None:
        return None
    it = iter(values)
    root = TreeNode(next(it))
    queue = [root]
    while queue:
        node = queue.pop(0)
        try:
            lv = next(it)
        except StopIteration:
            break
        if lv is not None:
            node.left = TreeNode(lv)
            queue.append(node.left)
        try:
            rv = next(it)
        except StopIteration:
            break
        if rv is not None:
            node.right = TreeNode(rv)
            queue.append(node.right)
    return root


# ---------------------------------------------------------------------------
# Problem model + evaluation harness
# ---------------------------------------------------------------------------


class Problem:
    """A single generated coding problem."""

    def __init__(self, title, topic, difficulty, description, function_name,
                 starter_code, test_cases, hint="", solution="",
                 input_transform=None, output_transform=None, compare=None):
        self.title = title
        self.topic = topic
        self.difficulty = difficulty
        self.description = description
        self.function_name = function_name
        self.starter_code = starter_code
        self.test_cases = test_cases  # list of (raw_args_tuple, expected)
        self.hint = hint
        self.solution = solution
        self.input_transform = input_transform
        self.output_transform = output_transform
        self.compare = compare or (lambda a, b: a == b)


def evaluate_submission(problem, source_code):
    """Executes the user's source code and runs it against a problem's test
    cases. Returns (results, top_level_error)."""
    namespace = {}
    try:
        exec(compile(source_code, "<submission>", "exec"), namespace)
    except Exception:
        return None, traceback.format_exc(limit=2)

    func = namespace.get(problem.function_name)
    if func is None or not callable(func):
        return None, (
            f"Couldn't find a function named `{problem.function_name}`. "
            f"Make sure your solution defines it exactly."
        )

    results = []
    for raw_args, expected in problem.test_cases:
        args_copy = copy.deepcopy(raw_args)
        try:
            call_args = (
                problem.input_transform(args_copy)
                if problem.input_transform
                else args_copy
            )
            start = time.time()
            actual = func(*call_args)
            elapsed = time.time() - start
            actual_cmp = (
                problem.output_transform(actual)
                if problem.output_transform
                else actual
            )
            passed = bool(problem.compare(actual_cmp, expected))
            results.append({
                "input": raw_args,
                "expected": expected,
                "actual": actual_cmp,
                "passed": passed,
                "elapsed": elapsed,
                "error": None,
            })
        except Exception:
            results.append({
                "input": raw_args,
                "expected": expected,
                "actual": None,
                "passed": False,
                "elapsed": 0,
                "error": traceback.format_exc(limit=2),
            })
    return results, None


# ---------------------------------------------------------------------------
# Difficulty scaling helper
# ---------------------------------------------------------------------------


def size_for_difficulty(difficulty, easy=(5, 8), medium=(8, 14), hard=(14, 22)):
    lo, hi = {"Easy": easy, "Medium": medium, "Hard": hard}[difficulty]
    return random.randint(lo, hi)


# ---------------------------------------------------------------------------
# Problem generators — the "AI" that builds a fresh problem every time.
# Each generator takes a difficulty string and returns a Problem with
# randomized numbers/strings and correctly computed expected outputs.
# ---------------------------------------------------------------------------

# ---- Arrays ----------------------------------------------------------------


def gen_two_sum(difficulty):
    def solve(nums, target):
        seen = {}
        for idx, v in enumerate(nums):
            if target - v in seen:
                return sorted([seen[target - v], idx])
            seen[v] = idx
        return []

    def make_case():
        n = size_for_difficulty(difficulty, (5, 7), (7, 12), (12, 18))
        nums = [random.randint(-30, 30) for _ in range(n)]
        i, j = random.sample(range(n), 2)
        target = nums[i] + nums[j]
        return nums, target

    nums1, t1 = make_case()
    e1 = solve(nums1, t1)
    nums2, t2 = make_case()
    e2 = solve(nums2, t2)
    nums3, t3 = make_case()
    e3 = solve(nums3, t3)

    # Edge cases: minimum-size array, duplicate values, negative target/numbers
    edge_min = [3, 5]
    edge_dup = [4, 4, 7, 2]
    edge_neg = [-6, 2, 9, -3, 1]
    edge_cases = [
        ((edge_min, 8), solve(edge_min, 8)),
        ((edge_dup, 8), solve(edge_dup, 8)),
        ((edge_neg, -9), solve(edge_neg, -9)),
    ]
    test_cases = [
        ((nums1, t1), e1), ((nums2, t2), e2), ((nums3, t3), e3),
    ] + edge_cases
    desc = f"""Given an array of integers `nums` and an integer `target`, return the
indices of the two numbers that add up to `target`, as a sorted list [i, j].
You may assume exactly one valid pair exists, and you may not reuse the same
element twice.

Example:
Input: nums = {nums1}, target = {t1}
Output: {e1}
"""
    starter = "def two_sum(nums, target):\n    # Your code here\n    pass\n"
    hint = ("Store each number you've seen in a dictionary mapping value -> "
            "index, so you can look up the complement (target - v) in O(1).")
    solution_code = (
        "def two_sum(nums, target):\n"
        "    seen = {}\n"
        "    for idx, v in enumerate(nums):\n"
        "        if target - v in seen:\n"
        "            return sorted([seen[target - v], idx])\n"
        "        seen[v] = idx\n"
        "    return []\n"
    )
    return Problem("Two Sum", "Arrays", difficulty, desc, "two_sum", starter,
                    test_cases, hint=hint, solution=solution_code)


def gen_max_subarray(difficulty):
    def solve(nums):
        best = cur = nums[0]
        for x in nums[1:]:
            cur = max(x, cur + x)
            best = max(best, cur)
        return best

    def make_case():
        n = size_for_difficulty(difficulty, (5, 7), (7, 12), (12, 20))
        return [random.randint(-15, 15) for _ in range(n)]

    nums1 = make_case()
    e1 = solve(nums1)
    nums2 = make_case()
    e2 = solve(nums2)
    nums3 = make_case()
    e3 = solve(nums3)

    # Edge cases: single element, all negative, all identical values
    edge_single = [random.randint(-15, 15)]
    edge_all_negative = [-3, -7, -1, -9, -4]
    edge_all_same = [5, 5, 5, 5, 5]
    edge_cases = [
        ((edge_single,), solve(edge_single)),
        ((edge_all_negative,), solve(edge_all_negative)),
        ((edge_all_same,), solve(edge_all_same)),
    ]
    test_cases = [
        ((nums1,), e1), ((nums2,), e2), ((nums3,), e3),
    ] + edge_cases
    desc = f"""Given an integer array `nums`, find the contiguous subarray (containing
at least one number) with the largest sum, and return that sum.

Example:
Input: nums = {nums1}
Output: {e1}
"""
    starter = "def max_subarray(nums):\n    # Your code here\n    pass\n"
    hint = ("Kadane's algorithm: keep a running sum that resets to just the "
            "current element whenever continuing the streak would be worse.")
    solution_code = (
        "def max_subarray(nums):\n"
        "    best = cur = nums[0]\n"
        "    for x in nums[1:]:\n"
        "        cur = max(x, cur + x)\n"
        "        best = max(best, cur)\n"
        "    return best\n"
    )
    return Problem("Maximum Subarray", "Arrays", difficulty, desc,
                    "max_subarray", starter, test_cases, hint=hint,
                    solution=solution_code)


def gen_contains_duplicate(difficulty):
    def solve(nums):
        return len(set(nums)) != len(nums)

    def make_case():
        n = size_for_difficulty(difficulty, (4, 6), (6, 12), (12, 20))
        has_dup = random.random() < 0.5
        if has_dup:
            base = [random.randint(-20, 20) for _ in range(max(n - 1, 1))]
            base.append(random.choice(base))
            random.shuffle(base)
            return base
        pool = list(range(-40, 40))
        random.shuffle(pool)
        return pool[:n]

    nums1 = make_case()
    e1 = solve(nums1)
    nums2 = make_case()
    e2 = solve(nums2)
    nums3 = make_case()
    e3 = solve(nums3)

    # Edge cases: single element (never a duplicate), all identical values,
    # and all distinct values
    edge_single = [random.randint(-20, 20)]
    edge_all_same = [4, 4, 4, 4]
    edge_all_distinct = [1, 2, 3, 4, 5]
    edge_cases = [
        ((edge_single,), solve(edge_single)),
        ((edge_all_same,), solve(edge_all_same)),
        ((edge_all_distinct,), solve(edge_all_distinct)),
    ]
    test_cases = [
        ((nums1,), e1), ((nums2,), e2), ((nums3,), e3),
    ] + edge_cases
    desc = f"""Given an integer array `nums`, return True if any value appears at
least twice in the array, and False if every element is distinct.

Example:
Input: nums = {nums1}
Output: {e1}
"""
    starter = "def contains_duplicate(nums):\n    # Your code here\n    pass\n"
    hint = ("Compare the length of the array to the length of the set of its "
            "elements — a set automatically drops duplicates.")
    solution_code = (
        "def contains_duplicate(nums):\n"
        "    return len(set(nums)) != len(nums)\n"
    )
    return Problem("Contains Duplicate", "Arrays", difficulty, desc,
                    "contains_duplicate", starter, test_cases, hint=hint,
                    solution=solution_code)


# ---- Strings -----------------------------------------------------------------


def gen_valid_palindrome(difficulty):
    def solve(s):
        cleaned = [c.lower() for c in s if c.isalnum()]
        return cleaned == cleaned[::-1]

    def make_case():
        n = size_for_difficulty(difficulty, (4, 7), (7, 12), (12, 18))
        letters = string.ascii_lowercase
        if random.random() < 0.5:
            half = [random.choice(letters) for _ in range(n // 2)]
            core = half + ([random.choice(letters)] if n % 2 else []) + half[::-1]
        else:
            core = [random.choice(letters) for _ in range(n)]
        decorated = []
        for ch in core:
            decorated.append(ch.upper() if random.random() < 0.3 else ch)
            if random.random() < 0.15:
                decorated.append(random.choice([" ", ",", "!"]))
        return "".join(decorated)

    s1 = make_case()
    e1 = solve(s1)
    s2 = make_case()
    e2 = solve(s2)
    s3 = make_case()
    e3 = solve(s3)

    # Edge cases: single character, only punctuation (cleans to empty string,
    # which is a palindrome), and a mixed-case near-palindrome that fails
    edge_single = "q"
    edge_punct_only = "!!! , ,,,"
    edge_not_palindrome = "Hello, World!"
    edge_cases = [
        ((edge_single,), solve(edge_single)),
        ((edge_punct_only,), solve(edge_punct_only)),
        ((edge_not_palindrome,), solve(edge_not_palindrome)),
    ]
    test_cases = [
        ((s1,), e1), ((s2,), e2), ((s3,), e3),
    ] + edge_cases
    desc = f"""Given a string `s`, determine whether it is a palindrome, considering
only alphanumeric characters and ignoring case. Return True or False.

Example:
Input: s = "{s1}"
Output: {e1}
"""
    starter = "def is_palindrome(s):\n    # Your code here\n    pass\n"
    hint = ("Filter down to alphanumeric characters, lowercase them, then "
            "compare the cleaned string to its reverse.")
    solution_code = (
        "def is_palindrome(s):\n"
        "    cleaned = [c.lower() for c in s if c.isalnum()]\n"
        "    return cleaned == cleaned[::-1]\n"
    )
    return Problem("Valid Palindrome", "Strings", difficulty, desc,
                    "is_palindrome", starter, test_cases, hint=hint,
                    solution=solution_code)


def gen_first_unique_char(difficulty):
    def solve(s):
        counts = {}
        for c in s:
            counts[c] = counts.get(c, 0) + 1
        for i, c in enumerate(s):
            if counts[c] == 1:
                return i
        return -1

    def make_case():
        n = size_for_difficulty(difficulty, (5, 8), (8, 14), (14, 22))
        letters = string.ascii_lowercase[:8]
        return "".join(random.choice(letters) for _ in range(n))

    s1 = make_case()
    e1 = solve(s1)
    s2 = make_case()
    e2 = solve(s2)
    s3 = make_case()
    e3 = solve(s3)

    # Edge cases: single character, no unique character exists, first char
    # itself is the unique one
    edge_single = "z"
    edge_no_unique = "aabbcc"
    edge_first_unique = "xaabbcc"
    edge_cases = [
        ((edge_single,), solve(edge_single)),
        ((edge_no_unique,), solve(edge_no_unique)),
        ((edge_first_unique,), solve(edge_first_unique)),
    ]
    test_cases = [
        ((s1,), e1), ((s2,), e2), ((s3,), e3),
    ] + edge_cases
    desc = f"""Given a string `s`, return the index of the first character that does
not repeat anywhere else in the string. If no such character exists, return -1.

Example:
Input: s = "{s1}"
Output: {e1}
"""
    starter = "def first_unique_char(s):\n    # Your code here\n    pass\n"
    hint = ("Count how many times each character appears first, then scan "
            "again and return the first index whose count is exactly 1.")
    solution_code = (
        "def first_unique_char(s):\n"
        "    counts = {}\n"
        "    for c in s:\n"
        "        counts[c] = counts.get(c, 0) + 1\n"
        "    for i, c in enumerate(s):\n"
        "        if counts[c] == 1:\n"
        "            return i\n"
        "    return -1\n"
    )
    return Problem("First Unique Character", "Strings", difficulty, desc,
                    "first_unique_char", starter, test_cases, hint=hint,
                    solution=solution_code)


def gen_reverse_words(difficulty):
    def solve(s):
        return " ".join(reversed(s.split()))

    words_pool = ["the", "quick", "brown", "fox", "jumps", "over", "lazy",
                  "dog", "code", "python", "array", "stack", "queue", "tree"]

    def make_case():
        k = size_for_difficulty(difficulty, (2, 4), (4, 7), (7, 10))
        return " ".join(random.choice(words_pool) for _ in range(k))

    s1 = make_case()
    e1 = solve(s1)
    s2 = make_case()
    e2 = solve(s2)
    s3 = make_case()
    e3 = solve(s3)

    # Edge cases: single word, extra surrounding/inner whitespace
    edge_single = "hello"
    edge_extra_spaces = "  a   bee   sea  "
    edge_cases = [
        ((edge_single,), solve(edge_single)),
        ((edge_extra_spaces,), solve(edge_extra_spaces)),
    ]
    test_cases = [
        ((s1,), e1), ((s2,), e2), ((s3,), e3),
    ] + edge_cases
    desc = f"""Given a string `s` containing words separated by spaces, return a new
string with the words in reverse order, separated by a single space (with
no leading, trailing, or extra internal spaces).

Example:
Input: s = "{s1}"
Output: "{e1}"
"""
    starter = "def reverse_words(s):\n    # Your code here\n    pass\n"
    hint = ("`str.split()` with no arguments already collapses runs of "
            "whitespace and drops leading/trailing spaces for you.")
    solution_code = (
        "def reverse_words(s):\n"
        "    return ' '.join(reversed(s.split()))\n"
    )
    return Problem("Reverse Words in a String", "Strings", difficulty, desc,
                    "reverse_words", starter, test_cases, hint=hint,
                    solution=solution_code)


# ---- Hash Table --------------------------------------------------------------


def gen_majority_element(difficulty):
    def make_case():
        n = size_for_difficulty(difficulty, (5, 7), (7, 13), (13, 21))
        majority_val = random.randint(1, 9)
        count_majority = n // 2 + 1
        nums = [majority_val] * count_majority
        while len(nums) < n:
            nums.append(random.randint(1, 9))
        random.shuffle(nums)
        return nums, majority_val

    nums1, e1 = make_case()
    nums2, e2 = make_case()
    nums3, e3 = make_case()

    # Edge cases: single-element array, and an array where every element is
    # identical (trivially the majority)
    edge_single = [7]
    edge_all_same = [3, 3, 3, 3]
    edge_cases = [
        ((edge_single,), 7),
        ((edge_all_same,), 3),
    ]
    test_cases = [
        ((nums1,), e1), ((nums2,), e2), ((nums3,), e3),
    ] + edge_cases
    desc = f"""Given an array `nums` of size n, return the majority element — the
element that appears more than n // 2 times. You may assume the array always
has a majority element.

Example:
Input: nums = {nums1}
Output: {e1}
"""
    starter = "def majority_element(nums):\n    # Your code here\n    pass\n"
    hint = "A frequency dictionary (or Boyer-Moore voting) both work well here."
    solution_code = (
        "def majority_element(nums):\n"
        "    counts = {}\n"
        "    for x in nums:\n"
        "        counts[x] = counts.get(x, 0) + 1\n"
        "        if counts[x] > len(nums) // 2:\n"
        "            return x\n"
        "    return None\n"
    )
    return Problem("Majority Element", "Hash Table", difficulty, desc,
                    "majority_element", starter, test_cases, hint=hint,
                    solution=solution_code)


def gen_group_anagrams_count(difficulty):
    def solve(words):
        groups = {}
        for w in words:
            key = "".join(sorted(w))
            groups[key] = groups.get(key, 0) + 1
        return len(groups)

    base_words = [
        "eat", "tea", "tan", "ate", "nat", "bat", "cat", "act", "tac", "car",
        "arc", "race", "care", "acre", "listen", "silent", "enlist", "god",
        "dog", "star", "rats", "arts", "tars",
    ]

    def make_case():
        k = size_for_difficulty(difficulty, (3, 5), (5, 8), (8, 12))
        return [random.choice(base_words) for _ in range(k)]

    w1 = make_case()
    e1 = solve(w1)
    w2 = make_case()
    e2 = solve(w2)
    w3 = make_case()
    e3 = solve(w3)

    # Edge cases: single word, all words identical (1 group), all words
    # distinct with no anagram overlap
    edge_single = ["cat"]
    edge_all_same = ["eat", "eat", "eat"]
    edge_all_distinct = ["dog", "star", "listen"]
    edge_cases = [
        ((edge_single,), solve(edge_single)),
        ((edge_all_same,), solve(edge_all_same)),
        ((edge_all_distinct,), solve(edge_all_distinct)),
    ]
    test_cases = [
        ((w1,), e1), ((w2,), e2), ((w3,), e3),
    ] + edge_cases
    desc = f"""Given a list of strings `words`, group the anagrams together and
return the number of distinct anagram groups.

Example:
Input: words = {w1}
Output: {e1}
"""
    starter = "def count_anagram_groups(words):\n    # Your code here\n    pass\n"
    hint = ("Use the sorted letters of each word as a dictionary key — words "
            "that are anagrams of each other will produce the same key.")
    solution_code = (
        "def count_anagram_groups(words):\n"
        "    groups = {}\n"
        "    for w in words:\n"
        "        key = ''.join(sorted(w))\n"
        "        groups[key] = groups.get(key, 0) + 1\n"
        "    return len(groups)\n"
    )
    return Problem("Group Anagrams (Count Groups)", "Hash Table", difficulty,
                    desc, "count_anagram_groups", starter, test_cases,
                    hint=hint, solution=solution_code)


def gen_intersection_count(difficulty):
    def solve(a, b):
        return len(set(a) & set(b))

    def make_case():
        n = size_for_difficulty(difficulty, (4, 6), (6, 10), (10, 16))
        a = [random.randint(1, 15) for _ in range(n)]
        b = [random.randint(1, 15) for _ in range(n)]
        return a, b

    a1, b1 = make_case()
    e1 = solve(a1, b1)
    a2, b2 = make_case()
    e2 = solve(a2, b2)
    a3, b3 = make_case()
    e3 = solve(a3, b3)

    # Edge cases: no overlap at all, and identical arrays (full overlap)
    edge_none_a, edge_none_b = [1, 2, 3], [4, 5, 6]
    edge_same = [7, 8, 9]
    edge_cases = [
        ((edge_none_a, edge_none_b), solve(edge_none_a, edge_none_b)),
        ((edge_same, edge_same), solve(edge_same, edge_same)),
    ]
    test_cases = [
        ((a1, b1), e1), ((a2, b2), e2), ((a3, b3), e3),
    ] + edge_cases
    desc = f"""Given two integer arrays `a` and `b`, return the number of distinct
values that appear in both arrays.

Example:
Input: a = {a1}, b = {b1}
Output: {e1}
"""
    starter = "def intersection_count(a, b):\n    # Your code here\n    pass\n"
    hint = ("Turn both arrays into sets, then use the `&` operator to get "
            "their intersection, and take its length.")
    solution_code = (
        "def intersection_count(a, b):\n"
        "    return len(set(a) & set(b))\n"
    )
    return Problem("Intersection of Two Arrays", "Hash Table", difficulty,
                    desc, "intersection_count", starter, test_cases,
                    hint=hint, solution=solution_code)


# ---- Linked List ---------------------------------------------------------


def gen_reverse_list(difficulty):
    def make_case():
        n = size_for_difficulty(difficulty, (3, 5), (5, 9), (9, 14))
        return [random.randint(-20, 20) for _ in range(n)]

    v1 = make_case()
    v2 = make_case()
    v3 = make_case()

    # Edge cases: single-node list and two-node list
    edge_single = [random.randint(-20, 20)]
    edge_two = [random.randint(-20, 20), random.randint(-20, 20)]
    edge_cases = [
        ((edge_single,), edge_single[::-1]),
        ((edge_two,), edge_two[::-1]),
    ]
    test_cases = [
        ((v1,), v1[::-1]), ((v2,), v2[::-1]), ((v3,), v3[::-1]),
    ] + edge_cases
    desc = f"""You are given the head of a singly linked list. Reverse the list and
return the head of the reversed list.

The linked list is built for you automatically from a plain Python list —
your function receives the actual `ListNode` head (each node has `.val`
and `.next`).

Example:
Input list values: {v1}
Output list values (reversed): {v1[::-1]}
"""
    starter = (
        "# ListNode is already defined for you:\n"
        "# class ListNode:\n"
        "#     def __init__(self, val=0, next=None):\n"
        "#         self.val = val\n"
        "#         self.next = next\n\n"
        "def reverse_list(head):\n"
        "    # Your code here\n"
        "    pass\n"
    )
    hint = ("Walk the list while keeping a `prev` pointer, and re-point each "
            "node's `next` to `prev` as you move forward.")
    solution_code = (
        "def reverse_list(head):\n"
        "    prev = None\n"
        "    while head:\n"
        "        nxt = head.next\n"
        "        head.next = prev\n"
        "        prev = head\n"
        "        head = nxt\n"
        "    return prev\n"
    )
    return Problem(
        "Reverse Linked List", "Linked List", difficulty, desc,
        "reverse_list", starter, test_cases, hint=hint, solution=solution_code,
        input_transform=lambda args: (build_linked_list(args[0]),),
        output_transform=linked_list_to_list,
    )


def gen_middle_node(difficulty):
    def solve(values):
        n = len(values)
        slow_i = fast_i = 0
        while fast_i < n - 1:
            slow_i += 1
            fast_i += 2
        return values[slow_i]

    def make_case():
        n = size_for_difficulty(difficulty, (3, 6), (6, 10), (10, 15))
        return [random.randint(-20, 20) for _ in range(n)]

    v1 = make_case()
    e1 = solve(v1)
    v2 = make_case()
    e2 = solve(v2)
    v3 = make_case()
    e3 = solve(v3)

    # Edge cases: single-node list, two-node list (tests the "second middle"
    # tie-breaking rule), and three-node list
    edge_single = [9]
    edge_two = [1, 2]
    edge_three = [1, 2, 3]
    edge_cases = [
        ((edge_single,), solve(edge_single)),
        ((edge_two,), solve(edge_two)),
        ((edge_three,), solve(edge_three)),
    ]
    test_cases = [
        ((v1,), e1), ((v2,), e2), ((v3,), e3),
    ] + edge_cases
    desc = f"""You are given the head of a singly linked list. Return the *value* of
the middle node. If there are two middle nodes, return the value of the
second middle node.

Example:
Input list values: {v1}
Output: {e1}
"""
    starter = (
        "# ListNode is already defined for you.\n\n"
        "def middle_value(head):\n"
        "    # Your code here\n"
        "    pass\n"
    )
    hint = ("Use two pointers: move `slow` one step and `fast` two steps at "
            "a time. When `fast` runs out of list, `slow` sits at the middle.")
    solution_code = (
        "def middle_value(head):\n"
        "    slow = fast = head\n"
        "    while fast and fast.next:\n"
        "        slow = slow.next\n"
        "        fast = fast.next.next\n"
        "    return slow.val\n"
    )
    return Problem(
        "Middle of the Linked List", "Linked List", difficulty, desc,
        "middle_value", starter, test_cases, hint=hint, solution=solution_code,
        input_transform=lambda args: (build_linked_list(args[0]),),
    )


def gen_has_cycle(difficulty):
    def make_case():
        n = size_for_difficulty(difficulty, (3, 5), (5, 9), (9, 14))
        values = [random.randint(-20, 20) for _ in range(n)]
        has_cycle = random.random() < 0.5
        pos = random.randint(0, n - 1) if has_cycle else -1
        return values, pos

    values1, pos1 = make_case()
    e1 = pos1 >= 0
    values2, pos2 = make_case()
    e2 = pos2 >= 0
    values3, pos3 = make_case()
    e3 = pos3 >= 0

    # Edge cases: single node with no cycle, single node that cycles to
    # itself, and a list whose cycle starts at the head (not the tail)
    edge_single_no_cycle = ([5], -1)
    edge_single_self_cycle = ([5], 0)
    edge_cycle_at_head = ([1, 2, 3, 4], 0)
    edge_cases = [
        (edge_single_no_cycle, edge_single_no_cycle[1] >= 0),
        (edge_single_self_cycle, edge_single_self_cycle[1] >= 0),
        (edge_cycle_at_head, edge_cycle_at_head[1] >= 0),
    ]
    test_cases = [
        ((values1, pos1), e1), ((values2, pos2), e2), ((values3, pos3), e3),
    ] + edge_cases
    desc = """You are given the head of a singly linked list, which may or may not
contain a cycle (a node whose `next` eventually loops back to an earlier
node). Return True if the list has a cycle, False otherwise.

Your solution should use O(1) extra space (Floyd's cycle detection /
"tortoise and hare" is the classic approach).
"""
    starter = (
        "# ListNode is already defined for you.\n\n"
        "def has_cycle(head):\n"
        "    # Your code here\n"
        "    pass\n"
    )
    hint = ("Move a `slow` pointer one step and a `fast` pointer two steps "
            "at a time. If they ever meet, there's a cycle; if `fast` "
            "reaches the end, there isn't.")
    solution_code = (
        "def has_cycle(head):\n"
        "    slow = fast = head\n"
        "    while fast and fast.next:\n"
        "        slow = slow.next\n"
        "        fast = fast.next.next\n"
        "        if slow is fast:\n"
        "            return True\n"
        "    return False\n"
    )
    return Problem(
        "Linked List Cycle", "Linked List", difficulty, desc, "has_cycle",
        starter, test_cases, hint=hint, solution=solution_code,
        input_transform=lambda args: (
            build_linked_list_with_cycle(args[0], args[1]),
        ),
    )


# ---- Trees -----------------------------------------------------------------


def _random_tree_values(difficulty):
    n = size_for_difficulty(difficulty, (3, 7), (7, 12), (12, 18))
    values = [random.randint(-10, 10)]
    for _ in range(n - 1):
        values.append(random.randint(-10, 10) if random.random() > 0.2 else None)
    return values


def gen_tree_max_depth(difficulty):
    def solve(values):
        root = build_tree(values)

        def depth(node):
            if node is None:
                return 0
            return 1 + max(depth(node.left), depth(node.right))

        return depth(root)

    v1 = _random_tree_values(difficulty)
    e1 = solve(v1)
    v2 = _random_tree_values(difficulty)
    e2 = solve(v2)
    v3 = _random_tree_values(difficulty)
    e3 = solve(v3)

    # Edge cases: single-node tree, and a fully left-skewed chain
    edge_single = [5]
    edge_chain = [1, 2, None, 3, None, 4, None]
    edge_cases = [
        ((edge_single,), solve(edge_single)),
        ((edge_chain,), solve(edge_chain)),
    ]
    test_cases = [
        ((v1,), e1), ((v2,), e2), ((v3,), e3),
    ] + edge_cases
    desc = f"""You are given the root of a binary tree, provided as a level-order
list (None marks a missing child). Return its maximum depth — the number of
nodes along the longest path from the root down to the farthest leaf.

Example:
Input (level-order): {v1}
Output: {e1}
"""
    starter = (
        "# TreeNode is already defined for you:\n"
        "# class TreeNode:\n"
        "#     def __init__(self, val=0, left=None, right=None):\n"
        "#         self.val = val\n"
        "#         self.left = left\n"
        "#         self.right = right\n\n"
        "def max_depth(root):\n"
        "    # Your code here\n"
        "    pass\n"
    )
    hint = ("Think recursively: a tree's depth is 1 + the deeper of its two "
            "subtrees. An empty tree has depth 0.")
    solution_code = (
        "def max_depth(root):\n"
        "    if root is None:\n"
        "        return 0\n"
        "    return 1 + max(max_depth(root.left), max_depth(root.right))\n"
    )
    return Problem(
        "Maximum Depth of Binary Tree", "Trees", difficulty, desc,
        "max_depth", starter, test_cases, hint=hint, solution=solution_code,
        input_transform=lambda args: (build_tree(args[0]),),
    )


def gen_tree_sum(difficulty):
    def solve(values):
        root = build_tree(values)

        def s(node):
            if node is None:
                return 0
            return node.val + s(node.left) + s(node.right)

        return s(root)

    v1 = _random_tree_values(difficulty)
    e1 = solve(v1)
    v2 = _random_tree_values(difficulty)
    e2 = solve(v2)
    v3 = _random_tree_values(difficulty)
    e3 = solve(v3)

    # Edge cases: single-node tree, tree containing all zeros, and a tree
    # containing negative values that should reduce the sum
    edge_single = [8]
    edge_zeros = [0, 0, 0, None, 0]
    edge_negative = [5, -3, -8, None, 2]
    edge_cases = [
        ((edge_single,), solve(edge_single)),
        ((edge_zeros,), solve(edge_zeros)),
        ((edge_negative,), solve(edge_negative)),
    ]
    test_cases = [
        ((v1,), e1), ((v2,), e2), ((v3,), e3),
    ] + edge_cases
    desc = f"""You are given the root of a binary tree, provided as a level-order
list (None marks a missing child). Return the sum of the values of every
node in the tree.

Example:
Input (level-order): {v1}
Output: {e1}
"""
    starter = (
        "# TreeNode is already defined for you.\n\n"
        "def tree_sum(root):\n"
        "    # Your code here\n"
        "    pass\n"
    )
    hint = "A node's total is its own value plus the sums of its left and right subtrees."
    solution_code = (
        "def tree_sum(root):\n"
        "    if root is None:\n"
        "        return 0\n"
        "    return root.val + tree_sum(root.left) + tree_sum(root.right)\n"
    )
    return Problem(
        "Sum of Binary Tree", "Trees", difficulty, desc, "tree_sum", starter,
        test_cases, hint=hint, solution=solution_code,
        input_transform=lambda args: (build_tree(args[0]),),
    )


def gen_tree_count_leaves(difficulty):
    def solve(values):
        root = build_tree(values)

        def count(node):
            if node is None:
                return 0
            if node.left is None and node.right is None:
                return 1
            return count(node.left) + count(node.right)

        return count(root)

    v1 = _random_tree_values(difficulty)
    e1 = solve(v1)
    v2 = _random_tree_values(difficulty)
    e2 = solve(v2)
    v3 = _random_tree_values(difficulty)
    e3 = solve(v3)

    # Edge cases: single-node tree (the root itself is a leaf), and a
    # left-skewed chain (exactly one leaf)
    edge_single = [4]
    edge_chain = [1, 2, None, 3, None]
    edge_cases = [
        ((edge_single,), solve(edge_single)),
        ((edge_chain,), solve(edge_chain)),
    ]
    test_cases = [
        ((v1,), e1), ((v2,), e2), ((v3,), e3),
    ] + edge_cases
    desc = f"""You are given the root of a binary tree, provided as a level-order
list (None marks a missing child). Return the number of leaf nodes (nodes
with no children).

Example:
Input (level-order): {v1}
Output: {e1}
"""
    starter = (
        "# TreeNode is already defined for you.\n\n"
        "def count_leaves(root):\n"
        "    # Your code here\n"
        "    pass\n"
    )
    hint = ("A node is a leaf when both its `left` and `right` children are "
            "None. Recurse and add up leaf counts from both subtrees.")
    solution_code = (
        "def count_leaves(root):\n"
        "    if root is None:\n"
        "        return 0\n"
        "    if root.left is None and root.right is None:\n"
        "        return 1\n"
        "    return count_leaves(root.left) + count_leaves(root.right)\n"
    )
    return Problem(
        "Count Leaf Nodes", "Trees", difficulty, desc, "count_leaves",
        starter, test_cases, hint=hint, solution=solution_code,
        input_transform=lambda args: (build_tree(args[0]),),
    )


# ---- Recursion --------------------------------------------------------------


def gen_factorial(difficulty):
    rng = {"Easy": (3, 6), "Medium": (6, 10), "Hard": (10, 15)}[difficulty]
    n1 = random.randint(*rng)
    n2 = random.randint(*rng)
    n3 = random.randint(*rng)

    # Edge cases: 0! and 1! (both equal 1, easy to get wrong with an off-by-one
    # base case)
    edge_cases = [
        ((0,), math.factorial(0)),
        ((1,), math.factorial(1)),
    ]
    test_cases = [
        ((n1,), math.factorial(n1)),
        ((n2,), math.factorial(n2)),
        ((n3,), math.factorial(n3)),
    ] + edge_cases
    desc = f"""Write a recursive function that computes the factorial of a
non-negative integer `n` (n!). Recall that 0! = 1.

Example:
Input: n = {n1}
Output: {math.factorial(n1)}
"""
    starter = "def factorial(n):\n    # Your code here (make it recursive!)\n    pass\n"
    hint = "Base case: factorial(0) = 1. Recursive case: factorial(n) = n * factorial(n - 1)."
    solution_code = (
        "def factorial(n):\n"
        "    if n == 0:\n"
        "        return 1\n"
        "    return n * factorial(n - 1)\n"
    )
    return Problem("Factorial (Recursive)", "Recursion", difficulty, desc,
                    "factorial", starter, test_cases, hint=hint,
                    solution=solution_code)


def gen_fibonacci(difficulty):
    rng = {"Easy": (3, 10), "Medium": (10, 20), "Hard": (20, 28)}[difficulty]

    def fib(n):
        a, b = 0, 1
        for _ in range(n):
            a, b = b, a + b
        return a

    n1 = random.randint(*rng)
    n2 = random.randint(*rng)
    n3 = random.randint(*rng)

    # Edge cases: fib(0) and fib(1), the two base cases
    edge_cases = [
        ((0,), fib(0)),
        ((1,), fib(1)),
    ]
    test_cases = [
        ((n1,), fib(n1)), ((n2,), fib(n2)), ((n3,), fib(n3)),
    ] + edge_cases
    desc = f"""Return the n-th Fibonacci number (0-indexed, with fib(0) = 0 and
fib(1) = 1).

Example:
Input: n = {n1}
Output: {fib(n1)}
"""
    starter = "def fibonacci(n):\n    # Your code here\n    pass\n"
    hint = ("fib(n) = fib(n-1) + fib(n-2). For larger n, prefer an iterative "
            "or memoized approach over naive recursion.")
    solution_code = (
        "def fibonacci(n):\n"
        "    a, b = 0, 1\n"
        "    for _ in range(n):\n"
        "        a, b = b, a + b\n"
        "    return a\n"
    )
    return Problem("Fibonacci Number", "Recursion", difficulty, desc,
                    "fibonacci", starter, test_cases, hint=hint,
                    solution=solution_code)


def gen_sum_digits(difficulty):
    rng = {"Easy": (10, 999), "Medium": (1000, 99999),
           "Hard": (100000, 9999999)}[difficulty]

    def solve(n):
        if n < 10:
            return n
        return n % 10 + solve(n // 10)

    n1 = random.randint(*rng)
    n2 = random.randint(*rng)
    n3 = random.randint(*rng)

    # Edge cases: single-digit number (base case) and zero
    edge_cases = [
        ((0,), solve(0)),
        ((7,), solve(7)),
    ]
    test_cases = [
        ((n1,), solve(n1)), ((n2,), solve(n2)), ((n3,), solve(n3)),
    ] + edge_cases
    desc = f"""Write a recursive function that computes the sum of the digits of a
non-negative integer `n`.

Example:
Input: n = {n1}
Output: {solve(n1)}
"""
    starter = "def sum_digits(n):\n    # Your code here (make it recursive!)\n    pass\n"
    hint = ("Base case: a single-digit number is its own digit sum. "
            "Otherwise, peel off the last digit with `n % 10` and recurse "
            "on `n // 10`.")
    solution_code = (
        "def sum_digits(n):\n"
        "    if n < 10:\n"
        "        return n\n"
        "    return n % 10 + sum_digits(n // 10)\n"
    )
    return Problem("Sum of Digits (Recursive)", "Recursion", difficulty,
                    desc, "sum_digits", starter, test_cases, hint=hint,
                    solution=solution_code)


# ---- Dynamic Programming ------------------------------------------------


def gen_climb_stairs(difficulty):
    rng = {"Easy": (3, 6), "Medium": (6, 12), "Hard": (12, 30)}[difficulty]

    def solve(n):
        if n <= 2:
            return n
        a, b = 1, 2
        for _ in range(3, n + 1):
            a, b = b, a + b
        return b

    n1 = random.randint(*rng)
    n2 = random.randint(*rng)
    n3 = random.randint(*rng)

    # Edge cases: n=1 and n=2, the two base cases of the recurrence
    edge_cases = [
        ((1,), solve(1)),
        ((2,), solve(2)),
    ]
    test_cases = [
        ((n1,), solve(n1)), ((n2,), solve(n2)), ((n3,), solve(n3)),
    ] + edge_cases
    desc = f"""You are climbing a staircase with `n` steps. Each time you can climb
either 1 or 2 steps. Return the number of distinct ways you can climb to
the top.

Example:
Input: n = {n1}
Output: {solve(n1)}
"""
    starter = "def climb_stairs(n):\n    # Your code here\n    pass\n"
    hint = "This is Fibonacci in disguise: ways(n) = ways(n-1) + ways(n-2)."
    solution_code = (
        "def climb_stairs(n):\n"
        "    if n <= 2:\n"
        "        return n\n"
        "    a, b = 1, 2\n"
        "    for _ in range(3, n + 1):\n"
        "        a, b = b, a + b\n"
        "    return b\n"
    )
    return Problem("Climbing Stairs", "Dynamic Programming", difficulty, desc,
                    "climb_stairs", starter, test_cases, hint=hint,
                    solution=solution_code)


def gen_house_robber(difficulty):
    def solve(nums):
        prev = cur = 0
        for x in nums:
            prev, cur = cur, max(cur, prev + x)
        return cur

    def make_case():
        n = size_for_difficulty(difficulty, (4, 6), (6, 10), (10, 16))
        return [random.randint(0, 50) for _ in range(n)]

    nums1 = make_case()
    e1 = solve(nums1)
    nums2 = make_case()
    e2 = solve(nums2)
    nums3 = make_case()
    e3 = solve(nums3)

    # Edge cases: single house, two houses (can only take one), all zeros
    edge_single = [12]
    edge_two = [5, 9]
    edge_zeros = [0, 0, 0, 0]
    edge_cases = [
        ((edge_single,), solve(edge_single)),
        ((edge_two,), solve(edge_two)),
        ((edge_zeros,), solve(edge_zeros)),
    ]
    test_cases = [
        ((nums1,), e1), ((nums2,), e2), ((nums3,), e3),
    ] + edge_cases
    desc = f"""You are a robber planning to rob houses along a street. `nums[i]` is
the amount of money in house i. You cannot rob two adjacent houses (it
triggers an alarm). Return the maximum amount of money you can rob.

Example:
Input: nums = {nums1}
Output: {e1}
"""
    starter = "def house_robber(nums):\n    # Your code here\n    pass\n"
    hint = ("Track two running totals as you scan left to right: the best "
            "result including the previous house, and the best excluding it.")
    solution_code = (
        "def house_robber(nums):\n"
        "    prev = cur = 0\n"
        "    for x in nums:\n"
        "        prev, cur = cur, max(cur, prev + x)\n"
        "    return cur\n"
    )
    return Problem("House Robber", "Dynamic Programming", difficulty, desc,
                    "house_robber", starter, test_cases, hint=hint,
                    solution=solution_code)


# ---- Sorting & Searching --------------------------------------------------


def gen_binary_search(difficulty):
    def solve(nums, target):
        try:
            return nums.index(target)
        except ValueError:
            return -1

    def make_case():
        n = size_for_difficulty(difficulty, (5, 8), (8, 14), (14, 22))
        nums = sorted(random.sample(range(-50, 50), n))
        if random.random() < 0.7:
            target = random.choice(nums)
        else:
            outside = [x for x in range(-55, 55) if x not in nums]
            target = random.choice(outside) if outside else 999
        return nums, target

    nums1, t1 = make_case()
    e1 = solve(nums1, t1)
    nums2, t2 = make_case()
    e2 = solve(nums2, t2)
    nums3, t3 = make_case()
    e3 = solve(nums3, t3)

    # Edge cases: single-element array (found and not found), target at the
    # very first/last index
    edge_single = [7]
    edge_bounds = [1, 4, 9, 15, 22]
    edge_cases = [
        ((edge_single, 7), solve(edge_single, 7)),
        ((edge_single, 3), solve(edge_single, 3)),
        ((edge_bounds, 1), solve(edge_bounds, 1)),
        ((edge_bounds, 22), solve(edge_bounds, 22)),
    ]
    test_cases = [
        ((nums1, t1), e1), ((nums2, t2), e2), ((nums3, t3), e3),
    ] + edge_cases
    desc = f"""Given a sorted array of distinct integers `nums` and an integer
`target`, return the index of `target` if it exists, or -1 otherwise. Your
solution should run in O(log n) time.

Example:
Input: nums = {nums1}, target = {t1}
Output: {e1}
"""
    starter = "def binary_search(nums, target):\n    # Your code here\n    pass\n"
    hint = ("Keep a low/high pointer and repeatedly check the midpoint, "
            "narrowing the search range by half each time.")
    solution_code = (
        "def binary_search(nums, target):\n"
        "    lo, hi = 0, len(nums) - 1\n"
        "    while lo <= hi:\n"
        "        mid = (lo + hi) // 2\n"
        "        if nums[mid] == target:\n"
        "            return mid\n"
        "        elif nums[mid] < target:\n"
        "            lo = mid + 1\n"
        "        else:\n"
        "            hi = mid - 1\n"
        "    return -1\n"
    )
    return Problem("Binary Search", "Sorting & Searching", difficulty, desc,
                    "binary_search", starter, test_cases, hint=hint,
                    solution=solution_code)


def gen_kth_largest(difficulty):
    def solve(nums, k):
        return sorted(nums, reverse=True)[k - 1]

    def make_case():
        n = size_for_difficulty(difficulty, (5, 8), (8, 14), (14, 20))
        nums = [random.randint(-30, 30) for _ in range(n)]
        k = random.randint(1, n)
        return nums, k

    nums1, k1 = make_case()
    e1 = solve(nums1, k1)
    nums2, k2 = make_case()
    e2 = solve(nums2, k2)
    nums3, k3 = make_case()
    e3 = solve(nums3, k3)

    # Edge cases: k=1 (the maximum), k=n (the minimum), and an array with
    # duplicate values
    edge_nums = [4, 4, 8, 8, 2, 9]
    edge_cases = [
        ((edge_nums, 1), solve(edge_nums, 1)),
        ((edge_nums, len(edge_nums)), solve(edge_nums, len(edge_nums))),
        ((edge_nums, 3), solve(edge_nums, 3)),
    ]
    test_cases = [
        ((nums1, k1), e1), ((nums2, k2), e2), ((nums3, k3), e3),
    ] + edge_cases
    desc = f"""Given an integer array `nums` and an integer `k`, return the k-th
largest element in the array (the k-th largest *value*, counting
duplicates separately — not the k-th distinct value).

Example:
Input: nums = {nums1}, k = {k1}
Output: {e1}
"""
    starter = "def kth_largest(nums, k):\n    # Your code here\n    pass\n"
    hint = ("Sorting descending and indexing at position k - 1 is the "
            "simplest approach; for a challenge, try a heap instead.")
    solution_code = (
        "def kth_largest(nums, k):\n"
        "    return sorted(nums, reverse=True)[k - 1]\n"
    )
    return Problem("Kth Largest Element", "Sorting & Searching", difficulty,
                    desc, "kth_largest", starter, test_cases, hint=hint,
                    solution=solution_code)


# ---- Math --------------------------------------------------------------


def gen_is_prime(difficulty):
    hi = {"Easy": 50, "Medium": 200, "Hard": 1000}[difficulty]

    def solve(n):
        if n < 2:
            return False
        for i in range(2, int(n ** 0.5) + 1):
            if n % i == 0:
                return False
        return True

    n1 = random.randint(2, hi)
    n2 = random.randint(2, hi)
    n3 = random.randint(2, hi)

    # Edge cases: 0 and 1 (not prime by definition), 2 (smallest prime),
    # and 4 (smallest composite)
    edge_cases = [
        ((0,), solve(0)),
        ((1,), solve(1)),
        ((2,), solve(2)),
        ((4,), solve(4)),
    ]
    test_cases = [
        ((n1,), solve(n1)), ((n2,), solve(n2)), ((n3,), solve(n3)),
    ] + edge_cases
    desc = f"""Write a function that determines whether a given integer `n` is a
prime number. Return True or False.

Example:
Input: n = {n1}
Output: {solve(n1)}
"""
    starter = "def is_prime(n):\n    # Your code here\n    pass\n"
    hint = "You only need to check possible divisors up to the square root of n."
    solution_code = (
        "def is_prime(n):\n"
        "    if n < 2:\n"
        "        return False\n"
        "    for i in range(2, int(n ** 0.5) + 1):\n"
        "        if n % i == 0:\n"
        "            return False\n"
        "    return True\n"
    )
    return Problem("Prime Checker", "Math", difficulty, desc, "is_prime",
                    starter, test_cases, hint=hint, solution=solution_code)


def gen_gcd(difficulty):
    hi = {"Easy": 50, "Medium": 500, "Hard": 5000}[difficulty]
    a1, b1 = random.randint(1, hi), random.randint(1, hi)
    a2, b2 = random.randint(1, hi), random.randint(1, hi)
    a3, b3 = random.randint(1, hi), random.randint(1, hi)

    # Edge cases: equal numbers, a divides b exactly, and gcd with 1
    edge_cases = [
        ((6, 6), math.gcd(6, 6)),
        ((4, 12), math.gcd(4, 12)),
        ((1, 17), math.gcd(1, 17)),
    ]
    test_cases = [
        ((a1, b1), math.gcd(a1, b1)),
        ((a2, b2), math.gcd(a2, b2)),
        ((a3, b3), math.gcd(a3, b3)),
    ] + edge_cases
    desc = f"""Write a function that computes the greatest common divisor (GCD) of
two positive integers `a` and `b`.

Example:
Input: a = {a1}, b = {b1}
Output: {math.gcd(a1, b1)}
"""
    starter = "def gcd(a, b):\n    # Your code here\n    pass\n"
    hint = "Euclid's algorithm: gcd(a, b) = gcd(b, a % b), repeated until b is 0."
    solution_code = (
        "def gcd(a, b):\n"
        "    while b:\n"
        "        a, b = b, a % b\n"
        "    return a\n"
    )
    return Problem("Greatest Common Divisor", "Math", difficulty, desc,
                    "gcd", starter, test_cases, hint=hint,
                    solution=solution_code)


# ---- Stack & Queue --------------------------------------------------------


def gen_valid_parentheses(difficulty):
    def solve(s):
        match = {")": "(", "]": "[", "}": "{"}
        stack = []
        for c in s:
            if c in "([{":
                stack.append(c)
            elif c in match:
                if not stack or stack.pop() != match[c]:
                    return False
        return not stack

    def make_case():
        length = size_for_difficulty(difficulty, (2, 4), (4, 7), (7, 10))
        pairs = ["()", "[]", "{}"]
        s = "".join(random.choice(pairs) for _ in range(length))
        if random.random() < 0.4:
            chars = list(s)
            random.shuffle(chars)
            s = "".join(chars)
        return s

    s1 = make_case()
    e1 = solve(s1)
    s2 = make_case()
    e2 = solve(s2)
    s3 = make_case()
    e3 = solve(s3)

    # Edge cases: empty string (vacuously valid), single unmatched bracket,
    # and mismatched-type nesting like "(]"
    edge_empty = ""
    edge_single = "("
    edge_mismatched = "([)]"
    edge_cases = [
        ((edge_empty,), solve(edge_empty)),
        ((edge_single,), solve(edge_single)),
        ((edge_mismatched,), solve(edge_mismatched)),
    ]
    test_cases = [
        ((s1,), e1), ((s2,), e2), ((s3,), e3),
    ] + edge_cases
    desc = f"""Given a string `s` containing only the characters '(', ')', '{{',
'}}', '[' and ']', determine whether the string is valid — every opening
bracket must be closed by the matching type, in the correct order.

Example:
Input: s = "{s1}"
Output: {e1}
"""
    starter = "def is_valid(s):\n    # Your code here\n    pass\n"
    hint = ("Push opening brackets onto a stack. When you hit a closing "
            "bracket, it must match whatever is on top of the stack.")
    solution_code = (
        "def is_valid(s):\n"
        "    match = {')': '(', ']': '[', '}': '{'}\n"
        "    stack = []\n"
        "    for c in s:\n"
        "        if c in '([{':\n"
        "            stack.append(c)\n"
        "        elif c in match:\n"
        "            if not stack or stack.pop() != match[c]:\n"
        "                return False\n"
        "    return not stack\n"
    )
    return Problem("Valid Parentheses", "Stack & Queue", difficulty, desc,
                    "is_valid", starter, test_cases, hint=hint,
                    solution=solution_code)


def gen_next_greater_element(difficulty):
    def solve(nums):
        res = [-1] * len(nums)
        stack = []
        for i, x in enumerate(nums):
            while stack and nums[stack[-1]] < x:
                res[stack.pop()] = x
            stack.append(i)
        return res

    def make_case():
        n = size_for_difficulty(difficulty, (4, 6), (6, 10), (10, 15))
        return [random.randint(1, 30) for _ in range(n)]

    nums1 = make_case()
    e1 = solve(nums1)
    nums2 = make_case()
    e2 = solve(nums2)
    nums3 = make_case()
    e3 = solve(nums3)

    # Edge cases: single element (always -1), strictly decreasing sequence
    # (always -1), and strictly increasing sequence
    edge_single = [random.randint(1, 30)]
    edge_decreasing = [9, 7, 5, 3, 1]
    edge_increasing = [1, 3, 5, 7, 9]
    edge_cases = [
        ((edge_single,), solve(edge_single)),
        ((edge_decreasing,), solve(edge_decreasing)),
        ((edge_increasing,), solve(edge_increasing)),
    ]
    test_cases = [
        ((nums1,), e1), ((nums2,), e2), ((nums3,), e3),
    ] + edge_cases
    desc = f"""Given an array of integers `nums`, for each element find the next
greater element to its right (the first element that is larger). If none
exists, use -1. Return the results as a list, one per input element.

Example:
Input: nums = {nums1}
Output: {e1}
"""
    starter = "def next_greater_elements(nums):\n    # Your code here\n    pass\n"
    hint = ("Keep a stack of indices with decreasing values. Whenever the "
            "current number beats the top of the stack, that's its answer.")
    solution_code = (
        "def next_greater_elements(nums):\n"
        "    res = [-1] * len(nums)\n"
        "    stack = []\n"
        "    for i, x in enumerate(nums):\n"
        "        while stack and nums[stack[-1]] < x:\n"
        "            res[stack.pop()] = x\n"
        "        stack.append(i)\n"
        "    return res\n"
    )
    return Problem("Next Greater Element", "Stack & Queue", difficulty, desc,
                    "next_greater_elements", starter, test_cases, hint=hint,
                    solution=solution_code)


# ---------------------------------------------------------------------------
# Topic registry + generation dispatch
# ---------------------------------------------------------------------------

TOPICS = {
    "Arrays": [gen_two_sum, gen_max_subarray],
    "Strings": [gen_valid_palindrome, gen_first_unique_char],
    "Hash Table": [gen_majority_element, gen_group_anagrams_count],
    "Linked List": [gen_reverse_list, gen_middle_node],
    "Trees": [gen_tree_max_depth, gen_tree_sum],
    "Recursion": [gen_factorial, gen_fibonacci],
    "Dynamic Programming": [gen_climb_stairs, gen_house_robber],
    "Sorting & Searching": [gen_binary_search, gen_kth_largest],
    "Math": [gen_is_prime, gen_gcd],
    "Stack & Queue": [gen_valid_parentheses, gen_next_greater_element],
}

DIFFICULTIES = ["Easy", "Medium", "Hard"]


def generate_problem(topic, difficulty):
    if topic not in TOPICS:
        topic = random.choice(list(TOPICS.keys()))
    generator = random.choice(TOPICS[topic])
    return generator(difficulty)


# ---------------------------------------------------------------------------
# Chat request parsing — lets the "Ask AI" tab understand free-text asks
# ---------------------------------------------------------------------------

TOPIC_KEYWORDS = {
    "Arrays": ["array", "arrays", "list problem"],
    "Strings": ["string", "strings"],
    "Hash Table": ["hash", "hashmap", "hash table", "dictionary", "hash set"],
    "Linked List": ["linked list", "linkedlist", "linked-list"],
    "Trees": ["tree", "trees", "binary tree", "bst"],
    "Recursion": ["recursion", "recursive"],
    "Dynamic Programming": ["dynamic programming", " dp ", "dp problem"],
    "Sorting & Searching": ["sort", "sorting", "search", "searching", "binary search"],
    "Math": ["math", "number theory", "prime", "gcd"],
    "Stack & Queue": ["stack", "queue", "stacks", "queues"],
}

DIFF_KEYWORDS = {
    "Easy": ["easy", "beginner", "simple"],
    "Medium": ["medium", "intermediate"],
    "Hard": ["hard", "difficult", "advanced", "challenging"],
}


def parse_chat_request(text):
    padded = f" {text.lower()} "
    found_topic = None
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in padded for kw in keywords):
            found_topic = topic
            break
    found_difficulty = "Medium"
    for difficulty, keywords in DIFF_KEYWORDS.items():
        if any(kw in padded for kw in keywords):
            found_difficulty = difficulty
            break
    return found_topic, found_difficulty


# ---------------------------------------------------------------------------
# Thin JSON wrappers used by the web front-end (in place of the tkinter GUI)
# ---------------------------------------------------------------------------

current_problem = None


def js_new_problem(topic, difficulty):
    global current_problem
    if topic not in TOPICS:
        topic = random.choice(list(TOPICS.keys()))
    current_problem = generate_problem(topic, difficulty)
    return json.dumps({
        "title": current_problem.title,
        "topic": current_problem.topic,
        "difficulty": current_problem.difficulty,
        "description": current_problem.description.strip(),
        "starter_code": current_problem.starter_code,
    })


def js_reset_code():
    if current_problem is None:
        return ""
    return current_problem.starter_code


def js_run_code(source):
    if current_problem is None:
        return json.dumps({"error": "Load a problem first."})
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            results, error = evaluate_submission(current_problem, source)
    except Exception:
        results, error = None, traceback.format_exc(limit=2)

    stdout_text = buf.getvalue()

    if error:
        return json.dumps({"error": error, "stdout": stdout_text})

    out = []
    for r in results:
        out.append({
            "input": repr(r["input"]),
            "expected": repr(r["expected"]),
            "actual": repr(r["actual"]),
            "passed": r["passed"],
            "error": r["error"],
        })
    return json.dumps({"results": out, "stdout": stdout_text})


def js_get_hint():
    if current_problem is None:
        return "Load a problem first!"
    return current_problem.hint or "No hint stored for this one -- just dive in!"


def js_get_solution():
    if current_problem is None:
        return "Load a problem first!"
    return current_problem.solution or "No reference solution stored for this problem."


def js_parse_chat(text):
    topic, difficulty = parse_chat_request(text)
    return json.dumps({"topic": topic, "difficulty": difficulty})


def js_topics():
    return json.dumps(list(TOPICS.keys()))