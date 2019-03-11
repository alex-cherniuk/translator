from lexical_analysis import LexicalAnalyzer, AnalysisError, Lexeme
from postfix_transformation import PostfixProcessor, PostfixExecutor
from syntax_analysis import SyntaxAnalyzer
from file_wrapper import CSVWrapper


class Compiler(object):
    def __init__(self, root='statement_list'):
        self.lexical_analyzer = LexicalAnalyzer()
        self.syntax_analyzer = SyntaxAnalyzer()
        self.syntax_analyzer.set_root(root)
        self.postfix_transformer = PostfixProcessor()
        self.executor = PostfixExecutor()

    @property
    def variables(self):
        return self.executor.variables

    def get_lexemes(self, file, output_function, output_status=False):
        lexemes, error_log = self.lexical_analyzer.analyze(file)
        if not error_log:
            if output_status:
                output_function("Lexical analysis completed successfully")
            return lexemes
        else:
            output_function('\n'+error_log)
            return None

    def get_match(self, file, output_function, output_status=False):
        lexemes = self.get_lexemes(file, output_function, output_status)
        if lexemes:
            result = self.syntax_analyzer.get_match(lexemes)
            if isinstance(result, Lexeme):
                if result.text == '=':
                    error = AnalysisError(file=file,
                                          error_type="Syntax Error",
                                          lexeme=result,
                                          message="Wrong structure in assignment statement after symbol:")
                else:
                    error = AnalysisError(file=file,
                                          error_type="Syntax Error",
                                          lexeme=result,
                                          message="Wrong structure! Unexpected symbol:")
                output_function('\n' + str(error))
                return None
            elif result is None:
                error = AnalysisError(file=file,
                                      error_type="Syntax Error",
                                      lexeme=lexemes[-1],
                                      message="Unexpected end of the program after ")
                output_function('\n' + str(error))
                return None
            elif output_status:
                output_function("Syntax analysis completed successfully")
            return result

    def get_postfix(self, file, output_function, output_status=False):
        match = self.get_match(file, output_function)
        if match:
            terminal_matches = match.get_terminal_matches()
            postfix, marks, postfix_history = self.postfix_transformer.get_postfix_matches(terminal_matches)
            marks_table = [['mark name', 'position']]
            for mark, position in marks.items():
                marks_table.append([str(mark), position])
            CSVWrapper.write_csv(file.postfix_history_path, postfix_history)
            CSVWrapper.write_csv(file.postfix_marks_path, marks_table)
            if output_status:
                output_function(', '.join([str(element) for element in postfix]))
                output_function('\n' + CSVWrapper.read_csv(file.postfix_marks_path))
            else:
                return postfix

    def get_output(self, file, output_function, value, start_position):
        if not(value is None):
            self.executor.get_output(self.executor.postfix, file, output_function, value, start_position)
        else:
            postfix = self.get_postfix(file, output_function)
            if postfix:
                self.executor.get_output(postfix, file, output_function)
