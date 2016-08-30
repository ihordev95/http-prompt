from pygments.lexer import RegexLexer, bygroups, words, include, combined

from pygments.token import Text, String, Keyword, Name, Operator

from . import options as opt


__all__ = ['HttpPromptLexer']


FLAG_OPTIONS = [name for name, _ in opt.FLAG_OPTIONS]
VALUE_OPTIONS = [name for name, _ in opt.VALUE_OPTIONS]


def string_rules(state):
    return [
        (r'(")((?:[^\r\n"\\]|(?:\\.))+)(")',
         bygroups(Text, String, Text), state),

        (r'(")((?:[^\r\n"\\]|(?:\\.))+)', bygroups(Text, String), state),

        (r"(')((?:[^\r\n'\\]|(?:\\.))+)(')",
         bygroups(Text, String, Text), state),

        (r"(')((?:[^\r\n'\\]|(?:\\.))+)", bygroups(Text, String), state),

        (r'([^\s"\'\\]|(\\.))+', String, state)
    ]


class HttpPromptLexer(RegexLexer):

    name = 'HttpPrompt'
    aliases = ['http-prompt']
    filenames = ['*.http-prompt']

    tokens = {
        'root': [
            (r'\s+', Text),
            (r'(cd)(\s*)', bygroups(Keyword, Text), 'cd'),
            (r'(rm)(\s*)', bygroups(Keyword, Text), 'rm_option'),
            (r'(httpie|curl)(\s*)', bygroups(Keyword, Text), 'preview_action'),
            (r'(?i)(get|head|post|put|patch|delete)(\s*)',
             bygroups(Keyword, Text), 'action'),
            (r'exit\s*', Keyword, 'end'),
            (r'help\s*', Keyword, 'end'),
            (r'env\s*', Keyword, 'redir_out'),
            (r'source\s*', Keyword, 'file_path'),
            (r'exec\s*', Keyword, 'file_path'),
            (r'', Text, 'concat_mut')
        ],

        'cd': string_rules('end'),

        'rm_option': [
            (r'(\-(?:h|o|b|q))(\s*)', bygroups(Name, Text), 'rm_name'),
            (r'(\*)(\s*)', bygroups(Name, Text), 'end')
        ],
        'rm_name': string_rules('end'),

        'concat_mut': [
            (r'$', Text, 'end'),
            (r'\s+', Text),

            # Flag options, such as `--form`, `--json`
            (words(FLAG_OPTIONS, suffix=r'\b'), Name),

            # Options with values, such as `--style=default`, `--pretty all`
            (words(VALUE_OPTIONS, suffix=r'\b'), Name, 'option_op'),

            # Unquoted or value-quoted request mutation,
            # such as `name="John Doe"`, `name=John\ Doe`
            (r'((?:[^\s\'"\\=:]|(?:\\.))+)(:|==|=)',
             bygroups(Name, Operator), 'unquoted_mut'),

            # Full single-quoted request mutation, such as `'name=John Doe'`
            (r"(')((?:[^\r\n'\\=:]|(?:\\.))+)(:|==|=)",
             bygroups(Text, Name, Operator), 'squoted_mut'),

            # Full double-quoted request mutation, such as `"name=John Doe"`
            (r'(")((?:[^\r\n"\\=:]|(?:\\.))+)(:|==|=)',
             bygroups(Text, Name, Operator), 'dquoted_mut')
        ],

        'option_op': [
            (r'(\s+|=)', Operator, 'option_value'),
        ],
        'option_value': string_rules('#pop:2'),
        'file_path': [
            (r'(/)?([^/\0]+(/)?)+', String),
        ],
        'redir_out': [
            (r'(?i)(>>|>)(\s*)', Keyword, 'file_path')
        ],

        'unquoted_mut': string_rules('#pop'),
        'squoted_mut': [
            (r"((?:[^\r\n'\\]|(?:\\.))+)(')", bygroups(String, Text), '#pop'),
            (r"([^\r\n'\\]|(\\.))+", String, '#pop')
        ],
        'dquoted_mut': [
            (r'((?:[^\r\n"\\]|(?:\\.))+)(")', bygroups(String, Text), '#pop'),
            (r'([^\r\n"\\]|(\\.))+', String, '#pop')
        ],

        'action': [
            include('urlpath')
        ],
        'preview_action': [
            (r'(?i)(get|head|post|put|patch|delete)(\s*)',
             bygroups(Keyword, Text), combined('urlpath', 'redir_out')),
            include('redir_out'),
            (r'', Text, 'urlpath')
        ],
        'urlpath': [
            (r'https?://([^\s"\'\\]|(\\.))+', String,
             combined('concat_mut', 'redir_out')),

            (r'(")(https?://(?:[^\r\n"\\]|(?:\\.))+)(")',
             bygroups(Text, String, Text), combined('concat_mut', 'redir_out')),

            (r'(")(https?://(?:[^\r\n"\\]|(?:\\.))+)', bygroups(Text, String)),

            (r"(')(https?://(?:[^\r\n'\\]|(?:\\.))+)(')",
             bygroups(Text, String, Text), combined('concat_mut', 'redir_out')),

            (r"(')(https?://(?:[^\r\n'\\]|(?:\\.))+)", bygroups(Text, String)),

            (r'(")((?:[^\r\n"\\=:]|(?:\\.))+)(")',
             bygroups(Text, String, Text), combined('concat_mut', 'redir_out')),

            (r'(")((?:[^\r\n"\\=:]|(?:\\.))+)', bygroups(Text, String)),

            (r"(')((?:[^\r\n'\\=:]|(?:\\.))+)(')",
             bygroups(Text, String, Text), combined('concat_mut', 'redir_out')),

            (r"(')((?:[^\r\n'\\=:]|(?:\\.))+)", bygroups(Text, String)),

            (r'([^\-]([^\s"\'\\=:]|(\\.))+)(\s+|$)',
             String, combined('concat_mut', 'redir_out')),
            (r'', Text, combined('concat_mut', 'redir_out'))
        ],

        'end': [
            (r'\n', Text, 'root')
        ]
    }
