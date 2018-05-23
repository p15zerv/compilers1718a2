import plex


class ParseError(Exception):
    """ A user defined exception class, to describe parse errors. """
    pass


class RunError(Exception):
    """ A user defined exception class, to describe runtime errors. """
    pass


class MyParser:
    """ A class encapsulating all parsing functionality
    for a particular grammar. """

    def create_scanner(self, fp):
        """ Creates a plex scanner for a particular grammar
        to operate on file object fp. """

        self.run_values = []
        self.vars = {}

        # define some pattern constructs
        letter = plex.Range('azAZ')
        digit = plex.Range('09')
        id = letter + plex.Rep(letter | digit)

        bool_values = plex.NoCase(plex.Str('true', 'false', 't', 'f', '0', '1'))
        operator = plex.Str('and', 'or', 'not', '(', ')', '=')
        space = plex.Any(' \t\n')
        print_keyword = plex.Str('print')

        # the scanner lexicon - constructor argument is a list of (pattern,action ) tuples
        lexicon = plex.Lexicon([
            (print_keyword, plex.TEXT),
            (operator, plex.TEXT),
            (bool_values, 'BOOL'),
            (id, 'IDENTIFIER'),
            (space, plex.IGNORE),
        ])

        # create and store the scanner object
        self.scanner = plex.Scanner(lexicon, fp)

        # get initial lookahead
        self.la, self.val = self.next_token()

    def next_token(self):
        """ Returns tuple (next_token,matched-text). """

        return self.scanner.read()

    def position(self):
        """ Utility function that returns position in text in case of errors.
        Here it simply returns the scanner position. """

        return self.scanner.position()

    def match(self, token):
        """ Consumes (matches with current lookahead) an expected token.
        Raises ParseError if anything else is found. Acquires new lookahead. """

        if self.la == token:
            if self.la == 'BOOL':
                if self.val.lower() in ['true', 't', '1']:
                    self.run_values.append(True)
                else:
                    self.run_values.append(False)
            else:
                self.run_values.append(self.val)
            self.la, self.val = self.next_token()
        else:
            raise ParseError("found {} instead of {}".format(self.la, token))

    def parse(self, fp):
        """ Creates scanner for input file object fp and calls the parse logic code. """

        # create the plex scanner for fp
        self.create_scanner(fp)

        # call parsing logic
        self.stmt_list()
        # print('Parsing successful!')

    def evaluate_stmt(self):
        """ Evaluates and executes each statement parsed """
        # print(self.run_values)
        if self.run_values[0] == 'print':
            print(self.recursive_eval(self.run_values[1:]))
        else:
            self.vars[self.run_values[0]] = self.recursive_eval(self.run_values[2:])
        self.run_values = []

    def get_value(self, name):
        """ Returns the actual value of name """
        if name == 'and' or name == 'or' or name == 'not':
            return name
        elif isinstance(name, bool):
            return name
        elif name in self.vars:
            return self.vars[name]
        else:
            raise RunError('Variable "{}" referenced before assignment.'.format(name))

    def recursive_eval(self, sequence):
        """ Recursively evaluates the sequence """
        # print('\nEvaluating:')
        # print(sequence)
        if len(sequence) == 1:
            # If only one value left, return it
            return self.get_value(sequence[0])
        elif '(' in sequence:
            # evaluate expression in parentheses and replace that part of the sequence with its value
            left, right = self.find_par_pair(sequence)
            # print(left, right)
            val = self.recursive_eval(sequence[left:right+1])
            left_replace = max([left-1, 0])
            right_replace = min([right+2, len(sequence)])
            # print(sequence[:left_replace] + [val] + sequence[right_replace:])
            return self.recursive_eval(sequence[:left_replace] + [val] + sequence[right_replace:])
        elif 'not' in sequence:
            # if not is in the sequence, replace it and its operands with the expression's value
            new_sequence = []
            i = 0
            while i < len(sequence):
                v = sequence[i]
                if v == 'not':
                    next_val = self.get_value(sequence[i+1])
                    new_sequence.append(not next_val)
                    i += 2
                else:
                    new_sequence.append(self.get_value(v))
                    i += 1
            return self.recursive_eval(new_sequence)
        elif 'and' in sequence:
            # if and is in the sequence, replace it and its operands with the expression's value
            i = sequence.index('and')
            l_v = self.get_value(sequence[i-1])
            r_v = self.get_value(sequence[i+1])
            res = l_v and r_v
            right_replace = min([i+2, len(sequence)])
            return self.recursive_eval(sequence[:i-1] + [res] + sequence[right_replace:])
        elif 'or' in sequence:
            # if or is in the sequence, replace it and its operands with the expression's value
            i = sequence.index('or')
            l_v = self.get_value(sequence[i-1])
            r_v = self.get_value(sequence[i+1])
            res = l_v or r_v
            right_replace = min([i+2, len(sequence)])
            return self.recursive_eval(sequence[:i-1] + [res] + sequence[right_replace:])

    def find_par_pair(self, sequence):
        left = sequence.index('(')
        indentation = 1
        for index, value in enumerate(sequence[left+1:]):
            if value == '(':
                indentation += 1
            elif value == ')':
                indentation -= 1
            if indentation == 0:
                right = left + index + 1
                break
        return left + 1, right - 1

    def stmt_list(self):
        if self.la == 'IDENTIFIER' or self.la == 'print':
            self.stmt()
            self.evaluate_stmt()
            self.stmt_list()
        elif self.la is None:
            return
        else:
            raise ParseError('in stmt_list: IDENTIFIER or print expected')

    def stmt(self):
        if self.la == 'IDENTIFIER':
            self.match('IDENTIFIER')
            self.match('=')
            self.expr()
        elif self.la == 'print':
            self.match('print')
            self.expr()
        else:
            raise ParseError('in stmt: IDENTIFIER or print expected')

    def expr(self):
        if self.la == '(' or self.la == 'IDENTIFIER' or self.la == 'BOOL' or self.la == 'not':
            self.term()
            self.term_tail()
        else:
            raise ParseError(
                'in expr: ( or IDENTIFIER or BOOL or not expected')

    def term_tail(self):
        if self.la == 'or':
            self.orop()
            self.term()
            self.term_tail()
        elif self.la == 'IDENTIFIER' or self.la == 'print' or self.la is None or self.la == ')':
            return
        else:
            raise ParseError(
                'in term_tail: "or" or IDENTIFIER or print or None or ) expected')

    def term(self):
        if self.la == '(' or self.la == 'IDENTIFIER' or self.la == 'BOOL' or self.la == 'not':
            self.factor()
            self.factor_tail()
        else:
            raise ParseError(
                'in term: ( or IDENTIFIER or BOOL or not expected')

    def factor_tail(self):
        if self.la == 'and':
            self.andop()
            self.factor()
            self.factor_tail()
        elif self.la == 'or' or self.la == 'IDENTIFIER' or self.la == 'print' or self.la is None or self.la == ')':
            return
        else:
            raise ParseError(
                'in factor_tail: and or "or" or IDENTIFIER or print or ) or None expected')

    def factor(self):
        if self.la == '(' or self.la == 'IDENTIFIER' or self.la == 'BOOL':
            self.value()
        elif self.la == 'not':
            self.notop()
            self.value()
        else:
            raise ParseError('in factor')

    def value(self):
        if self.la == '(':
            self.match('(')
            self.expr()
            self.match(')')
        elif self.la == 'IDENTIFIER':
            self.match('IDENTIFIER')
        elif self.la == 'BOOL':
            self.match('BOOL')
        else:
            raise ParseError('in value: ( or IDENTIFIER or BOOL expected')

    def orop(self):
        if self.la == 'or':
            self.match('or')
        else:
            raise ParseError('in orop: or expected')

    def andop(self):
        if self.la == 'and':
            self.match('and')
        else:
            raise ParseError('in andop: and expected')

    def notop(self):
        if self.la == 'not':
            self.match('not')
        else:
            raise ParseError('in notop: not expected')


# the main part of prog

# create the parser object
parser = MyParser()

# open file for parsing
with open("recursive-descent-parsing.txt", "r") as fp:

    # parse file
    try:
        parser.parse(fp)
    except plex.errors.PlexError:
        _, lineno, charno = parser.position()
        print("Scanner Error: at line {} char {}".format(lineno, charno + 1))
    except ParseError as perr:
        _, lineno, charno = parser.position()
        print("Parser Error: {} at line {} char {}. Found: {}".format(
            perr, lineno, charno + 1, parser.la))
    except RunError as rerr:
        _, lineno, charno = parser.position()
        print("Run Error: {} at line {} char {}".format(rerr, lineno, charno + 1))
