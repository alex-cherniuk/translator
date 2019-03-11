import unittest

from lexical_analysis import LexicalAnalyzer
from postfix_transformation import PostfixProcessor, PostfixExecutor, PostfixJump, PostfixMark
from syntax_analysis import SyntaxAnalyzer


class _Combiner(object):
    def __init__(self, root='expression'):
        self.lexical_analyzer = LexicalAnalyzer()
        self.syntax_analyzer = SyntaxAnalyzer()
        self.syntax_analyzer.set_root(root)
        self.postfix_transformer = PostfixProcessor()
        self.executor = PostfixExecutor()

    @property
    def variables(self):
        return self.executor.variables

    def get_match(self, lines):
        if not isinstance(lines, list):
            lines = [lines]
        lexemes = self.lexical_analyzer.get_lexemes(lines)
        return self.syntax_analyzer.get_match(lexemes)

    def get_postfix(self, line):
        match = self.get_match(line)
        terminal_matches = match.get_terminal_matches()
        return self.postfix_transformer.get_postfix_matches(terminal_matches)

    def get_output(self, line):
        postfix, _, _ = self.get_postfix(line)
        return self.executor.get_output(postfix)


def to_string(matches, aggregate=' '):
    strings = []
    for match in matches:
        if type(match) in [PostfixJump, PostfixMark]:
            strings.append(str(match))
        else:
            strings.append(match.lexeme.text)
    return aggregate.join(strings)


def dict_to_string(dictionary, aggregate=', '):
    strings = ['%s: %s' % (key.name, value) for key, value in dictionary.items()]
    return aggregate.join(strings)


class ExpressionTest(unittest.TestCase):
    def setUp(self):
        self.combiner = _Combiner()

    def test0(self):
        match = self.combiner.get_match('13 != 100500')
        self.assertEquals(match.symbol.name, 'expression')

    def test1(self):
        match = self.combiner.get_match('1 == (13 != 100500)')
        self.assertEquals(match.symbol.name, 'expression')

    def test2(self):
        match = self.combiner.get_match('1 - (2 + 3)')
        self.assertEquals(match.symbol.name, 'expression')

    def test3(self):
        match = self.combiner.get_match('(1 + 1888) - (2 + 3)')
        self.assertEquals(match.symbol.name, 'expression')

    def test4(self):
        match = self.combiner.get_match('(1 + 1888) - (2 + 3)')
        self.assertEquals(match.symbol.name, 'expression')

    def test5(self):
        match = self.combiner.get_match('((1 + 1888) - (2 + 3)) + (2 + (2+3))')
        self.assertEquals(match.symbol.name, 'expression')

    def test6(self):
        match = self.combiner.get_match('(((1 + 1888) - (2 + 3)) + (2 + (2+3))) == 12')
        self.assertEquals(match.symbol.name, 'expression')

    def test7(self):
        match = self.combiner.get_match('((1 + 1888) - (2 + 3)) + (2 + (2+3))) == 12')
        self.assertEquals(match.text, ')')

    def test8_0(self):
        match = self.combiner.get_match('1 +')
        self.assertIsNone(match)

    def test8_1(self):
        match = self.combiner.get_match('+')
        self.assertIsNone(match)

    def test8_2(self):
        combiner = _Combiner('iterative_symbol_for_expression_0')
        match = combiner.get_match('+')
        self.assertIsNone(match)

    def test9(self):
        match = self.combiner.get_match('1 + 2)')
        self.assertEquals(match.text, ')')

    def test10(self):
        match = self.combiner.get_match('(((1 + 1888) - (2 + 3)) + (2 + (2+3))) == (12)')
        self.assertEquals(match.symbol.name, 'expression')

    def test11(self):
        match = self.combiner.get_match('1333 + 2333 + 3')
        self.assertEquals(match.symbol.name, 'expression')

    def test12(self):
        match = self.combiner.get_match('1333')
        self.assertEquals(match.symbol.name, 'expression')

    def test13(self):
        match = self.combiner.get_match('1333 + 1 +3+4+5+6+7+111111+ 88')
        self.assertEquals(match.symbol.name, 'expression')

    def test14(self):
        match = self.combiner.get_match('1333 + 1 +3+4/5+6+7+111111* 88')
        self.assertEquals(match.symbol.name, 'expression')

    def test15(self):
        match = self.combiner.get_match('1 * 1')
        self.assertEquals(match.symbol.name, 'expression')

    def test16(self):
        match = self.combiner.get_match('1 * 1 * 12 + 3 / 111 * 3 - 123421 + (100400 * 3 * 3 - 4342)')
        self.assertEquals(match.symbol.name, 'expression')

    def test_get_terminal_matches0(self):
        expression_as_string = '1 * ( 1 * 12 ) + 3 / 111 * 3 - 123421 + ( 100400 * 3 * 3 - 4342 )'
        match = self.combiner.get_match(expression_as_string)
        matches = match.get_terminal_matches()
        converted = to_string(matches)
        self.assertEquals(expression_as_string, converted)

    def test_get_terminal_matches1(self):
        expression_as_string = '(((1+1888)-(2+3))+(2+(2+3)))==12'
        match = self.combiner.get_match(expression_as_string)
        matches = match.get_terminal_matches()
        converted = to_string(matches, '')
        self.assertEquals(expression_as_string, converted)


