import unittest
import ast

with open('llm_func_call_for_ai_agent.py') as f:
    source = f.read()

module = ast.parse(source)
selected = []
for node in module.body:
    if isinstance(node, ast.FunctionDef) and node.name in {'check_safe_eval', 'preprocess_code'}:
        selected.append(ast.get_source_segment(source, node))
code = '\n\n'.join(selected)
namespace = {"re": __import__("re"), "textwrap": __import__("textwrap"), "ast": __import__("ast")}
exec(code, namespace)
preprocess_code = namespace['preprocess_code']

class TestPreprocessCode(unittest.TestCase):
    def test_valid_code(self):
        text = """```python\nprint('hi')\n```"""
        self.assertEqual(preprocess_code(text).strip(), "print('hi')")

    def test_missing_code_block(self):
        text = "no code"
        self.assertEqual(preprocess_code(text), '')

if __name__ == '__main__':
    unittest.main()
