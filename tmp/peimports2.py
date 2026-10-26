import struct, sys

def rva_to_off(data, rva, sections):
    for name, vaddr, vsize, rawptr, rawsize in sections:
        if vaddr <= rva < vaddr + max(vsize, rawsize):
            return rawptr + (rva - vaddr)
    return None

def parse_pe(path):
    data = open(path, 'rb').read()
    e_lfanew = struct.unpack_from('<I', data, 0x3c)[0]
    coff = e_lfanew + 4
    num_sections = struct.unpack_from('<H', data, coff+2)[0]
    opt_size = struct.unpack_from('<H', data, coff+16)[0]
    opt = coff + 20
    magic = struct.unpack_from('<H', data, opt)[0]
    ddir = opt + (112 if magic == 0x20b else 96)
    sec_off = opt + opt_size
    sections = []
    for i in range(num_sections):
        o = sec_off + i*40
        name = data[o:o+8].rstrip(b'\x00').decode('ascii','replace')
        vsize, vaddr, rawsize, rawptr = struct.unpack_from('<IIII', data, o+8)
        sections.append((name, vaddr, vsize, rawptr, rawsize))
    return data, sections, ddir

def imports(path):
    data, sections, ddir = parse_pe(path)
    import_rva, _ = struct.unpack_from('<II', data, ddir + 8)
    off = rva_to_off(data, import_rva, sections)
    res = []
    i = 0
    while True:
        o = off + i*20
        ilt_rva, _, _, name_rva, _ = struct.unpack_from('<IIIII', data, o)
        if ilt_rva == 0 and name_rva == 0:
            break
        noff = rva_to_off(data, name_rva, sections)
        end = data.index(b'\x00', noff)
        dll = data[noff:end].decode('ascii','replace')
        # walk thunks
        toff = rva_to_off(data, ilt_rva, sections)
        j = 0
        funcs = []
        while True:
            if data[opt_bits(path) == 64: 0]:
                pass
            # determine 64-bit
            entry = struct.unpack_from('<Q', data, toff + j*8)[0] if is64(path) else struct.unpack_from('<I', data, toff + j*4)[0]
            if entry == 0:
                break
            if (is64(path) and entry & (1<<63)) or ((not is64(path)) and entry & (1<<31)):
                funcs.append(('ord', entry & 0xffff))
            else:
                eoff = rva_to_off(data, entry, sections)
                hint = struct.unpack_from('<H', data, eoff)[0]
                end2 = data.index(b'\x00', eoff+2)
                funcs.append(('name', data[eoff+2:end2].decode('ascii','replace')))
            j += 1
        res.append((dll, funcs))
        i += 1
    return res

def is64(path):
    data, sections, ddir = parse_pe(path)
    e_lfanew = struct.unpack_from('<I', data, 0x3c)[0]
    coff = e_lfanew + 4
    opt = coff + 20
    magic = struct.unpack_from('<H', data, opt)[0]
    return magic == 0x20b

def opt_bits(path):
    return 64 if is64(path) else 32

def exports(path):
    data, sections, ddir = parse_pe(path)
    exp_rva, _ = struct.unpack_from('<II', data, ddir)
    if exp_rva == 0:
        return set()
    off = rva_to_off(data, exp_rva, sections)
    nfuncs, nnames = struct.unpack_from('<II', data, off+20)[0], struct.unpack_from('<II', data, off+24)[0]
    names_rva = struct.unpack_from('<I', data, off+32)[0]
    noff = rva_to_off(data, names_rva, sections)
    out = set()
    for i in range(nnames):
        nr = struct.unpack_from('<I', data, noff + i*4)[0]
        e = rva_to_off(data, nr, sections)
        end = data.index(b'\x00', e)
        out.add(data[e:end].decode('ascii','replace'))
    return out

if __name__ == '__main__':
    target = sys.argv[1]
print('== imports of', target, '==')
dep_exports = {}
for dll, funcs in imports(target):
    print(f'\n{dll} ({len(funcs)} imports)')
    named = [f[1] for f in funcs if f[0]=='name']
    ords = [f[1] for f in funcs if f[0]=='ord']
    print('  named:', ', '.join(named[:40]))
    if ords:
        print('  ordinals:', ords[:40])
