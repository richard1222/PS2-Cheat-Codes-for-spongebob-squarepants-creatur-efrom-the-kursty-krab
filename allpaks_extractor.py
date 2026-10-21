#!/usr/bin/env python3
"""
ALLPAKS.PS2 Extractor
Tool for extracting files from ALLPAKS.PS2 archives (Blitz Games format)
Used by: SpongeBob: Creature from the Krusty Krab, Pac-Man World 3, etc.

Based on the blitz_games.bms QuickBMS script by Luigi Auriemma
"""

import struct
import os
import sys

def read_allpaks(filepath, output_dir):
    with open(filepath, 'rb') as f:
        # Read header (13 dwords = 52 bytes)
        header = f.read(52)
        if len(header) < 52:
            print("Error: File too small for header")
            return
        
        tstmp, align, version, files, info_off, textractr_off, zero, dummy1, offset3, dummy2, names_off, names_size, info_size = struct.unpack('<13I', header)
        
        print(f"Header:")
        print(f"  Timestamp: 0x{tstmp:08X}")
        print(f"  Align: {align}")
        print(f"  Version: {version}")
        print(f"  Files: {files}")
        print(f"  Info offset: 0x{info_off:X} (raw), *align = 0x{info_off * align:X}")
        print(f"  Texture extractor offset: 0x{textractr_off:X}")
        print(f"  Offset3: 0x{offset3:X}")
        print(f"  Names offset: 0x{names_off:X} (raw), *align = 0x{names_off * align:X}")
        print(f"  Names size: {names_size}")
        print(f"  Info size: {info_size}")
        
        # Apply alignment
        info_off *= align
        textractr_off *= align
        offset3 *= align
        names_off *= align
        
        # Read name table
        f.seek(names_off)
        name_data = f.read(names_size)
        names = name_data.split(b'\x00')
        
        # Determine method
        method = 0
        tmp = files * 32
        if info_size != 0:
            if tmp > info_size:
                method = 1
        else:
            tmp = tmp + info_off
            tmp = (tmp + align - 1) // align * align  # x align
            if tmp > names_off:  # u> not >=
                method = 1
        
        print(f"  Method: {method}")
        
        # Check for BASE_OFF2
        base_off2 = 0
        if info_off > 0x140:
            f.seek(0x140)
            base_off2_raw = struct.unpack('<I', f.read(4))[0]
            base_off2 = base_off2_raw + info_off
            print(f"  BASE_OFF2: 0x{base_off2:X}")
        
        # Parse file entries
        f.seek(info_off)
        entries = []
        for i in range(files):
            offset = struct.unpack('<I', f.read(4))[0]
            some_crc = struct.unpack('<I', f.read(4))[0]
            size = struct.unpack('<I', f.read(4))[0]
            name_off = struct.unpack('<I', f.read(4))[0]
            is_file = struct.unpack('<I', f.read(4))[0]
            
            if is_file == 0xFFFFFFFF:
                # Skip internal structures
                if method == 0:
                    f.read(4)  # ZERO
                    f.read(8)  # CRC longlong
                continue
            
            if method == 0:
                zero = struct.unpack('<I', f.read(4))[0]
                crc = struct.unpack('<Q', f.read(8))[0]
            
            # Calculate actual offset
            offset *= align
            if is_file & 0x10:
                offset += base_off2
            
            # Get name
            if name_off >= names_size:
                name = ""
            else:
                # Find name in name_data
                name_end = name_data.find(b'\x00', name_off)
                if name_end == -1:
                    name_end = len(name_data)
                name = name_data[name_off:name_end].decode('ascii', errors='replace')
            
            entries.append({
                'index': i,
                'offset': offset,
                'size': size,
                'name': name,
                'is_file': is_file,
                'crc': some_crc
            })
        
        print(f"\nTotal entries: {len(entries)}")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Extract files
        extracted = 0
        for entry in entries:
            name = entry['name']
            if not name:
                continue
            
            # Clean up name (remove any path separators issues)
            name = name.replace('\\', '/')
            if name.startswith('/'):
                name = name[1:]
            
            # Create subdirectories
            full_path = os.path.join(output_dir, name)
            os.makedirs(os.path.dirname(full_path), exist_ok=True) if os.path.dirname(full_path) else None
            
            # Read and write file
            f.seek(entry['offset'])
            data = f.read(entry['size'])
            
            with open(full_path, 'wb') as out:
                out.write(data)
            
            extracted += 1
            if extracted % 100 == 0:
                print(f"  Extracted {extracted} files...")
        
        print(f"\nExtraction complete: {extracted} files extracted to {output_dir}")
        
        # Save file list
        list_path = os.path.join(output_dir, 'filelist.txt')
        with open(list_path, 'w') as lf:
            for entry in entries:
                if entry['name']:
                    lf.write(f"{entry['offset']:08X}  {entry['size']:8d}  {entry['name']}\n")
        print(f"File list saved to {list_path}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python allpaks_extractor.py <ALLPAKS.PS2 file> [output_dir]")
        print("Example: python allpaks_extractor.py ALLPAKS.PS2 extracted/")
        sys.exit(1)
    
    filepath = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "extracted"
    
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        sys.exit(1)
    
    read_allpaks(filepath, output_dir)
