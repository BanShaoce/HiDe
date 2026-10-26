import struct, sys
path = sys.argv[1]
data = open(path, 'rb').read()
# DOS header
e_lfanew = struct.unpack_from('<I', data, 0x3c)[0]
# PE signature + COFF header
sig = data[e_lfanew:e_lfanew+4]
assert sig == b'PE\x00\x00'
coff = e_lfanew + 4
machine = struct.unpack_from('<H', data, coff)[0]
num_sections = struct.unpack_from('<H', data, coff+2)[0]
opt_size = struct.unpack_from('<H', data, coff+16)[0]
opt = coff + 20
magic = struct.unpack_from('<H', data, opt)[0]
if magic == 0x20b:  # PE32+
    ddir_off = opt + 112
else:
    ddir_off = opt + 96
# Data directory 1 = import table
import_rva, import_size = struct.unpack_from('<II', data, ddir_off + 8)
# section headers
sec_off = opt + opt_size
sections = []
for i in range(num_sections):
    o = sec_off + i*40
    name = data[o:o+8].rstrip(b'\x00').decode('ascii', 'replace')
    vsize, vaddr, rawsize, rawptr = struct.unpack_from('<IIII', data, o+8)
    sections.append((name, vaddr, vsize, rawptr, rawsize))
def rva_to_off(rva):
    for name, vaddr, vsize, rawptr, rawsize in sections:
        if vaddr <= rva < vaddr + max(vsize, rawsize):
            return rawptr + (rva - vaddr)
    return None
imports = []
off = rva_to_off(import_rva)
i = 0
while True:
    o = off + i*20
    ilt_rva, _, _, name_rva, iat_rva = struct.unpack_from('<IIIII', data, o)
    if ilt_rva == 0 and name_rva == 0:
        break
    noff = rva_to_off(name_rva)
    end = data.index(b'\x00', noff)
    dll = data[noff:end].decode('ascii', 'replace')
    imports.append(dll)
    i += 1
print('\n'.join(imports))
