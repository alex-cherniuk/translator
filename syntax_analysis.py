from utils import required
import re
from common import type_regexes


class Symbol(object):
    def __init__(self, name=None):
        self._name = name

    @property
    def name(self):
        if self._name:
            return self._name
        return self._get_default_name()

    @name.setter
    def name(self, value):
        self._name = value

    def _get_default_name(self):
        raise NotImplementedError

    def get_match(self, lexemes):
        raise NotImplementedError

    def __str__(self):
        return '<%s>' % self.name

    __repr__ = __str__


class RegexSymbol(Symbol):
    def __init__(self, regex):
        super(RegexSymbol, self).__init__()
        self.regex = re.compile(regex)

    """
    def get_match(self, lexemes):
        lexeme_index = self._get_lexeme_index(lexemes)
        if isinstance(lexeme_index, int):
            lexeme = lexemes[lexeme_index]
            if self.name == lexeme.lex_type:
                lexemes[lexeme_index].matched = True
                return TerminalMatch(self, lexeme), lexemes
        return None, lexemes

    @staticmethod
    def _get_lexeme_index(lexemes):
        for index, lexeme in enumerate(lexemes):
            if not lexeme.matched:
                return index
    """
    def get_match(self, lexemes):
        if lexemes:
            first_lexeme = lexemes[0]
            if self.name == first_lexeme.lex_type:
                SyntaxAnalyzer.lexeme_position_from_tail = len(lexemes)
                return TerminalMatch(self, first_lexeme), lexemes[1:]
        return None, lexemes

    def _get_default_name(self):
        return str(self.regex)


class SimpleSymbol(Symbol):
    def __init__(self, children):
        super(SimpleSymbol, self).__init__()
        self.possible_children = children

    """
    def get_match(self, lexemes):
        lexeme_index = self._get_lexeme_index(lexemes)
        if isinstance(lexeme_index, int):
            lexeme = lexemes[lexeme_index]
            if lexeme.text in self.possible_children:
                lexemes[lexeme_index].matched = True
                return TerminalMatch(self, lexeme), lexemes
        return None, lexemes 

    @staticmethod
    def _get_lexeme_index(lexemes):
        for index, lexeme in enumerate(lexemes):
            if not lexeme.matched:
                return index
    """

    def get_match(self, lexemes):
        if lexemes:
            first_lexeme = lexemes[0]
            if first_lexeme.text in self.possible_children:
                SyntaxAnalyzer.lexeme_position_from_tail = len(lexemes)
                return TerminalMatch(self, first_lexeme), lexemes[1:]
        return None, lexemes

    def _get_default_name(self):
        return str(self.possible_children)


class IterativeSymbol(Symbol):
    def __init__(self, symbols):
        super(IterativeSymbol, self).__init__()
        self.symbols = symbols

    def get_match(self, lexemes):
        symbol_matches = []
        updated_lexemes = lexemes
        while True:
            current_matches, updated_lexemes = self._get_symbol_matches(updated_lexemes)
            if current_matches:
                symbol_matches += current_matches
            elif symbol_matches:
                break
            else:
                return EmptyMatch(self), lexemes
        return NonTerminalMatch(self, symbol_matches), updated_lexemes

    def _get_symbol_matches(self, lexemes):
        updated_lexemes = lexemes
        matches = []
        for symbol in self.symbols:
            symbol_match, updated_lexemes = symbol.get_match(updated_lexemes)
            if not symbol_match:
                return None, lexemes
            matches.append(symbol_match)
        return matches, updated_lexemes

    def _get_default_name(self):
        return str(self.symbols)


class CompositeSymbol(Symbol):
    def __init__(self, children=None):
        super(CompositeSymbol, self).__init__()
        if not children:
            children = []
        self.possible_children = children

    def get_match(self, lexemes):
        matches = []
        for symbols in self.possible_children:
            symbol_match, updated_lexemes = self._get_match_for_symbols(lexemes, symbols)
            if symbol_match:
                matches.append((symbol_match, updated_lexemes))
        if not matches:
            return None, lexemes
        if len(matches) == 1:
            return matches[0]
        raise ValueError('More than one match!')

    def _get_match_for_symbols(self, lexemes, symbols):
        symbol_matches = []
        updated_lexemes = lexemes
        for symbol in symbols:
            symbol_match, updated_lexemes = symbol.get_match(updated_lexemes)
            if not symbol_match:
                return None, lexemes
            symbol_matches.append(symbol_match)
        return NonTerminalMatch(self, symbol_matches), updated_lexemes

    def _get_default_name(self):
        return str(self.possible_children)


class Match(object):
    def __init__(self, symbol):
        required(symbol)
        self.symbol = symbol

    @property
    def name(self):
        return self.symbol.name

    @property
    def text(self):
        raise NotImplementedError

    def __str__(self):
        return '%s' % self.text

    __repr__ = __str__

    def get_terminal_matches(self):
        raise NotImplementedError


