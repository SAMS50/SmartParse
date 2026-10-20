
"""
Labelled test cases for SmartParse evaluation.

Each expected error contains:
- line: diagnostic anchor line
- expected: missing or expected token
- category: error type

The anchor is where the parser encounters the error,
not necessarily where the programmer should insert a token.
"""

DATASET = [
    {
        "id": "T01",
        "name": "Valid declarations",
        "source": "int x = 5;\nint y = 10;\n",
        "errors": []
    },
    {
        "id": "T02",
        "name": "Valid for loop",
        "source": (
            "for (int i = 0; i < 5; i++) {\n"
            "    x = x + i;\n"
            "}\n"
        ),
        "errors": []
    },
    {
        "id": "T03",
        "name": "Missing semicolon",
        "source": (
            "int x = 5\n"
            "int y = 10;\n"
        ),
        "errors": [
            {"line": 2, "expected": ";",
             "category": "missing"}
        ]
    },
    {
        "id": "T04",
        "name": "Missing parenthesis",
        "source": (
            "if (x > 10 {\n"
            "    x = x + 1;\n"
            "}\n"
        ),
        "errors": [
            {"line": 1, "expected": ")",
             "category": "missing"}
        ]
    },
    {
        "id": "T05",
        "name": "Wrong closing bracket",
        "source": (
            "if (x > 10] {\n"
            "    x = x + 1;\n"
            "}\n"
        ),
        "errors": [
            {"line": 1, "expected": ")",
             "category": "substitute"}
        ]
    },
    {
        "id": "T06",
        "name": "Two missing semicolons",
        "source": (
            "int x = 5\n"
            "int y = 10\n"
            "int z = 15;\n"
        ),
        "errors": [
            {"line": 2, "expected": ";",
             "category": "missing"},
            {"line": 3, "expected": ";",
             "category": "missing"}
        ]
    },
    {
        "id": "T07",
        "name": "Nested missing parenthesis",
        "source": (
            "while (x < 10) {\n"
            "    if (x > 5 {\n"
            "        x = x + 1;\n"
            "    }\n"
            "}\n"
        ),
        "errors": [
            {"line": 2, "expected": ")",
             "category": "missing"}
        ]
    },
    {
        "id": "T08",
        "name": "Missing closing brace",
        "source": (
            "int main() {\n"
            "    int x = 5;\n"
            "    return x;\n"
        ),
        "errors": [
            {"line": 4, "expected": "}",
             "category": "missing"}
        ]
    },
    {
        "id": "T09",
        "name": "Two independent errors",
        "source": (
            "int x = 5\n"
            "int y = 10;\n"
            "if (x > 2 {\n"
            "    y = y + 1;\n"
            "}\n"
        ),
        "errors": [
            {"line": 2, "expected": ";",
             "category": "missing"},
            {"line": 3, "expected": ")",
             "category": "missing"}
        ]
    },
    {
        "id": "T10",
        "name": "Missing semicolon in block",
        "source": (
            "int main() {\n"
            "    int x = 5\n"
            "    int y = 7;\n"
            "    return y;\n"
            "}\n"
        ),
        "errors": [
            {"line": 3, "expected": ";",
             "category": "missing"}
        ]
    },
    {
        "id": "T11",
        "name": "Wrong bracket in while",
        "source": (
            "while (x < 5] {\n"
            "    x = x + 1;\n"
            "}\n"
        ),
        "errors": [
            {"line": 1, "expected": ")",
             "category": "substitute"}
        ]
    },
    {
        "id": "T12",
        "name": "Valid nested function",
        "source": (
            "int add(int a, int b) {\n"
            "    return a + b;\n"
            "}\n"
            "int x = add(2, 3);\n"
        ),
        "errors": []
    }
]
