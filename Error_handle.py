import sys


class Error_handle:
    SYNTAX_ERROR = 1

    def __init__(self):
        pass

    def error_handle(self, error_type):
        if error_type == self.SYNTAX_ERROR:
            sys.stdout.write("syntax error near unexpected token\n")
            sys.stdout.flush()
            exit()
            pass
        pass
    pass