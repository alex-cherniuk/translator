from lexical_analysis import Lexeme, AnalysisError
from syntax_analysis import TerminalMatch
from file_wrapper import CSVWrapper
from copy import copy


class PostfixMark(object):
    def __init__(self, name, start_position=None):
        self.name = name
        self.start_position = start_position

    def __str__(self):
        return self.name

    __repr__ = __str__


class PostfixJump(object):
    def __init__(self, name, mark=None):
        self.name = name
        self.mark = mark

    def __str__(self):
        return '%s' % self.name

    __repr__ = __str__


class PostfixProcessor(object):
    def __init__(self):
        operators_ordering = [
            '( { if while',
            ';',
            'write read enddo',
            '=',
            'or',
            'and',
            'not',
            '< > >= <= != <> ==',
            '+ -',
            '* /',
            '^',
            '@ +_',
            ','
        ]
        self.cycles_operators = {'then': 'if', 'do': 'while'}
        self._priorities = dict()
        for priority, operators in enumerate(operators_ordering):
            for operator in operators.split(' '):
                self._priorities[operator] = priority

        self._output = None
        self._operator_stack = None
        self._dif_output = []
        self._marks = None
        self._execute_from_stack_on_separator = False

    def _reinitialize(self):
        self._output = list()
        self._marks = dict()
        self._operator_stack = list()

    def add_to_output(self, element):
        if type(element) == list:
            self._output.extend(element)
            self._dif_output.extend(element)
        else:
            self._output.append(element)
            self._dif_output.append(element)

    def _get_priority(self, match):
        return self._priorities[match.lexeme.text]

    def _move_higher_priority_operators_to_output(self, baseline_priority):
        while True:
            if not self._operator_stack:
                return
            last_operator = self._operator_stack[-1]
            if type(last_operator) == PostfixMark:
                return
            if self._get_priority(last_operator) < baseline_priority:
                return
            else:
                self.add_to_output(self._operator_stack.pop())

    def _clear_operator_stack(self, till_symbol_name=None):
        while self._operator_stack[-1].name != till_symbol_name:
            if type(self._operator_stack[-1]) == PostfixMark:
                mark = self._operator_stack[-1]
                self._marks[mark] = len(self._output)
                self._operator_stack.pop()
            else:
                self.add_to_output(self._operator_stack.pop())
        if till_symbol_name:
            self._operator_stack.pop()

    def _add_mark(self):
        mark_name = 'mark_%s' % len(self._marks)
        vars()[mark_name] = PostfixMark(mark_name)
        self._marks[eval(mark_name)] = None
        return eval(mark_name)

    @staticmethod
    def _get_printable_postfix_history(postfix_history):
        table = [['step', 'enter', 'stack', 'output']]
        for i, [enter, stack, output] in enumerate(postfix_history):
            stack_string = ', '.join([str(element) for element in stack])
            output_string = ', '.join([str(element) for element in output])
            table.append([i, str(enter), stack_string, output_string])
        return table

    def get_postfix_matches(self, infix_ordered):
        self._reinitialize()

        postfix_history = []
        for i, current_match in enumerate(infix_ordered):
            if current_match.name in {'constant', 'identifier'}:
                self.add_to_output(current_match)

            elif current_match.name in {'if', 'opening_parenthesis', 'opening_curly_brace'}:
                self._operator_stack.append(current_match)

            elif current_match.name == 'closing_parenthesis':
                self._clear_operator_stack('opening_parenthesis')

            elif current_match.name == 'closing_curly_brace':
                self._clear_operator_stack('opening_curly_brace')
                self._execute_from_stack_on_separator = True

            elif current_match.symbol.name in self.cycles_operators.keys():
                self._clear_operator_stack(self.cycles_operators[current_match.symbol.name])
                false_mark = self._add_mark()
                self.add_to_output([false_mark, PostfixJump(name='jump_on_False', mark=false_mark)])
                self._operator_stack.append(false_mark)

            elif current_match.symbol.name == 'else':
                self._execute_from_stack_on_separator = False
                exit_mark = self._add_mark()
                self.add_to_output([exit_mark, PostfixJump(name='jump', mark=exit_mark)])
                false_mark = self._operator_stack.pop()
                false_mark.start_position = len(self._output)
                self._marks[false_mark] = false_mark.start_position
                self._operator_stack.append(exit_mark)

            elif current_match.symbol.name == 'while':
                loop_mark = self._add_mark()
                loop_mark.start_position = len(self._output)
                self._marks[loop_mark] = loop_mark.start_position
                self._operator_stack.extend([loop_mark, current_match])

            elif current_match.symbol.name == 'enddo':
                self._execute_from_stack_on_separator = False
                exit_mark = self._operator_stack.pop()
                loop_mark = self._operator_stack.pop()
                self.add_to_output([loop_mark, PostfixJump(name='jump', mark=loop_mark)])
                exit_mark.start_position = len(self._output)
                self._marks[exit_mark] = exit_mark.start_position

            elif current_match.symbol.name == 'write':
                self._operator_stack.append(current_match)

            elif current_match.symbol.name == 'read':
                self._operator_stack.append(current_match)

            elif current_match.symbol.name == 'statement_separator':
                if self._execute_from_stack_on_separator:
                    match = self._operator_stack.pop()
                    if type(match) == PostfixMark:
                        match.start_position = len(self._output)
                        self._marks[match] = match.start_position
                    else:
                        self.add_to_output(match)
                    self._execute_from_stack_on_separator = False
                baseline_priority = self._get_priority(current_match)
                self._move_higher_priority_operators_to_output(baseline_priority)

            else:
                unary_operators = {'-': '@', '+': '+_'}
                if current_match.lexeme.text in unary_operators.keys():
                    previous_match = infix_ordered[i-1]
                    if not (previous_match.lexeme.lex_type in ['constant', 'identifier']) \
                            and not (previous_match.lexeme.text == ')'):
                        current_match.lexeme.text = unary_operators[current_match.lexeme.text]
                        self._operator_stack.append(current_match)
                        continue
                baseline_priority = self._get_priority(current_match)
                self._move_higher_priority_operators_to_output(baseline_priority)
                self._operator_stack.append(current_match)
            postfix_history.append([current_match, copy(self._operator_stack), self._dif_output])
            self._dif_output = []

        if self._operator_stack:
            for operator in list(reversed(self._operator_stack)):
                if type(operator) == PostfixMark:
                    self._marks[operator] = len(self._output)
                else:
                    self._dif_output.append(operator)
                    self._output.append(operator)
            postfix_history[-1][1] = []
            postfix_history[-1][2] = self._dif_output
        postfix_matches = self._output
        marks = self._marks
        self._reinitialize()
        return postfix_matches, marks, self._get_printable_postfix_history(postfix_history)