class PostfixExpressionTransformationTest(unittest.TestCase):
    def setUp(self):
        self.combiner = _Combiner()

    def test0(self):
        matches, marks, _ = self.combiner.get_postfix('1 + 1')
        self.assertEquals(to_string(matches), '1 1 +')

    def test1(self):
        matches, marks, _ = self.combiner.get_postfix('1 + 2 * 3')
        self.assertEquals(to_string(matches), '1 2 3 * +')

    def test2(self):
        matches, marks, _ = self.combiner.get_postfix('1 + 2 * 3 + 100500 / 7 * 99')
        self.assertEquals(to_string(matches), '1 2 3 * + 100500 7 / 99 * +')

    def test3(self):
        matches, marks, _ = self.combiner.get_postfix('2 + 3 ^ 6 / 8')
        self.assertEquals(to_string(matches), '2 3 6 ^ 8 / +')

    def test4(self):
        matches, marks, _ = self.combiner.get_postfix('2 + 3^6 / 8')
        self.assertEquals(to_string(matches), '2 3 6 ^ 8 / +')

    def test5(self):
        matches, marks, _ = self.combiner.get_postfix('2 * (3 - 4)')
        self.assertEquals(to_string(matches), '2 3 4 - *')

    def test6(self):
        matches, marks, _ = self.combiner.get_postfix('(3 + 4) / (10 - 7) + 2 - 12 * (13 * 169)')
        self.assertEquals(to_string(matches), '3 4 + 10 7 - / 2 + 12 13 169 * * -')

    def test7(self):
        matches, marks, _ = self.combiner.get_postfix('7 / (2 * (3 + 4))')
        self.assertEquals(to_string(matches), '7 2 3 4 + * /')

    def test8(self):
        matches, marks, _ = self.combiner.get_postfix('17 * (3 + (12 + 7)^6)')
        self.assertEquals(to_string(matches), '17 3 12 7 + 6 ^ + *')


class ExecutionTest(unittest.TestCase):
    def setUp(self):
        self.combiner = _Combiner()

    def test0(self):
        result = self.combiner.get_output('1 + 1')
        self.assertEquals(2, result)

    def test1(self):
        result = self.combiner.get_output('1 + 3 + 10')
        self.assertEquals(14, result)

    def test2(self):
        result = self.combiner.get_output('12 + 3^2')
        self.assertEquals(21, result)

    def test3(self):
        result = self.combiner.get_output('(3 + 4) / (10 - 7) + 2 - 12 * (13 * 169)')
        self.assertEquals(-26359.666666666668, result)

    def test4(self):
        result = self.combiner.get_output('1 + 2 * 3 + 100500 / 7 * 99')
        self.assertEquals(1421364.1428571427, result)


class AssignmentTest(unittest.TestCase):
    def setUp(self):
        self.combiner = _Combiner('assignment_statement')

    def test0(self):
        matches, marks, _ = self.combiner.get_postfix('a = 1')
        self.assertEquals('a 1 =', to_string(matches))

    def test1(self):
        matches, marks, _ = self.combiner.get_postfix('a = 2 + 2 / 3')
        self.assertEquals('a 2 2 3 / + =', to_string(matches))

    def test2(self):
        matches, marks, _ = self.combiner.get_postfix('a = (56 + 2^141) / 3')
        self.assertEquals('a 56 2 141 ^ + 3 / =', to_string(matches))

    def test3(self):
        matches, marks, _ = self.combiner.get_postfix('a = 3 + 100500')
        self.assertEquals('a 3 100500 + =', to_string(matches))

    def test4(self):
        self.combiner.get_output('a = 3 + 100500')
        self.assertEquals({'a': 100503}, self.combiner.variables)

    def test5(self):
        self.combiner.get_output('variable_name = 3 + 2^4')
        self.assertEquals({'variable_name': 19}, self.combiner.variables)


