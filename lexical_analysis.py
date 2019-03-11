import re
from common import type_regexes
from file_wrapper import FileWrapper, CSVWrapper


class Lexeme(object):
    def __init__(self, text, lex_type, location, terminal_number):
        self.text = text
        self.lex_type = lex_type
        self.location = location
        self.terminal_number = terminal_number
        self.matched = False

    @property
    def value(self):
        if self.lex_type != 'constant':
            return self.text
        converted = int(self.text)
        if str(converted) == self.text:
            return converted
        return float(self.text)

    @property
    def line(self):
        return self.location[0]

    @property
    def column(self):
        return self.location[1]

    def to_list(self):
        return [str(self.line), str(self.column), self.text, self.lex_type, str(self.terminal_number)]

    def __str__(self):
        return '%3s:%3s %10s %12s %3s' % (self.line, self.column, self.text, self.lex_type, self.terminal_number)

    __repr__ = __str__


class _LineSplitter(object):
    def __init__(self, special_substrings):
        special_for_regex = sorted(list(special_substrings), key=lambda substring: -len(substring))
        special_for_regex = [re.escape(substring) for substring in special_for_regex]
        special_for_regex.append('\\s+')
        regex = '(%s)' % '|'.join(special_for_regex)
        self._regex = re.compile(regex)

    def get_tokens(self, line):
        tokens = re.split(self._regex, line)
        if ''.join(tokens) != line:
            raise ValueError('self-check failed')
        tokens_with_indexes = []
        current_index = 0
        for token in tokens:
            if token and not token.isspace():
                tokens_with_indexes.append((current_index, token))
            current_index += len(token)
        return tokens_with_indexes


class LexicalAnalyzer(object):
    def __init__(self):
        special_substrings = {
            ';',
            '(',
            ')',
            '==',
            '!=',
            '>=',
            '<=',
            '>',
            '<',
            '+',
            '-',
            '*',
            '/',
            '=',
            '{',
            '}',
            '^'
        }
        keywords = {
            'if',
            'then',
            'else',
            'while',
            'do',
            'enddo',
            'write',
            'read'
        }
        reserved_lexemes_list = sorted(keywords | special_substrings)
        self.terminal_lexemes = {name: i for i, name in enumerate(list(reversed(reserved_lexemes_list)))}
        self._line_splitter = _LineSplitter(special_substrings)
        self._type_regexes = {lex_type: re.compile(regex) for lex_type, regex in type_regexes.items()}

    def get_lexemes(self, rows):
        lexemes = []
        for row_number, row in enumerate(rows):
            lexemes.extend(self._get_lexemes_for_line(row_number, row))
        return lexemes

    def _get_lexemes_for_line(self, row_number, row):
        lexemes = []
        for start_index, token in self._line_splitter.get_tokens(row):
            lex_type = self._get_type(token)
            current_lexeme = Lexeme(token, lex_type, (row_number, start_index),
                                    self._get_terminal_number(token, lex_type))
            lexemes.append(current_lexeme)
        return lexemes

    def _get_type(self, text):
        if text in self.terminal_lexemes:
            return 'terminal'
        for lex_type, regex in self._type_regexes.items():
            if re.match(regex, text):
                return lex_type
        return 'error'

    def _get_terminal_number(self, text, lex_type):
        if text in self.terminal_lexemes:
            return self.terminal_lexemes[text]
        elif lex_type == 'identifier':
            return len(self.terminal_lexemes)
        return len(self.terminal_lexemes) + 1

    @staticmethod
    def _get_table(lexemes, table_type):
        table = {'index': table_type}
        for lexeme in lexemes:
            if lexeme.lex_type == table_type:
                if not (lexeme.text in table.values()):
                    index = len(table)
                    table[index] = lexeme.text
        return [[index, text] for index, text in table.items()]

    @staticmethod
    def _get_lexemes_list(lexemes):
        lexemes_list = [['line', 'column', 'name', 'type', 'number']]
        for lexeme in lexemes:
            lexemes_list.append(lexeme.to_list())
        return lexemes_list

    def analyze(self, file):
        lexemes = self.get_lexemes(file.rows)
        error_log_list = []
        for lexeme in lexemes:
            if lexeme.lex_type == 'error':
                error_log_list.append(AnalysisError(file=file,
                                                    error_type="Lexical Error",
                                                    lexeme=lexeme,
                                                    message="Unknown symbol"))
        if not error_log_list:
            lexemes_list = self._get_lexemes_list(lexemes)
            identifiers = self._get_table(lexemes, 'identifier')
            constants = self._get_table(lexemes, 'constant')
            CSVWrapper.write_csv(file.lexemes_path, lexemes_list)
            CSVWrapper.write_csv(file.identifiers_path, identifiers)
            CSVWrapper.write_csv(file.constants_path, constants)
            return lexemes, None
        return lexemes, AnalysisError.to_string(error_log_list)


class AnalysisError(object):
    def __init__(self, file, error_type, lexeme, message):
        self.file = file
        self.lexeme = lexeme
        self.error_type = error_type
        self.message = message
        self.row = self.file.rows[self.lexeme.line]

    def __str__(self):
        return "File {}\nLine {}, column {}\n{}\n{}: {} '{}'".format(self.file.file_path,
                                                                     self.lexeme.line,
                                                                     self.lexeme.column,
                                                                     self.row,
                                                                     self.error_type,
                                                                     self.message,
                                                                     self.lexeme.text)

    __repr__ = __str__

    @staticmethod
    def to_string(error_list, aggregate='\n'+'*'*60+'\n'):
        return aggregate.join(map(lambda error: str(error), error_list))


if __name__ == '__main__':
    import os
    current_working_directory = os.getcwd().replace('\\', '/')
    root_directory = '/'.join(current_working_directory.split('/')[:-1])
    test_file_path = root_directory + '/input_files/mytestfile2.txt'
    test_file = FileWrapper(test_file_path)
    _lexemes, error_log = LexicalAnalyzer().analyze(test_file)
    if not error_log:
        for _current_lexeme in _lexemes:
            print(_current_lexeme)
    else:
        print(error_log)
