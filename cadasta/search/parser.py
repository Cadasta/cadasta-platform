import pyparsing


# Specify the ES fields for all ES types for full-text search
fields = ['type', 'name', 'attributes.value', 'tenure_attributes.value',
          'tenure_type_id', 'description', 'original_file', 'mime_type']

# pyparsing objects
fuzzy = pyparsing.Regex(r'\S+')
exact = pyparsing.QuotedString('"', unquoteResults=False)
term = exact | fuzzy
must_term = pyparsing.Group('+' + term)
must_not_term = pyparsing.Group('-' + term)
token = must_term | must_not_term | term
query = pyparsing.OneOrMore(token)


def parse_query(raw_query_str):
    """This function takes the raw UI search query string, parses it, then
    generates and returns the 'bool' JSON object for the 'query' DSL field."""

    # Parse query string into tokens and sort them into buckets
    tokens = query.parseString(raw_query_str).asList()
    must_terms = []
    must_not_terms = []
    should_terms = []
    for token in tokens:
        if isinstance(token, list):
            if token[0] == '-':
                must_not_terms.append(token[1])
            else:
                assert token[0] == '+'
                must_terms.append(token[1])
        else:
            should_terms.append(token)

    # Go through each bucket and generate the 'bool' clause lists
    must_dsl = transform_to_dsl(must_terms)
    must_not_dsl = transform_to_dsl(must_not_terms, has_fuzziness=False)
    should_dsl = transform_to_dsl(should_terms)

    # Add clause to remove archived resources
    must_not_dsl.append({'match': {'archived': True}})

    # Construct then return the complete 'bool' DSL
    dsl = {'bool': {'must_not': must_not_dsl}}
    if must_dsl:
        dsl['bool']['must'] = must_dsl
    if should_dsl:
        dsl['bool']['should'] = should_dsl
    return dsl


def transform_to_dsl(terms, has_fuzziness=True):
    dsl = []
    for term in terms:
        # Exact phrase clause
        if term[0] == '"' and term[-1] == '"':
            dsl.append({'multi_match': {
                'query': term[1:-1],
                'fields': fields,
                'type': 'phrase',
                'boost': 10 if has_fuzziness else 1,
            }})

        # Fuzzy term
        else:
            # Exact match clause
            dsl.append({'multi_match': {
                'query': term,
                'fields': fields,
                'boost': 10 if has_fuzziness else 1,
            }})

            # Fuzzy match clause
            if has_fuzziness and len(term) > 1:
                dsl.append({'multi_match': {
                    'query': term,
                    'fields': fields,
                    'fuzziness': get_fuzziness(term),
                    'prefix_length': 1,
                }})
    return dsl


def get_fuzziness(term):
    assert len(term) > 0
    if len(term) == 1:
        return 0
    elif len(term) < 4:
        return 1
    else:
        return 2
