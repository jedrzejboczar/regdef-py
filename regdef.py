#!/usr/bin/env python3

import io
import re
import copy
import json
import math


class Register:
    """
    Simple class for visualisation of register field values.
    """
    def __init__(self, group_names, group_lengths, positions=None, name='NONE', value=0):
        """Basic constructor, it is more convenient to use from_xxx() classmethods."""
        # check if groups are consistent
        #  assert sum(group_lengths) % 8 == 0, \
        #      'register has to have number of bits being multiple of 8 (group_lengths=%s)' \
        #      % group_lengths
        assert len(group_names) == len(group_lengths), \
            'number of names and number of groups are different'
        assert value < 2**(sum(group_lengths)), \
            'value is greater than maximum defined by group_lengths (%d > 2**%d)' \
            % (value, sum(group_lengths))
        # save values
        self.name = name
        self.value = value
        self.names = group_names
        self.lengths = group_lengths
        self.positions = positions

    @classmethod
    def from_value(cls, value, group_names=None, group_lengths=None, **kwargs):
        """
        Create a result from given value. If not other information is provided,
        then this method will try to deduct them from the given value.
        """
        # set default values if not provided
        if group_lengths is None:
            n_bytes = int((math.floor(math.log2(value) / 8) + 1))
            group_lengths = [1] * (n_bytes * 8)
        if group_names is None:
            group_names = ['_'] * len(group_lengths)
        return cls(group_names, group_lengths, value=value, **kwargs)

    @classmethod
    def from_specs(cls, fields_specs, **kwargs):
        """
        Create the register using special format string.

        The format consists of register fields separated by whitespace.
        Each field is in one of formats (positions start from 0 being LSB):
        NAME:BIT_POSITION or NAME:START_POSITION:END_POSITION or NAME:@NUM_BITS

        The bits can go up or down, but be consistent!
        START_POSITION:END_POSITION can be reversed

        e.g:
        Reserved:31:17 COUNTFLAG:@1 Reserved:@13 CLKSOURCE:2 TICKINT:1 ENABLE:0
        Bits 31 to 17  One bit      13 bits      Bit 2       Bit 1     Bit 0
        """
        names = []
        lengths = []
        positions = []
        for field_str in fields_specs.split():
            atoms = field_str.split(':')
            name = atoms[0]
            position = None
            if len(atoms) == 2:
                if atoms[1].startswith('@'):  # NAME:@NUM_BITS
                    length = int(atoms[1][1:])
                else:  # NAME:BIT_POSITION
                    length = 1
                    position = int(atoms[1])
            elif len(atoms) == 3:  # NAME:START_POSITION:END_POSITION
                start, end = int(atoms[1]), int(atoms[2])
                # we will make it that we always have HIGHER:LOWER
                if end > start:
                    start, end = end, start
                length = abs(end - start) + 1
                position = (start, end)
            else:
                print('ERROR: ignoring field "%s"' % field_str)
                continue
            names.append(name)
            lengths.append(length)
            positions.append(position)

        # TODO: reinterpret position data

        # if not even two positions have been specified, do not assume order
        n_positions = sum(pos is not None for pos in positions)
        #  assert n_positions > 1, 'At least 2 positions are required to assume order of bits'
        if n_positions < 2:
            # assume increasing
            #  print('Assuming increasing order (from 0) because only %d positions were given' % n_positions)
            positions_given = (0, 1)
        else:
            positions_given = list(filter(None, positions))

        # for min/max on either int or a tuple
        def min_any(arg):
            if isinstance(arg, tuple):
                return min(arg)
            else:
                return arg
        def max_any(arg):
            if isinstance(arg, tuple):
                return max(arg)
            else:
                return arg

        # assume order
        p1, p2 = positions_given[:2]
        # simplify if tuples
        p1 = min_any(p1)
        p2 = min_any(p2)
        assert p1 != p2, 'Could not assume order, positions: %s' % positions
        assuming_decreasing = p1 > p2

        # sort positions based on the assumed order
        positions_sorted = []
        for pos in positions:
            if isinstance(pos, tuple):
                ps = (min(pos), max(pos))
                positions_sorted.append(tuple(reversed(ps)) if assuming_decreasing else ps)
            else:
                positions_sorted.append(pos)
        positions = positions_sorted

        # make the list be always increasing for consistency
        if assuming_decreasing:
            positions = list(reversed(positions))
            lengths = list(reversed(lengths))
            names = list(reversed(names))

        # fill the Nones
        if positions[0] is None:
            if lengths[0] == 1:
                positions[0] = 0
            else:
                positions[0] = (0, lengths[0] - 1)
        for i in range(0, len(positions)):
            if positions[i] is None:
                prev = max_any(positions[i - 1])
                if lengths[i] == 1:
                    positions[i] = prev + 1
                else:
                    positions[i] = (prev + 1, prev + 1 + lengths[i] - 1)

        # test if everything is consistent, i.e. all increasing or all decreasing
        # flatten the position data
        positions_flat = []
        for pos in positions:
            if isinstance(pos, tuple):
                positions_flat.append(max(pos))
                positions_flat.append(min(pos))
            else:
                positions_flat.append(pos)
        descreasing = all(earlier > later for earlier, later in zip(positions_flat, positions_flat[1:]))

        # if it was not decreasing than check if it is increasing
        if not descreasing:
            positions_flat = []
            for pos in positions:
                if isinstance(pos, tuple):
                    positions_flat.append(min(pos))
                    positions_flat.append(max(pos))
                else:
                    positions_flat.append(pos)
            increasing = all(earlier < later for earlier, later in zip(positions_flat, positions_flat[1:]))

            assert increasing, 'Positions list was neither increasing nor descreasing: %s' % positions

        # ok, now fill in the missing holes in positions with reserved areas
        assert len(names) == len(lengths) == len(positions), 'Yyy...something is not yes...'
        new_names = []
        new_lengths = []
        new_positions = []
        prev_max = -1
        for i in range(len(positions)):
            if min_any(positions[i]) - (prev_max + 1) > 0:
                new_names.append('_')
                new_lengths.append(min_any(positions[i]) - (prev_max + 1))
                if new_lengths[-1] == 1:
                    new_positions.append(prev_max + 1)
                else:
                    new_positions.append((prev_max + 1, min_any(positions[i]) - 1))
            new_names.append(names[i])
            new_lengths.append(lengths[i])
            new_positions.append(positions[i])
            prev_max = max_any(positions[i])

        names = new_names
        lengths = new_lengths
        positions = new_positions

        # create register object
        return cls(names, lengths, positions=positions, **kwargs)

    def set(self, value):
        self.value = value

    @property
    def n_bits(self):
        return sum(self.lengths)

    @property
    def bin(self):
        return '0b{bits:0>{n_bits}}'.format(
            bits=bin(self.value)[2:], n_bits=self.n_bits)

    @property
    def hex(self):
        return '0x{chars:0>{n_chars}}'.format(
            chars=hex(self.value)[2:], n_chars=self.n_bits//8)

    def pprint(self):
        print(self.repr_long())

    def repr_short(self):
        return 'Register(%d-bit, %s: %s)' % (self.n_bits, self.name, self.hex)

    def repr_long(self):
        ostream = io.StringIO()
        print('Register(%d-bit, %s):' % (self.n_bits, self.name), file=ostream)
        name_len = max([len(n) for n in self.names])
        #  bits = bin(self.value)[2:]
        i = 0
        for i in range(len(self.names)):
            group_name, group_len = self.names[i], self.lengths[i]
            group_value = self.bin[2:][i:i+group_len]
            if self.positions is None:
                endpos = self.n_bits-i-1
                startpos = endpos-group_len+1
            else:
                pos = self.positions[i]
                if isinstance(pos, tuple):
                    startpos, endpos = pos
                else:
                    startpos, endpos = pos, pos
            pos_str = '%d:%d' % (startpos, endpos)
            fmt = '  {pos:>5} {nbits:>3} │ {name:{name_len}}: {values}'
            text = fmt.format(name=group_name, name_len=name_len,
                              values=group_value, pos=pos_str,
                              nbits='#%d' % group_len)
            print(text, file=ostream)
            i += group_len
        text = ostream.getvalue()
        ostream.close()
        return text

    def __repr__(self):
        return self.repr_short()

    def get_reg_n(self):
        n = sum(self.lengths)
        valid_int_lengths = [8, 16, 32, 64]
        reg_n = None
        for l in valid_int_lengths:
            if l >= n:
                reg_n = l
                break
        assert reg_n is not None, \
            'Could not find an integer size that would hold %d bits' % n
        return reg_n

    def code_masks(self, address, prefix='',
                   reg_t=None, reg_n=None, address_t='uint8_t',
                   reserved_regex='reserved|RESERVED|_', cpp=True):
        """
        Generate C/C++ code for register definition

        reg_t - if present defines the type of variable used for register (no checks
                of variable size) higher priority than reg_n
        reg_n - if present defines the number of bits in integer used for register value
                else the value is taken automatically as the lowest that is enough
        address_t - type of variable that holds `address`
        prefix - added before union name
        reserved_regex - regex which, if matches on field name, makes the filed be treated
                         as reserved field - it is given no name
        little_endian - whether to generate for little endian target (changes bitfields order)
        cpp - whether to generate type definitions for C++ or for C
        """

        # find int size, variable length must be one of theses from stdint.h
        n = sum(self.lengths)
        if reg_t is None:
            if reg_n is None:
                reg_n = self.get_reg_n()
            assert reg_n >= n, 'Cannot hold %d bits in %d-bit integer' % (n, reg_n)
            reg_t = 'uint{n}_t'.format(n=reg_n)

        reg_name = self.name.upper()
        #  reg_name = self.name if cpp else self.name.upper()
        #  field_name = lambda name: name if cpp else name.upper()
        field_name = lambda name: name.upper()

        if cpp:
            address_templ = 'constexpr {addr_t} {name}_ADDRESS = {addr}U;'
            nbits_templ = 'constexpr size_t {name}_NBITS = {n}U;'
            field_pos_templ = 'constexpr {reg_t} {name}_{field}_POS = {pos}U;'
            field_mask_templ = 'constexpr {reg_t} {name}_{field}_MASK = 0b{bits}U << {name}_{field}_POS;'
        else:
            address_templ = '#define {name}_ADDRESS  (({addr_t}) ({addr}U))'
            nbits_templ = '#define {name}_NBITS   ({n}U)'
            field_pos_templ = '#define {name}_{field}_POS   ({pos}U)'
            field_mask_templ = '#define {name}_{field}_MASK   (0b{bits}U << {name}_{field}_POS)'

        lines = [
            address_templ.format(name=prefix + reg_name, addr_t=address_t, addr=address),
            nbits_templ.format(name=prefix + reg_name, n=n),
        ]

        # generate fields definitions
        next_pos = 0
        # reverse to stat from the ones for bit 0
        #  for n, name in zip(reversed(self.lengths), reversed(self.names)):
        for n, name in zip(self.lengths, self.names):
            pos = next_pos
            next_pos = pos + n
            # ignore reserved fields
            if re.match(reserved_regex, name):
                continue
            lines.append(field_pos_templ.format(name=reg_name, field=field_name(name), pos=pos, reg_t=reg_t))
            bits = n * '1'
            lines.append(field_mask_templ.format(name=reg_name, field=field_name(name), reg_t=reg_t, bits=bits))

        # TODO: alignment

        return '\n'.join(lines)

    ### ALSO: this just won't work well, bitfields are just too undefined
    ###  e.g. https://stackoverflow.com/questions/6043483/why-bit-endianness-is-an-issue-in-bitfields
    def ccode(self, address,
              reg_t=None, reg_n=None, address_t='uint8_t', prefix='',
              reserved_regex='reserved|RESERVED|_', cpp=False):
        """
        Generate C/C++ code for register definition

        reg_t - if present defines the type of variable used for register (no checks
                of variable size) higher priority than reg_n
        reg_n - if present defines the number of bits in integer used for register value
                else the value is taken automatically as the lowest that is enough
        address_t - type of variable that holds `address`
        prefix - added before union name
        reserved_regex - regex which, if matches on field name, makes the filed be treated
                         as reserved field - it is given no name
        cpp - whether to generate type definitions for C++ or for C
        """

        # find int size, variable length must be one of theses from stdint.h
        n = sum(self.lengths)
        if reg_t is None:
            if reg_n is None:
                reg_n = self.get_reg_n()
            assert reg_n >= n, 'Cannot hold %d bits in %d-bit integer' % (n, reg_n)
            reg_t = 'uint{n}_t'.format(n=reg_n)

        if cpp:
            template = """
struct {name} {{
    static constexpr {addr_t} address{addr_arr} = {addr};
    static constexpr size_t n_bits = {n};
{accessor}
{initialiser}
{struct}
}};
            """.strip()

            accessor_templ = """    inline {reg_t} raw() {{
        return {raw};
    }}
            """.rstrip()

            initialiser_templ = """
static {name} from_raw({reg_t} raw) {{
    return {{
{initialisers}
    }};
}}
            """.strip()

        else:  # C code
            template = """
{addr}
#define {name}_N_BITS    ({n})
{accessor}
{initialiser}
typedef struct {name} {{
{struct}
}} {name};
            """.strip()

            accessor_templ = """
#define {name}_RAW(reg)   ({raw})
            """.strip()

            initialiser_templ = """
#define {name}_FROM_RAW(raw) (({name}) {{ {initialisers} }})
            """.strip()

        # assemble struct code from bitfields
        struct_templ = '{reg_t} {name}:{n};'
        field_mask_templ = '({reg}{field} << {pos}U)'
        init_field_templ = '.{field} = ((raw) & (0b{bits}U << {pos}U)) >> {pos}U'

        lines = []
        field_masks = []
        init_fields = []
        next_pos = 0
        for n, name in zip(self.lengths, self.names):  # reverse to stat from the ones for bit 0
            pos = next_pos
            next_pos = pos + n
            # remove names from reserved fields
            reserved = re.match(reserved_regex, name)
            lines.append(1 * 4 * ' ' + struct_templ.format(reg_t=reg_t, name=name if not reserved else '', n=n))
            if not reserved:
                # accessor for the field
                field_masks.append(field_mask_templ.format(field=name, pos=pos, reg='' if cpp else 'reg.'))
                init_fields.append(init_field_templ.format(field=name, pos=pos, bits='1' * n))

        struct_code = '\n'.join(lines)

        # accessor
        raw = ' | '.join(field_masks)
        reg_name = prefix + self.name
        accessor = accessor_templ.format(name=reg_name, raw=raw, reg_t=reg_t)
        if cpp:
            accessor = '\n%s\n' % accessor

        # initialiser
        join_str = ',\n' if cpp else ', '
        init_fields = ',\n'.join(2 * 4 * ' ' + s for s in init_fields) if cpp else ', '.join(init_fields)
        initialiser = initialiser_templ.format(name=reg_name, reg_t=reg_t,
                                               initialisers=init_fields)
        if cpp:
            initialiser = '\n'.join(4 * ' ' + s for s in initialiser.split('\n'))

        # add address (one or many)
        if not isinstance(address, list):
            addr_arr = ''
            if cpp:
                addr = address
            else:
                addr = '#define {name}_ADDRESS   ({addr})'.format(name=reg_name, addr=address)
        else:
            # we have many addresses
            if cpp:
                addr_arr = '[%d]' % len(address)
                addr = '{%s}' % (', '.join('%s' % a for a in address))
            else:
                addr_arr = ''
                addr = []
                for i, a in enumerate(address):
                    atmp = '#define {name}_ADDRESS_{i}   ({addr})'
                    addr.append(atmp.format(name=reg_name, i=i, addr=a))
                addr = '\n'.join(addr)

        return template.format(
            name=reg_name,
            addr_t=address_t,
            addr_arr=addr_arr,
            addr=addr,
            n=sum(self.lengths),
            reg_t=reg_t,
            struct=struct_code,
            accessor=accessor if len(field_masks) > 0 else '',
            initialiser=initialiser if len(field_masks) > 0 else '',
        )

def parse_regdef_json(file_name, comments=True, **ccode_kwargs):
    """
    Generates C code for register definitions given a file with definition of registers
    The register fields description is the same as for Register.from_specs().
    The syntax of JSON file is as follows and has 2 variants:

"GCONF1": {
    "address": "0x00",
    "def": "reserved:11 lock_gconf:10 shaft2:9 shaft1:8 test_mode:7 reserved:6:4 poscmp_enable:3 reserved:2:0",
},
"GCONF2": {
    "address": "0x00",
    "defs": [
        "reserved:11",
        "lock_gconf:10",
        "shaft2:9",
        "shaft1:8",
        "test_mode:7",
        "reserved:6:4",
        "poscmp_enable:3",
        "reserved:2:0"
    ]
}

    All other fields are optional and are passed to the Register.ccode() method.

    ccode_kwargs - passed to ccode, overwritten by configurations in json
    """
    with open(file_name) as fp:
        reg_defs = json.load(fp)
    #  __import__('pprint').pprint(reg_defs)

    code = []
    registers = []
    for reg_name, reg_def in reg_defs.items():
        # ignore empty nodes or ones with name starting with //
        if reg_name and reg_name.strip().startswith('//'):
            if comments:
                code.append(reg_name)
            continue
        if not reg_name or not reg_def:
            continue
        if 'defs' in reg_def.keys():
            specs = ' '.join(reg_def.pop('defs'))
        else:
            specs = reg_def.pop('def')

        address = reg_def.pop('address')

        # construct the kwargs by taking defaults from ccode_kwargs
        # and then overwriting the ones that were defined in json
        kwargs = copy.copy(ccode_kwargs)
        kwargs.update(reg_def)

        reg = Register.from_specs(specs, name=reg_name)
        code.append(reg.ccode(address, **kwargs))
        #  code.append(reg.code_masks(address, **kwargs))

        registers.append({'name': reg_name, 'address': address, 'reg': reg})

    return code, registers

################################################################################

def test1():
    specs = {
        'GCONF': 'reserved:11 lock_gconf:10 shaft2:9 shaft1:8 test_mode:7 reserved:6:4 poscmp_enable:3 reserved:2:0'
    }
    regs = [Register.from_specs(s, name=name) for name, s in specs.items()]
    reg = regs[0]
    reg.pprint()
    print()
    print(reg.ccode(0x00))
    print()
    print(reg.ccode(0x00, reg_n=32))
    print()
    print(reg.ccode(0x00, reg_t='uint_fast32_t'))

    code = parse_regdef_json('regdef.json')
    for c in code:
        print('//' * 10)
        print(c)


def test2():
    #  code = parse_regdef_json('tmc5041.regdef.json', reg_n=32)
    code = parse_regdef_json('regdef.json', reg_n=32)
    for c in code:
        print()
        print(c)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Generates code/shows registers map defined in JSON file.'
        + ' Code requires C99/C++20.')
    parser.add_argument('command', choices=['show', 'code'],
                        help='Either show parsed, human-readable registers description,'
                        + ' or generate code')
    parser.add_argument('-C', action='store_true',
                        help='Generated C code instead of C++')
    parser.add_argument('-c', '--no-comments', action='store_true',
                        help='Do not add keys starting with // to generated code')
    parser.add_argument('-p', '--prefix', default='',
                        help='Prefix string for the generated code')
    parser.add_argument('-n', '--n-bits', nargs=1, default=32, type=int,
                        help='Number of bits used for uintN_t variables for register type')
    parser.add_argument('regdef', help='Register description json file')
    args = parser.parse_args()

    code, registers = parse_regdef_json(args.regdef, reg_n=args.n_bits,
                                        comments=not args.no_comments,
                                        prefix=args.prefix, cpp=not args.C)

    if args.command == 'show':
        for register in registers:
            print('ADDRESS = %s' % register['address'])
            register['reg'].pprint()
    else:
        for c in code:
            print(c)
            if not c.strip().startswith('//'):
                print()


if __name__ == "__main__":
    main()
