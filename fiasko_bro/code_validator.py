from collections import OrderedDict

from . import validators


class CodeValidator:
    blacklists = {
        'has_variables_from_blacklist': [
            'list',
            'lists',
            'input',
            'cnt',
            'data',
            'name',
            'load',
            'value',
            'object',
            'file',
            'result',
            'item',
            'num',
            'info',
            'n',
        ],
        'has_no_commit_messages_from_blacklist': [
            'win',
            'commit',
            'commit#1',
            'fix',
            'minor edits',
            'update',
            'done',
            'first commit',
            'start',
            'refactor',
            '!',
            'bug fix',
            'corrected',
            'add files via upload',
            'test',
            'fixed',
            'minor bugfix',
            'minor bugfixes',
            'finished',
            'first commit',
            'fixes',
            '',
        ],
        'has_no_directories_from_blacklist': [
            '.idea',
            '__pycache__',
            '.vscode',
        ],
    }

    whitelists = {
        'has_no_short_variable_names': [
            'a',
            'b',
            'c',
            'x',
            'y',
            'x1',
            'x2',
            'y1',
            'y2',
            '_',
        ],
        'has_no_calls_with_constants': [
            'pow',
            'exit',
            'round',
            'range',
            'enumerate',
            'time',
            'itemgetter',
            'get',
            'group',
            'replace',
            'combinations',
            'seek',
        ],
        'is_snake_case': [
            # from sqlalchemy.sqlalchemy.orm.sessionmaker
            'Session',
            # from sqlalchemy.ext.automap
            'Base',
            'User',
            'Order'
            'Address',
        ],
        'right_assignment_for_snake_case': [
            'Base',
        ],
        'has_no_exit_calls_in_functions': [
            'main',
        ],
        'is_pep8_fine': [
            '/migrations/',
            '/alembic/',
            'manage.py',
        ],
        'has_no_encoding_declaration': [
            '/migrations/',
        ],
        'has_no_local_imports': [
            'manage.py',
        ],
        'has_local_var_named_as_global': [
            'settings.py',
        ],
        'has_variables_from_blacklist': [
            'apps.py',
        ],
        'has_no_extra_dockstrings_whitelist': [
            '/migrations/',
            '/alembic/',
        ]
    }

    _default_settings = {
        'readme_filename': 'README.md',
        'allowed_max_pep8_violations': 5,
        'max_complexity': 7,
        'minimum_name_length': 2,
        'min_percent_of_another_language': 30,
        'last_commits_to_check_amount': 5,
        'tab_size': 4,
        'functions_with_docstrings_percent_limit': 80,
        'max_pep8_line_length': 100,
    }

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
            (
                'encoding',
                [validators.are_sources_in_utf],
            ),
            (
                'bom',
                [validators.has_no_bom],
            ),
            (
                'syntax',
                [validators.has_no_syntax_errors],
            ),
            (
                'general',
                [
                    validators.has_no_directories_from_blacklist,
                    validators.is_pep8_fine,
                    validators.has_changed_readme,
                    validators.is_snake_case,
                    validators.is_mccabe_difficulty_ok,
                    validators.has_no_encoding_declaration,
                    validators.has_no_star_imports,
                    validators.has_no_local_imports,
                    validators.has_local_var_named_as_global,
                    validators.has_variables_from_blacklist,
                    validators.has_no_short_variable_names,
                    validators.has_no_range_from_zero,
                    validators.are_tabs_used_for_indentation,
                    validators.has_no_try_without_exception,
                    validators.has_frozen_requirements,
                    validators.has_no_vars_with_lambda,
                    validators.has_no_calls_with_constants,
                    validators.has_readme_in_single_language,
                    validators.has_no_urls_with_hardcoded_arguments,
                    validators.has_no_nonpythonic_empty_list_validations,
                    validators.has_no_extra_dockstrings,
                    validators.has_no_exit_calls_in_functions,
                    validators.has_no_libs_from_stdlib_in_requirements,
                    validators.has_no_lines_ends_with_semicolon,
                    validators.not_validates_response_status_by_comparing_to_200,
                    validators.has_no_mutable_default_arguments,
                    validators.has_no_slices_starts_from_zero,
                    validators.has_no_cast_input_result_to_str,
                    validators.has_no_return_with_parenthesis,
                ],
            ),
        ]
    )

    warning_validator_groups = {
        'commits': [
            validators.has_no_commit_messages_from_blacklist,
        ],
        'syntax': [
            validators.has_indents_of_spaces,
            validators.has_no_variables_that_shadow_default_names,
        ]
    }

    for name in warning_validator_groups:
        assert name in error_validator_groups.keys()

    def __init__(self, **kwargs):
        self.validator_arguments = dict(self._default_settings)
        self.validator_arguments.update(kwargs)

    @staticmethod
    def _is_successful_validation(validation_result):
        return not isinstance(validation_result, tuple)

    def _run_validator_group(self, group, arguments):
        errors = []
        for validator in group:
            validation_result = validator(**arguments)
            if not self._is_successful_validation(validation_result):
                errors.append(validation_result)
        return errors

    def _run_warning_validators_until(self, failed_error_group_name, arguments):
        """Gets warnings up until but not including the failed group"""
        warnings = []
        for error_group_name in self.error_validator_groups.keys():
            if error_group_name == failed_error_group_name:
                return warnings
            warnings += self._run_validator_group(
                self.warning_validator_groups.get(error_group_name, []),
                arguments
            )
        return warnings

    def validate(self, solution_repo, original_repo=None, **kwargs):
        self.validator_arguments.update(kwargs)
        self.validator_arguments['whitelists'] = self.whitelists
        self.validator_arguments['blacklists'] = self.blacklists
        self.validator_arguments['solution_repo'] = solution_repo
        if original_repo:
            self.validator_arguments['original_repo'] = original_repo

        errors = []
        for error_group_name, error_group in self.error_validator_groups.items():
            errors += self._run_validator_group(
                error_group,
                self.validator_arguments
            )
            if errors:
                errors += self._run_warning_validators_until(
                    error_group_name,
                    self.validator_arguments
                )
                return errors
        return errors