class ConstantOperand(object):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return '%s' % self.value


class IdentifierOperand(object):
    def __init__(self, lexeme, variables):
        self.lexeme = lexeme
        self.variables = variables

    def __str__(self):
        return '%s(%s)' % (self.lexeme.text, self.value)

    @property
    def identifier(self):
        return self.lexeme.value

    @property
    def value(self):
        if self.identifier in self.variables.keys():
            return self.variables[self.identifier]
        return None


class PostfixExecutor(object):
    def __init__(self):
        self.variables = dict()
        self.operands = list()
        self.postfix = list()

    def _get_operator(self, match):
        operator_str = match.lexeme.text

        if hasattr(self, '_%s' % match.symbol.name):
            return getattr(self, '_%s' % match.symbol.name)

        if operator_str == '^':
            operator_str = '**'
        if operator_str == '@':
            operator_str = '-'

        def operator(a, b):
            if type(a) == IdentifierOperand:
                if a.value is None:
                    return a.lexeme
            elif type(b) == IdentifierOperand:
                if b.value is None:
                    return b.lexeme
            if operator_str == '/' and b.value == 0:
                return ZeroDivisionError, match.lexeme
            code_str = ' '.join([str(item) for item in [a.value, operator_str, b.value]])
            return ConstantOperand(eval(code_str))

        return operator

    def _assignment_operator(self, variable_name, operand):
        self.variables[variable_name.identifier] = operand.value

    def get_output(self, postfix_ordered, file=None, output_function=None, value=None, start_position=0):
        if not(value is None):
            self._assignment_operator(self.operands.pop(), ConstantOperand(value))
        if value is None:
            self.postfix = postfix_ordered
        length_postfix_ordered = len(postfix_ordered)
        text_reading = False
        while True:
            if start_position >= length_postfix_ordered:
                break
            match = postfix_ordered[start_position]
            if type(match) == TerminalMatch:
                lexeme_value = match.lexeme.value
                if match.symbol.name == 'constant':
                    self.operands.append(ConstantOperand(lexeme_value))
                elif match.symbol.name == 'identifier':
                    self.operands.append(IdentifierOperand(match.lexeme, self.variables))
                elif match.symbol.name == 'write':
                    match = postfix_ordered[start_position-1]
                    if match.symbol.name == 'identifier':
                        output_function(self.variables[match.lexeme.text])
                    elif match.symbol.name == 'constant':
                        output_function(match.lexeme.text)
                    else:
                        output_function(self.operands.pop().value)
                elif match.symbol.name == 'read':
                    output_function(mode='input', next_compiler_position=start_position+1)
                    text_reading = True
                    break
                else:
                    if match.lexeme.text == '@':
                        last_operand = self.operands.pop()
                        result = ConstantOperand(-last_operand.value)
                    elif match.lexeme.text == '+_':
                        result = self.operands.pop()
                    else:
                        result = self._get_operator(match)(*self.operands[-2:])
                        self.operands = self.operands[:-2]
                    if type(result) == Lexeme:
                        error = AnalysisError(file=file,
                                              error_type="Name Error",
                                              lexeme=result,
                                              message="Undeclared identifier")
                        output_function('\n' + str(error))
                        break
                    elif type(result) == tuple:
                        error = AnalysisError(file=file,
                                              error_type="Value Error",
                                              lexeme=result[1],
                                              message="Zero Division")
                        output_function('\n' + str(error))
                        break
                    if result:
                        self.operands.append(result)
            elif type(match) == PostfixJump:
                if match.name == 'jump':
                    start_position = match.mark.start_position
                    continue
                elif not self.operands.pop().value:
                    start_position = match.mark.start_position
                    continue
            start_position += 1

        if not text_reading:
            if file:
                variables_table = [['variable', 'value']]
                for variable, value in self.variables.items():
                    variables_table.append([variable, value])
                CSVWrapper.write_csv(file.variables_path, variables_table)
            if len(self.operands) == 1:
                return self.operands[0].value


if __name__ == '__main__':
    from brand_new.lexical_analysis import LexicalAnalyzer
    from brand_new.syntax_analysis import SyntaxAnalyzer
    lexical_analyzer = LexicalAnalyzer()
    syntax_analyzer = SyntaxAnalyzer()
    syntax_analyzer.set_root('expression')
    postfix_processor = PostfixProcessor()
    program = ['1/0']
    lexemes = lexical_analyzer.get_lexemes(program)
    program_match = syntax_analyzer.get_match(lexemes)
    terminal_matches = program_match.get_terminal_matches()
    postfix, program_marks, history = postfix_processor.get_postfix_matches(terminal_matches)
    postfix_executor = PostfixExecutor()
    output_log = postfix_executor.get_output(postfix)
    print(history)
    print(postfix)
    print(output_log)
