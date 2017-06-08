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
    if 'diff_mods' in search_params and search_params['diff_mods']:
        diff_mods = search_params['diff_mods']
    else:
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

    return { 'diff_mods': valid_mods }