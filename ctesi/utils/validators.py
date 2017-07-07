VALID_NUCLEIC_ACIDS = 'ACGTNUKSYMWRBDHV'
VALID_AMINO_ACIDS = 'APBQCRDSETFUGVHWIYKZLXMN'
NUCLEIC_DELCHARS = str.maketrans({ord(c): None for c in VALID_NUCLEIC_ACIDS})
AA_DELCHARS = str.maketrans({ord(c): None for c in VALID_AMINO_ACIDS})


def validate_sequence(sequence, valid_chars):
    """Check whether sequence is valid nucleotide or protein sequence."""
    return len(sequence.upper().translate(valid_chars)) == 0

def validate_protein(sequence):
    return validate_sequence(sequence, AA_DELCHARS)

def validate_search_params(search_params):
    search_params['diff_mods'] = _validate_diff_mods(search_params.get('diff_mods'))
    search_params['options'] = _validate_options(search_params.get('options'))
    return {k: v for k, v in search_params.items() if v}

def _validate_diff_mods(diff_mods):
    if not diff_mods:
        return None

    valid_mods = []

    for mod in diff_mods:
        if float(mod['mass']) > 0 and validate_protein(mod['aa']):
            # make sure we aren't repeating amino acids
            mod['aa'] = ''.join(set(mod['aa']))
            valid_mods.append(mod)

            # keep composition keyed by uppercase amino acids for consistency
            mod['comp'] = dict(zip(
                map(str.upper, mod['comp'].keys()),
                mod['comp'].values()
            ))

            # make sure we have light and heavy options set
            mod['light'] = mod.get('light') or False
            mod['heavy'] = mod.get('heavy') or False

    return valid_mods


def _validate_options(options):
    if not options:
        return None

    accepted_options = {
        'minPeptidesPerProtein': int
    }

    valid_options = {}

    for k, v in options.items():
        if k in accepted_options.keys():
            try:
                valid_options[k] = accepted_options[k](v)
            except:
                pass

    return valid_options
