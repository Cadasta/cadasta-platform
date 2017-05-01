import pytest

from django.test import TestCase

from .. import parser


class ParserTest(TestCase):

    def test_parse_string(self):
        p = parser.query.parseString

        # Simple cases
        assert p('a').asList() == ['a']
        assert p('a        ').asList() == ['a']
        assert p('    a    ').asList() == ['a']
        assert p('        a').asList() == ['a']
        assert p('a b').asList() == ['a', 'b']
        assert p('a             b').asList() == ['a', 'b']
        assert p('   a          b').asList() == ['a', 'b']
        assert p('a          b   ').asList() == ['a', 'b']
        assert p('   a       b   ').asList() == ['a', 'b']
        assert p('a_b').asList() == ['a_b']
        assert p('a b c').asList() == ['a', 'b', 'c']
        assert p('a___ b--- c+++').asList() == ['a___', 'b---', 'c+++']

        # Quoted cases
        assert p('"a b"').asList() == ['"a b"']
        assert p('"a    b"').asList() == ['"a    b"']
        assert p('"a b" c').asList() == ['"a b"', 'c']
        assert p('a "b c"').asList() == ['a', '"b c"']
        assert p('a "b c" d').asList() == ['a', '"b c"', 'd']

        # +- cases
        assert p('+a').asList() == [['+', 'a']]
        assert p('-a').asList() == [['-', 'a']]
        assert p('+"a  b"').asList() == [['+', '"a  b"']]
        assert p('-"a  b"').asList() == [['-', '"a  b"']]
        assert p('b +a').asList() == ['b', ['+', 'a']]
        assert p('b -a').asList() == ['b', ['-', 'a']]
        assert p('"b +a"').asList() == ['"b +a"']
        assert p('"b -a"').asList() == ['"b -a"']
        assert p('b+a').asList() == ['b+a']
        assert p('b-a').asList() == ['b-a']
        assert p('"b+a"').asList() == ['"b+a"']
        assert p('"b-a"').asList() == ['"b-a"']
        assert p('+a b c').asList() == [['+', 'a'], 'b', 'c']
        assert p('-a b c').asList() == [['-', 'a'], 'b', 'c']
        assert p('+a "b c"').asList() == [['+', 'a'], '"b c"']
        assert p('-a "b c"').asList() == [['-', 'a'], '"b c"']
        assert p('a   b +c').asList() == ['a', 'b', ['+', 'c']]
        assert p('a   b -c').asList() == ['a', 'b', ['-', 'c']]
        assert p('a   "b +c"').asList() == ['a', '"b +c"']
        assert p('a   "b -c"').asList() == ['a', '"b -c"']
        assert p('+a -b +c').asList() == [['+', 'a'], ['-', 'b'], ['+', 'c']]
        assert p('-a +b -c').asList() == [['-', 'a'], ['+', 'b'], ['-', 'c']]
        assert p('+a -"b +c"').asList() == [['+', 'a'], ['-', '"b +c"']]
        assert p('-a +"b -c"').asList() == [['-', 'a'], ['+', '"b -c"']]
        assert p('+a-b +c').asList() == [['+', 'a-b'], ['+', 'c']]
        assert p('-a+b -c').asList() == [['-', 'a+b'], ['-', 'c']]
        assert p('+"a-b" +c').asList() == [['+', '"a-b"'], ['+', 'c']]
        assert p('-"a+b" -c').asList() == [['-', '"a+b"'], ['-', 'c']]
        assert p('+a-"b +c"').asList() == [['+', 'a-"b'], ['+', 'c"']]
        assert p('-a+"b -c"').asList() == [['-', 'a+"b'], ['-', 'c"']]
        assert p('+a   -b+c').asList() == [['+', 'a'], ['-', 'b+c']]
        assert p('-a   +b-c').asList() == [['-', 'a'], ['+', 'b-c']]
        assert p('+a   -"b+c"').asList() == [['+', 'a'], ['-', '"b+c"']]
        assert p('-a   +"b-c"').asList() == [['-', 'a'], ['+', '"b-c"']]
        assert p('+a   "-b+c"').asList() == [['+', 'a'], '"-b+c"']
        assert p('-a   "+b-c"').asList() == [['-', 'a'], '"+b-c"']

    def test_parse_query(self):
        f = parser.fields

        assert parser.parse_query('ab') == {
            'bool': {
                'should': [
                    {
                        'multi_match': {
                            'query': 'ab',
                            'fields': f,
                            'boost': 10,
                        }
                    },
                    {
                        'multi_match': {
                            'query': 'ab',
                            'fields': f,
                            'fuzziness': 1,
                            'prefix_length': 1,
                        }
                    },
                ],
                'must_not': [{'match': {'archived': True}}],
            }
        }
        assert parser.parse_query('"a b"') == {
            'bool': {
                'should': [
                    {
                        'multi_match': {
                            'query': 'a b',
                            'fields': f,
                            'type': 'phrase',
                            'boost': 10,
                        }
                    },
                ],
                'must_not': [{'match': {'archived': True}}],
            }
        }
        assert parser.parse_query('+ab') == {
            'bool': {
                'must': [
                    {
                        'multi_match': {
                            'query': 'ab',
                            'fields': f,
                            'boost': 10,
                        }
                    },
                    {
                        'multi_match': {
                            'query': 'ab',
                            'fields': f,
                            'fuzziness': 1,
                            'prefix_length': 1,
                        }
                    },
                ],
                'must_not': [{'match': {'archived': True}}],
            }
        }
        assert parser.parse_query('+"a b"') == {
            'bool': {
                'must': [
                    {
                        'multi_match': {
                            'query': 'a b',
                            'fields': f,
                            'type': 'phrase',
                            'boost': 10,
                        }
                    },
                ],
                'must_not': [{'match': {'archived': True}}],
            }
        }
        assert parser.parse_query('-a') == {
            'bool': {
                'must_not': [
                    {
                        'multi_match': {
                            'query': 'a',
                            'fields': f,
                            'boost': 1,
                        }
                    },
                    {'match': {'archived': True}},
                ],
            }
        }
        assert parser.parse_query('-"a b"') == {
            'bool': {
                'must_not': [
                    {
                        'multi_match': {
                            'query': 'a b',
                            'fields': f,
                            'type': 'phrase',
                            'boost': 1,
                        }
                    },
                    {'match': {'archived': True}},
                ],
            }
        }
        assert parser.parse_query('"a" +"b"') == {
            'bool': {
                'must': [
                    {
                        'multi_match': {
                            'query': 'b',
                            'fields': f,
                            'type': 'phrase',
                            'boost': 10,
                        }
                    },
                ],
                'should': [
                    {
                        'multi_match': {
                            'query': 'a',
                            'fields': f,
                            'type': 'phrase',
                            'boost': 10,
                        }
                    },
                ],
                'must_not': [{'match': {'archived': True}}],
            }
        }
        assert parser.parse_query('"a" -"b"') == {
            'bool': {
                'must_not': [
                    {
                        'multi_match': {
                            'query': 'b',
                            'fields': f,
                            'type': 'phrase',
                            'boost': 1,
                        }
                    },
                    {'match': {'archived': True}},
                ],
                'should': [
                    {
                        'multi_match': {
                            'query': 'a',
                            'fields': f,
                            'type': 'phrase',
                            'boost': 10,
                        }
                    },
                ],
            }
        }
        assert parser.parse_query('+"a" -"b"') == {
            'bool': {
                'must': [
                    {
                        'multi_match': {
                            'query': 'a',
                            'fields': f,
                            'type': 'phrase',
                            'boost': 10,
                        }
                    },
                ],
                'must_not': [
                    {
                        'multi_match': {
                            'query': 'b',
                            'fields': f,
                            'type': 'phrase',
                            'boost': 1,
                        }
                    },
                    {'match': {'archived': True}},
                ],
            }
        }

    def test_transform_to_dsl(self):
        f = parser.fields

        assert parser.transform_to_dsl(['a']) == [
            {'multi_match': {'query': 'a', 'fields': f, 'boost': 10}},
        ]
        assert parser.transform_to_dsl(['ab']) == [
            {'multi_match': {'query': 'ab', 'fields': f, 'boost': 10}},
            {'multi_match': {
                'query': 'ab',
                'fields': f,
                'fuzziness': 1,
                'prefix_length': 1,
            }},
        ]
        assert parser.transform_to_dsl(['"a"']) == [
            {'multi_match': {
                'query': 'a',
                'fields': f,
                'type': 'phrase',
                'boost': 10,
            }},
        ]
        assert parser.transform_to_dsl(['a'], has_fuzziness=False) == [
            {'multi_match': {'query': 'a', 'fields': f, 'boost': 1}},
        ]
        assert parser.transform_to_dsl(['"a"'], has_fuzziness=False) == [
            {'multi_match': {
                'query': 'a',
                'fields': f,
                'type': 'phrase',
                'boost': 1,
            }},
        ]
        assert parser.transform_to_dsl(['ab', '"b"']) == [
            {'multi_match': {'query': 'ab', 'fields': f, 'boost': 10}},
            {'multi_match': {
                'query': 'ab',
                'fields': f,
                'fuzziness': 1,
                'prefix_length': 1,
            }},
            {'multi_match': {
                'query': 'b',
                'fields': f,
                'type': 'phrase',
                'boost': 10,
            }},
        ]
        assert parser.transform_to_dsl(['"a"', 'bc']) == [
            {'multi_match': {
                'query': 'a',
                'fields': f,
                'type': 'phrase',
                'boost': 10,
            }},
            {'multi_match': {'query': 'bc', 'fields': f, 'boost': 10}},
            {'multi_match': {
                'query': 'bc',
                'fields': f,
                'fuzziness': 1,
                'prefix_length': 1,
            }},
        ]
        assert parser.transform_to_dsl(['ab', '"b"'], has_fuzziness=False) == [
            {'multi_match': {'query': 'ab', 'fields': f, 'boost': 1}},
            {'multi_match': {
                'query': 'b',
                'fields': f,
                'type': 'phrase',
                'boost': 1,
            }},
        ]
        assert parser.transform_to_dsl(['"a"', 'bc'], has_fuzziness=False) == [
            {'multi_match': {
                'query': 'a',
                'fields': f,
                'type': 'phrase',
                'boost': 1,
            }},
            {'multi_match': {'query': 'bc', 'fields': f, 'boost': 1}},
        ]
        assert parser.transform_to_dsl(['"a']) == [
            {'multi_match': {'query': '"a', 'fields': f, 'boost': 10}},
            {'multi_match': {
                'query': '"a',
                'fields': f,
                'fuzziness': 1,
                'prefix_length': 1,
            }},
        ]
        assert parser.transform_to_dsl(['a"']) == [
            {'multi_match': {'query': 'a"', 'fields': f, 'boost': 10}},
            {'multi_match': {
                'query': 'a"',
                'fields': f,
                'fuzziness': 1,
                'prefix_length': 1,
            }},
        ]

    def test_get_fuzziness(self):
        with pytest.raises(AssertionError):
            parser.get_fuzziness('')
        assert parser.get_fuzziness('a') == 0
        assert parser.get_fuzziness('ab') == 1
        assert parser.get_fuzziness('abc') == 1
        assert parser.get_fuzziness('abcd') == 2
        assert parser.get_fuzziness('abcde') == 2
        assert parser.get_fuzziness('abcdef') == 2
