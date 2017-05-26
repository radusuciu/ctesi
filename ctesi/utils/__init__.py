from collections import OrderedDict, namedtuple
import csv

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
    if 'diff_mods' in search_params:
        diff_mods = search_params['diff_mods']
    else:
        return None

    valid_mods = []

    for mod in diff_mods:
        if float(mod['mass']) > 0 and validate_protein(mod['aa']):
            mod['aa'] = ''.join(set(mod['aa']))
            valid_mods.append(mod)

    return { 'diff_mods': valid_mods }



class CimageParams:

    CimageParam = namedtuple('CimageParam', ['comment', 'key', 'value'])
    _comment_char = '!'

    def __init__(self, path=None, data=None):
        self.data = data or OrderedDict()
        self._light = None
        self._heavy = None

        if path:
            self.read_file(path)


    @property
    def light(self):
        if self._light is None:
            self.parse_chem_tables()

        return self._light


    @light.setter
    def light(self, light):
        self._light = light


    @property
    def heavy(self):
        if self._heavy is None:
            self.parse_chem_tables()
            
        return self._heavy


    @heavy.setter
    def heavy(self, heavy):
        self._heavy = heavy


    @property
    def chem_headers(self):
        return list(next(iter(self.light.values())).keys())


    def read(self, raw):
        # reset rather than append
        self.data = OrderedDict()

        for line in raw:
            if line.startswith(self._comment_char):
                comment = line.strip(self._comment_char + ' ')
            else:
                (key, value) = map(str.strip, line.split('='))
                self.data[key] = self.CimageParam(comment, key, value)

        self.parse_chem_tables()


    def read_file(self, path):
        with open(str(path)) as f:
            raw = f.read().splitlines()

        self.read(raw)
        return self


    def parse_chem_tables(self):
        self.light = self._parse_chem_table(self.data['light.chem.table'].value)
        self.heavy = self._parse_chem_table(self.data['heavy.chem.table'].value)
        return self


    def _parse_chem_table(self, path):
        table = OrderedDict()

        with open(path) as f:
            reader = csv.reader(f, delimiter='\t')
            headers = next(reader)[1:]

            for row in reader:
                if row:
                    table[row[0]] = OrderedDict(zip(headers, row[1:]))

        return table

    def write_chem_tables(self, light_path=None, heavy_path=None):
        self._write_chem_table(light_path or self['light.chem.table'], self.light)
        self._write_chem_table(heavy_path or self['heavy.chem.table'], self.heavy)
        return self


    def _write_chem_table(self, path, data):
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f, delimiter='\t', quoting=csv.QUOTE_NONE)

            headers = [''] + list(data['A'].keys())
            writer.writerow(headers)

            for aa, counts in data.items():
                writer.writerow([aa] + list(counts.values()))


    def to_string(self):
        lines = []

        for item in self.data:
            param = self.data[item]

            lines.append('{} {} {}\n{} = {}'.format(
                self._comment_char * 3,
                param.comment,
                self._comment_char*3,
                param.key,
                param.value
            ))

        return '\n'.join(lines)


    def write_file(self, path):
        if not self.data:
            return

        with open(str(path), 'w') as f:
            f.write(self.to_string())

        return self


    def __getitem__(self, key):
        return self.data[key].value
