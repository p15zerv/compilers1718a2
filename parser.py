import plex

#test
class ParseError(Exception):
    """ A user defined exception class, to describe parse errors. """
    pass


class MyParser:
    """ A class encapsulating all parsing functionality
    for a particular grammar. """

    def create_scanner(self, fp):
        """ Creates a plex scanner for a particular grammar
        to operate on file object fp. """

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
            self.la, self.val = self.next_token()
        else:
            raise ParseError("found {} instead of {}".format(self.la, token))

    def parse(self, fp):
        """ Creates scanner for input file object fp and calls the parse logic code. """

        # create the plex scanner for fp
        self.create_scanner(fp)

        # call parsing logic
        self.stmt_list()
        print('Parsing successful!')

    def stmt_list(self):
        if self.la == 'IDENTIFIER' or self.la == 'print':
            self.stmt()
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
            raise ParseError('in expr: ( or IDENTIFIER or BOOL or not expected')

    def term_tail(self):
        if self.la == 'or':
            self.orop()
            self.term()
            self.term_tail()
        elif self.la == 'IDENTIFIER' or self.la == 'print' or self.la is None or self.la == ')':
            return
        else:
            raise ParseError('in term_tail: "or" or IDENTIFIER or print or None or ) expected')

    def term(self):
        if self.la == '(' or self.la == 'IDENTIFIER' or self.la == 'BOOL' or self.la == 'not':
            self.factor()
            self.factor_tail()
        else:
            raise ParseError('in term: ( or IDENTIFIER or BOOL or not expected')

    def factor_tail(self):
        if self.la == 'and':
            self.andop()
            self.factor()
            self.factor_tail()
        elif self.la == 'or' or self.la == 'IDENTIFIER' or self.la == 'print' or self.la is None or self.la == ')':
            return
        else:
            raise ParseError('in factor_tail: and or "or" or IDENTIFIER or print or ) or None expected')

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
        print("Parser Error: {} at line {} char {}. Found: {}".format(perr, lineno, charno + 1, parser.la))
