"""Read-only exact-address pointer and MIPS memory-access candidates."""
import hashlib
import struct
from ps2_elf_audit import parse_elf, file_to_vaddr, vaddr_to_file
from ps2_mips_string_xrefs import _flow_break, _writes_register, _signed16

MEMORY_OPS = {32:'LB',33:'LH',35:'LW',36:'LBU',37:'LHU',39:'LWU',
              40:'SB',41:'SH',43:'SW',55:'LD',63:'SD'}

def inspect_addresses(blob, addresses, lookahead=6, max_hits=100):
    if not 1 <= len(addresses) <= 32 or any(not 0 <= a <= 0xffffffff for a in addresses):
        raise ValueError('provide 1–32 unsigned 32-bit addresses')
    if not 1 <= lookahead <= 64 or not 1 <= max_hits <= 10000:
        raise ValueError('invalid lookahead or max-hits')
    elf=parse_elf(blob);endian='<' if elf['endian']=='little' else '>'
    rows={a:{'address':f'0x{a:08X}', 'file_offset':vaddr_to_file(elf,a),
             'pointer_slots':[], 'memory_accesses':[], 'pointer_count':0,
             'memory_access_count':0} for a in dict.fromkeys(addresses)}
    seen_pointers=set();seen_pairs=set()
    for seg in elf['segments']:
        start=seg['file_offset'];end=start+seg['filesz']
        first=start+((-seg['vaddr'])%4)
        for off in range(first,end-3,4):
            word=struct.unpack_from(endian+'I',blob,off)[0]
            if word in rows and off not in seen_pointers:
                seen_pointers.add(off);row=rows[word];row['pointer_count']+=1
                if len(row['pointer_slots'])<max_hits:
                    row['pointer_slots'].append({'file_offset':off,'address':file_to_vaddr(elf,off)})
            if not seg['executable'] or word>>26!=15:continue
            reg=word>>16&31
            if not reg:continue
            for lowoff in range(off+4,min(off+4*(lookahead+1),end-3),4):
                low=struct.unpack_from(endian+'I',blob,lowoff)[0]
                op=low>>26
                if op in MEMORY_OPS and low>>21&31==reg:
                    address=(((word&65535)<<16)+_signed16(low&65535))&0xffffffff
                    key=(off,lowoff,address)
                    if address in rows and key not in seen_pairs:
                        seen_pairs.add(key);row=rows[address];row['memory_access_count']+=1
                        if len(row['memory_accesses'])<max_hits:
                            row['memory_accesses'].append({'lui_address':seg['vaddr']+off-start,
                                'access_address':seg['vaddr']+lowoff-start,'kind':MEMORY_OPS[op]})
                if _flow_break(low) or _writes_register(low,reg):break
    for row in rows.values():
        row['truncated']=(row['pointer_count']>len(row['pointer_slots']) or
                          row['memory_access_count']>len(row['memory_accesses']))
    return {'sha256':hashlib.sha256(blob).hexdigest(),'addresses':list(rows.values()),
            'limitations':['Static candidates; executable segments may contain data',
                            'Only LUI plus immediate memory accesses; no reachability proof',
                            'No gp-relative, derived-base or indirect access tracking']}
