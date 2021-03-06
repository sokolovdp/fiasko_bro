# Fiasko Bro

Fiasko Bro enables you to automatically review Python code in a git repo.

Here's the simplest usage example:

```python
>>> from fiasko_bro import CodeValidator, LocalRepositoryInfo
>>> code_validator = CodeValidator()
>>> repo_to_validate = LocalRepositoryInfo('/path/to/repo/')
>>> code_validator.validate(repo_to_validate)
[('camel_case_vars', 'переименуй, например, WorkBook.')]
```
The `validate` method returns list of tuples which consist of an error slug and an error message.

You might also want to compare it against some "original" repo:
```python
>>> from fiasko_bro import CodeValidator, LocalRepositoryInfo
>>> code_validator = CodeValidator()
>>> repo_to_validate = LocalRepositoryInfo(solution_repo='/path/to/repo/')
>>> original_repo = LocalRepositoryInfo(original_repo='/path/to/different/repo/')
>>> code_validator.validate(solution_repo=repo_to_validate, original_repo=original_repo)
[('no_new_code', None)]
```
In this example, no new code was added to the original repo, so the validation has stopped.

## Customize validators
### How validators work
Of course, the standard suit of validators can be modified in a way that best suits your needs.

The are two kinds of validators: error validators and warning validators.
The difference between them is that warning validators don't halt the validation process, while the error validators do.
Error validators are [grouped](https://github.com/devmanorg/fiasko_bro/blob/master/fiasko_bro/code_validator.py#L133) according to their purpose, like so:
```python
error_validator_groups = OrderedDict(
    [
        (
            'commits',
            [validators.has_more_commits_than_origin],
        ),
        (
            'readme',
            [validators.has_readme_file],
        ),
        ...
    ]
)
```
Here, for example, you have the group `commits` that consists only of one validator `has_more_commits_than_origin`.

In each group, every validator is executed.
If some of the validators in the group fail, the `validate` method returns the error list without proceeding to the next group.
If all the validators in the error group succeed, the warning validators for this group are executed.
They are stored in `warning_validator_groups`:
```python
warning_validator_groups = {
    'commits': [
        validators.has_no_commit_messages_from_blacklist,
    ],
    'syntax': [
        validators.has_indents_of_spaces,
        validators.has_no_variables_that_shadow_default_names,
    ]
}
```
The `commits` warning validator group is executed only if the `commits` error validator group passes successfully.

Warning validators just add some more errors in case the validation failed.
They are not executed if none of the error validators failed.

### Add a simple validator
A simple validator is a validator that only takes the repository to validate. It returns `None` is case of success
and a tuple of an error slug and an error message in case of a problem. Here's an example of existing validator:
```python
def has_no_syntax_errors(solution_repo, *args, **kwargs):
    for filename, tree in solution_repo.get_ast_trees(with_filenames=True):
        if tree is None:
            return 'syntax_error', 'в %s' % filename
```
Note the `*args, **kwargs` part. The validator actually gets a lot of arguments, but doesn't care about them.

Now you can add validator to one of the existing validator groups or create your own:
```python
code_validator.error_validator_groups['general'].append(has_no_syntax_errors)
```

### Compare against original repo
If you want your validator to compare against some other repository, add the `original repo` argument.
```python
def has_more_commits_than_origin(solution_repo, original_repo=None, *args, **kwargs):
    if not original_repo:
        return
    if solution_repo.count_commits() <= original_repo.count_commits():
        return 'no_new_code', None
```
Notice we made sure our validator succeeds in case there's no `original_repo`.
We consider it a sensible solution for our case, but you can choose any other behavior.

### Conditionally execute a validator
If you want the validator to be executed only for certain types of repositories, add `tokenized_validator` to it:

```python
from fiasko_bro import tokenized_validator

@tokenized_validator(token='min_max_challenge')
def has_min_max_functions(solution_repo, *args, **kwargs):
    for tree in solution_repo.get_ast_trees():
        names = get_all_names_from_tree(tree)
        if 'min' in names and 'max' in names:
            return
    return 'builtins', 'no min or max is used'
```

then add the validator to the appropriate group
```python
code_validator.error_validator_groups['general'].append(has_min_max_functions)
```
and when calling `validate` for certain repo, pass the token:
```python
code_validator.validate(solution_repo=solution_repo, validator_token='min_max_challenge')
```
The validator won't be executed for any other repository.

### Blacklist/whitelists for validators
For every rule there's an exception. Exceptions are easy to take into account using blacklists or whitelists.

First, add the blacklist and whitelist to the `code_validator` instance:
```python
code_validator.whitelists['has_no_calls_with_constants'] = ['pow', 'exit']
```
Then create and add the validator with the same name as the dictionary key:
```python
def has_no_calls_with_constants(solution_repo, whitelists, *args, **kwargs):
    whitelist = whitelists.get('has_no_calls_with_constants', [])
    for filepath, tree in solution_repo.get_ast_trees(with_filenames=True):
        if 'tests' in filepath:  # tests can have constants in asserts
            continue
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
        for call in calls:
            if isinstance(ast_helpers.get_closest_definition(call), ast.ClassDef):  # for case of id = db.String(256)
                continue
            attr_to_get_name = 'id' if hasattr(call.func, 'id') else 'attr'
            function_name = getattr(call.func, attr_to_get_name, None)
            if not function_name or function_name in whitelist:
                continue
            for arg in call.args:
                if isinstance(arg, ast.Num):
                    return 'magic_numbers', 'например, %s' % arg.n
```
Notice in the first line we pull the whitelist from the dictionary and incorporate it in our validation logic.

### Installation

With pip:
```bash
pip install git+https://github.com/devmanorg/fiasko_bro.git
```

Or just clone the project and install the requirements:
```bash
$ git clone https://github.com/devmanorg/fiasko_bro.git
$ cd fiasko_bro
$ pip install -r requirements.txt
```