class EmptyMatch(Match):
    @property
    def text(self):
        return ''

    def get_terminal_matches(self):
        return []


class NonTerminalMatch(Match):
    def __init__(self, symbol, children):
        super(NonTerminalMatch, self).__init__(symbol)
        required(children)
        self.children = children

    def get_terminal_matches(self):
        matches = []
        for child in self.children:
            matches.extend(child.get_terminal_matches())
        return [m for m in matches if not isinstance(m, EmptyMatch)]

    @property
    def text(self):
        return ' '.join([child.text for child in self.children])


class TerminalMatch(Match):
    def __init__(self, symbol, lexeme):
        super(TerminalMatch, self).__init__(symbol)
        self.lexeme = lexeme

    def get_terminal_matches(self):
        return [self]

    @property
    def text(self):
        return self.lexeme.text


class SyntaxAnalyzer(object):
    lexeme_position_from_tail = None

    def __init__(self):
        self._symbol_dict = self._get_symbol_dict()
        self._root = None

    def set_root(self, symbol_name):
        self._root = self._symbol_dict[symbol_name]

    @staticmethod
    def _get_symbol_dict():
        comparison_operator = SimpleSymbol({'==', '!=', '>', '<', '>=', '<=', '<>'})
        low_priority_math_operator = SimpleSymbol({'+', '-'})
        high_priority_math_operator = SimpleSymbol({'*', '/', '^'})
        low_priority_operator = CompositeSymbol([
            [comparison_operator],
            [low_priority_math_operator]
        ])
        opening_parenthesis = SimpleSymbol({'('})
        closing_parenthesis = SimpleSymbol({')'})
        statement_separator = SimpleSymbol({';'})
        expression = CompositeSymbol()

        constant = RegexSymbol(type_regexes['constant'])
        identifier = RegexSymbol(type_regexes['identifier'])
        assignment_operator = SimpleSymbol({'='})
        assignment_statement = CompositeSymbol([[identifier, assignment_operator, expression]])
        statement = CompositeSymbol([
            [assignment_statement]
        ])
        statement_list = IterativeSymbol([statement, statement_separator])
        opening_curly_brace = SimpleSymbol({'{'})
        closing_curly_brace = SimpleSymbol({'}'})
        statement_list_in_braces = CompositeSymbol([
            [opening_curly_brace, statement_list, closing_curly_brace]
        ])
        output_statement = CompositeSymbol([[
            SimpleSymbol('write'),
            expression
        ]])
        input_statement = CompositeSymbol([[
            SimpleSymbol('read'),
            identifier
        ]])
        conditional_statement = CompositeSymbol([[
            SimpleSymbol('if'),
            expression,
            SimpleSymbol('then'),
            statement_list_in_braces,
            SimpleSymbol('else'),
            statement_list_in_braces
        ]])
        iteration_statement = CompositeSymbol([[
            SimpleSymbol('while'),
            expression,
            SimpleSymbol('do'),
            statement_list_in_braces,
            SimpleSymbol('enddo'),
        ]])
        statement.possible_children.append([output_statement])
        statement.possible_children.append([input_statement])
        statement.possible_children.append([conditional_statement])
        statement.possible_children.append([iteration_statement])
        factor = CompositeSymbol([
            [constant],
            [low_priority_math_operator, constant],
            [identifier],
            [low_priority_math_operator, identifier],
            [opening_parenthesis, expression, closing_parenthesis]
        ])
        term = CompositeSymbol([[factor, IterativeSymbol([high_priority_math_operator, factor])]])
        iterative_symbol_for_expression_0 = IterativeSymbol([low_priority_operator, term])
        expression.possible_children.append(
            [term, iterative_symbol_for_expression_0])

        symbol_names = dir()
        symbol_dict = dict()
        for name in symbol_names:
            symbol = eval(name)
            symbol.name = name
            if name in symbol_dict:
                raise ValueError('name=%s is repeated' % name)
            symbol_dict[name] = symbol

        return symbol_dict

    def get_match(self, lexemes):
        match, updated_lexemes = self._root.get_match(lexemes)
        """
        for lexeme in updated_lexemes:
            print(lexeme.text, lexeme.matched)
            if not lexeme.matched:
                return lexeme
        if not match or isinstance(match, EmptyMatch):
            return None
        return match

        """
        if self.lexeme_position_from_tail != 1:
            return lexemes[-self.lexeme_position_from_tail+1]
        elif not match or isinstance(match, EmptyMatch) or updated_lexemes:
            return None
        return match


if __name__ == '__main__':
    from brand_new.lexical_analysis import LexicalAnalyzer
    lexical_analyzer = LexicalAnalyzer()
    syntax_analyzer = SyntaxAnalyzer()
    syntax_analyzer.set_root('output_statement')
    text = ['write a+2']
    lexemes_list = lexical_analyzer.get_lexemes(text)
    syntax_match = syntax_analyzer.get_match(lexemes_list)
    print(syntax_match)

