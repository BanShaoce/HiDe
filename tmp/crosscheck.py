import struct

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
    return data, sections, ddir, magic

def imports(path):
    data, sections, ddir, magic = parse_pe(path)
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
        toff = rva_to_off(data, ilt_rva, sections)
        j = 0
        funcs = []
        while True:
            if magic == 0x20b:
                entry = struct.unpack_from('<Q', data, toff + j*8)[0]
            else:
                entry = struct.unpack_from('<I', data, toff + j*4)[0]
            if entry == 0:
                break
            if (magic == 0x20b and entry & (1<<63)) or (magic != 0x20b and entry & (1<<31)):
                funcs.append(('ord', entry & 0xffff))
            else:
                eoff = rva_to_off(data, entry, sections)
                end2 = data.index(b'\x00', eoff+2)
                funcs.append(('name', data[eoff+2:end2].decode('ascii','replace')))
            j += 1
        res.append((dll, funcs))
        i += 1
    return res

def exports(path):
    data, sections, ddir, magic = parse_pe(path)
    exp_rva, _ = struct.unpack_from('<II', data, ddir)
    if exp_rva == 0:
        return set()
    off = rva_to_off(data, exp_rva, sections)
    nnames = struct.unpack_from('<I', data, off+24)[0]
    names_rva = struct.unpack_from('<I', data, off+32)[0]
    noff = rva_to_off(data, names_rva, sections)
    out = set()
    for i in range(nnames):
        nr = struct.unpack_from('<I', data, noff + i*4)[0]
        e = rva_to_off(data, nr, sections)
        end = data.index(b'\x00', e)
        out.add(data[e:end].decode('ascii','replace'))
    return out

base = r'C:\Users\19457\anaconda3\envs\HiDe\Lib\site-packages\torch\lib'
for target in ['c10_cuda.dll', 'torch_cuda.dll']:
    print('====', target, '====')
    for dll, funcs in imports(base + '\\' + target):
        if dll.lower() not in ('c10.dll', 'cudart64_12.dll'):
            continue
        exp = exports(base + '\\' + dll)
        named = [f[1] for f in funcs if f[0] == 'name']
        missing = [n for n in named if n not in exp]
        print(f'{dll}: imported {len(named)} named, missing {len(missing)}')
        for m in missing[:50]:
            print('  MISSING', m)