class ProgramTest(unittest.TestCase):
    def setUp(self):
        self.combiner = _Combiner('statement_list')

    def test0(self):
        matches, marks, _ = self.combiner.get_postfix([
            'if b == 20 then',
            '   {c = b - 5;}',
            'else',
            '   {a = 10;};',
            'b = c - a;'])
        self.assertEquals(to_string(matches), 'b 20 == mark_0 jump_on_False c b 5 - = mark_1 jump a 10 = b c a - =')
        self.assertEquals(dict_to_string(marks), 'mark_0: 12, mark_1: 15')

    def test1(self):
        self.combiner.get_output([
            'a = 3 + 1;',
            'b = 3 + 1 - 1;',
            'c = 8 - 1;',
        ])
        self.assertEquals({
            'a': 4,
            'b': 3,
            'c': 7
        }, self.combiner.variables)

    def test2(self):
        self.combiner.get_output([
            'a = 3 + 1;',
            'b = a + 2;',
        ])
        self.assertEquals({
            'a': 4,
            'b': 6,
        }, self.combiner.variables)

    def test3(self):
        self.combiner.get_output([
            'a = 3 + 1;',
            'a = a + 2;',
        ])
        self.assertEquals({
            'a': 6,
        }, self.combiner.variables)

    def test4(self):
        self.combiner.get_output([
            'a = 3 + 1;',
            'a = a + 2;',
        ])
        self.assertEquals({
            'a': 6,
        }, self.combiner.variables)

    def test5(self):
        self.combiner.get_output([
            'a = 3 + 1;',
            'a = a + 2;',
            'b = a + 2;',
            'b = a + 2;',
            'a = a + 2;',
        ])
        self.assertEquals({
            'a': 8,
            'b': 8,
        }, self.combiner.variables)

    def test6(self):
        self.combiner.get_output([
            'a = 3 + 1;',
            'a = a^2 + 2;',
        ])
        self.assertEquals({
            'a': 18,
        }, self.combiner.variables)


class StatementListInBracesTest(unittest.TestCase):
    def setUp(self):
        self.combiner = _Combiner('statement_list_in_braces')

    def test0(self):
        match = self.combiner.get_match('{a = 1;}')
        self.assertEquals(match.symbol.name, 'statement_list_in_braces')

    def test1(self):
        match = self.combiner.get_match('{a = 1; b=3*3 + 6^131212; a = a + b;}')
        self.assertEquals(match.symbol.name, 'statement_list_in_braces')


class ConditionalsTest(unittest.TestCase):
    def setUp(self):
        self.combiner = _Combiner('conditional_statement')

    def test0(self):
        match = self.combiner.get_match('if 12 then {a = 1;} else {a=3;}')
        self.assertEquals(match.symbol.name, 'conditional_statement')

    def test1(self):
        match = self.combiner.get_match('if 12 then {a = 1; b = c^3;} else {a=3; a=3+7+a;}')
        self.assertEquals(match.symbol.name, 'conditional_statement')

    def test2(self):
        match = self.combiner.get_match('if 12 > 3 then {a = 1; b = c^3;} else {a=3; a=3+7+a;}')
        self.assertEquals(match.symbol.name, 'conditional_statement')

    def test3(self):
        match = self.combiner.get_match([
            '    if b == 20 then',
            '        {c = b - 5;}',
            '    else',
            '        {a = 10;}'])
        self.assertEquals(match.symbol.name, 'conditional_statement')

    def test4(self):
        matches, marks, _ = self.combiner.get_postfix('if 12 > 3 then {a = 1;} else {a=3;}')
        self.assertEquals(to_string(matches), '12 3 > mark_0 jump_on_False a 1 = mark_1 jump a 3 =')
        self.assertEquals(dict_to_string(marks), 'mark_0: 10, mark_1: 13')


class IterationalsTest(unittest.TestCase):
    def setUp(self):
        self.combiner = _Combiner('iteration_statement')

    def test0(self):
        match = self.combiner.get_match('while a < 10 do {a = a + 1;} enddo')
        self.assertEquals(match.symbol.name, 'iteration_statement')

    def test1(self):
        match = self.combiner.get_match('while b >= 10 do {b = b - (a + 1);} enddo')
        self.assertEquals(match.symbol.name, 'iteration_statement')

    def test2(self):
        match = self.combiner.get_match([
            'while a >= 10 do {',
            '    b = b + 1;',
            '    if b == 20 then',
            '        {c = b - 5;}',
            '    else',
            '        {a = 10;};',
            '    }',
            'enddo'])
        self.assertEquals(match.symbol.name, 'iteration_statement')

    def test3(self):
        match = self.combiner.get_match([
            'while a < 10 do {',
            '    a = a + 1;',
            '    b = a*5 + 1;'
            '    }',
            'enddo'])
        self.assertEquals(match.symbol.name, 'iteration_statement')

    def test4(self):
        matches, marks, _ = self.combiner.get_postfix([
            'while a >= 10 do {',
            '    b = b + 1;',
            '    if b == 20 then',
            '        {c = b - 5;}',
            '    else',
            '        {a = 10;};',
            '    }',
            'enddo'])
        matches_string = 'a 10 >= mark_1 jump_on_False b b 1 + = b 20 == mark_2 jump_on_False' \
                         ' c b 5 - = mark_3 jump a 10 = mark_0 jump'
        self.assertEquals(to_string(matches), matches_string)
        self.assertEquals(dict_to_string(marks), 'mark_0: 0, mark_1: 27, mark_2: 22, mark_3: 25')

    def test5(self):
        matches, marks, _ = self.combiner.get_postfix([
            'while a < 10 do {',
            '    a = a + 1;',
            '    b = a*5 + 1;'
            '    }',
            'enddo'])
        matches_string = 'a 10 < mark_1 jump_on_False a a 1 + = b a 5 * 1 + = mark_0 jump'
        self.assertEquals(to_string(matches), matches_string)
        self.assertEquals(dict_to_string(marks), 'mark_0: 0, mark_1: 19')
