import pep8
import ast

from mccabe import _read, PathGraphingAstVisitor


def count_pep8_violations(repository_info, max_line_length=79, path_whitelist=None):
    path_whitelist = path_whitelist or []
    pep8style = pep8.StyleGuide(
        paths=['--max-line-length', str(max_line_length)],
        quiet=True
    )
    python_file_paths = repository_info.get_python_file_filenames()
    validatable_paths = []
    for python_file_path in python_file_paths:
        for whitelisted_path_part in path_whitelist:
            if whitelisted_path_part in python_file_path:
                break
        else:
            validatable_paths.append(python_file_path)
    result = pep8style.check_files(validatable_paths)
    return result.total_errors


def get_mccabe_violations_for_file(filepath, max_complexity):
    code = _read(filepath)
    tree = compile(code, filepath, "exec", ast.PyCF_ONLY_AST)
    visitor = PathGraphingAstVisitor()
    visitor.preorder(tree, visitor)

    violations = []
    for graph in visitor.graphs.values():
        if graph.complexity() >= max_complexity:
            complex_function_name = graph.entity
            if complex_function_name.startswith('If '):
                complex_function_name = 'if __name__ == "__main__"'
            violations.append(complex_function_name)
    return violations
