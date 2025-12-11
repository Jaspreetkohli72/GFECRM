
import csv
import re

raw_data = """
CNC work rates by vikas on 30.10.25
2mm..for me..175 to 185 for client 200 to 225
3mm..for me. 260 to 280 for client 300 to 330
4mm..for me..350 to 375 for client 400 to 420

28.5.24......
PATTI... 18ft (60 to 64 per kg)
18x3.. 2.5kg 
18x5.. 4kg 
25x3.. 3.25kg
25x5.. 5.5kg
32x5.. 7.5kg
40x5.. 9kg
50x5.. 12kgmm. 
65x5.. 17kg
75x5.. 22kg
100x5.. 26kg

ANGLE.. 18ft (60 to 68 per kg)
18x3.. 4kg
25x2.5.. 4.5kg
25x3.. 7kg
25x5.. 9kg
32x3.. 9kg
35x5.. 14kg
40x5.. 17kg
50x5.. 22kg
65x6.. 39kg
75x6.. 45kg

BAR Square / Round Rod.. 18ft (61per kg)
10mm.. 4.5kg
12mm.. 7.5kg
16mm.. 12kg
20mm.. 18kg
25mm.. 24kg

PYPE Square / Round.. 20ft (62 to 70 per kg)
3/4".. 5.5kg (1mm)
1".. 5.5(.5mm)/7.5(1mm)/9kg (2mm)
1.25".. 6.5(.5mm)/9kg(1mm)/12kg(2mm)
1.5".. 8.5(.5mm)/11(1mm)/14(2mm)
          19kg(2.5mm)
2".. 14(1mm)/18(2mm)/23kg(2.5mm)
2.5".. 20(1mm)/25(2mm)/32kg(2.5mm)
3".. 27(1mm)/35(2mm)/38kg(2.5mm)
4".. 33(1mm) /38(l2mm)/45kg(2.5mm)
6".. 52kg(2mm) to 60kg(2.5mm)

PYPE Rectangular.. 20ft (62 to 70 per kg)
2x1.. 8kg(.5mm)/11(1mm)/14kg(2mm)
          17.5kg(2.5mm)
3x1.. 14(1mm)/18kg (2mm)/22kg(2.5mm)
3x1.5.. 18(1mm)/23(2mm)/29kg(2.5mm)
4x1.. 18(1mm)/23kg(2mm)/28kg(2.5mm)
4x2.. 25(1mm)/33(2mm)/39kg(2.5mm)
5x2.5.. 45kg(2mm)/55kg(2.5mm)

CHANNEL.. 20ft.  (62 per kg)
3x1.5.. 23(2.5mm)/36kg(5mm)
4x2.. 40kg(3mm) / 55kg(6mm)
5x2.5.. 75kg(6mm)
6x3.. 95kg(6mm)

GARDER (I Beam)..  (63 per kg)
4x2.. 50kg(6mm)
4x4.5.. 140kg(6mm)
5x2.75.. 81kg(6mm)
6x3.. 90kg(6mm)
6x6.. 220kg(6mm)
8x4.. 160kg(6mm)
8x6.. 310kg(6mm)
9x4.5.. 190(6mm)
10x5.. 230(6mm)

SHEET...  (78 to 82 per kg)
3x8.. (22g) 14kg (20g) 18kg / (18g) 21kg (16g) 27kg 
Mtr.. (22g) 16kg (20g) 20kg / (18g) 25kg (16g) 30kg
4x8.. (22g) 20kg (20g) 25kg / (18g) 30kg (16g) 40kg (14g) 50kg

PROFILE SHEET.. (width 3.5ft)
0.40..Wt 1.1kg per running ft / 0.325 persqft) 
8ft (9kg) / 10ft (11kg) / 12ft (13.5kg) 14ft (15.5kg)
16ft (18kg) 18ft (20kg) 20ft (22kg)...   (100 per kg)
0.50..Wt 1.4 kg per running ft / 0.430 per sqft) 
8ft (11.5kg) / 10ft (14kg) / 12ft (17kg) 14ft (20kg)
16ft (22.5kg) / 18ft (25.5kg) 20ft (28kg)...   (98 per kg)
"""

def parse_data(text):
    inventory = []
    
    # --- Helper Functions ---
    def add_item(name, type, dim, rate, unit='ft'):
        inventory.append({
            'item_name': name,
            'base_rate': round(rate, 2),
            'unit': unit,
            'item_type': type,
            'dimension': dim
        })

    # --- 1. CNC Work ---
    # 2mm..for me..175 to 185 for client 200 to 225 -> avg 212.5
    # 3mm..for me. 260 to 280 for client 300 to 330 -> avg 315
    # 4mm..for me..350 to 375 for client 400 to 420 -> avg 410
    cnc_data = [
        ('2mm', 212.5), ('3mm', 315), ('4mm', 410)
    ]
    for cdim, crate in cnc_data:
        add_item(f"CNC Cutting {cdim}", "CNC Work", cdim, crate, 'sqft') # Assuming sqft

    # --- Section Metadata ---
    sec_meta = {
        'PATTI': {'rate': 62.0, 'len': 18.0, 'type': ['Flat Bar']},
        'ANGLE': {'rate': 64.0, 'len': 18.0, 'type': ['Angle']},
        'BAR': {'rate': 61.0, 'len': 18.0, 'type': ['Square Bar', 'Round Bar']},
        'PYPE S': {'rate': 66.0, 'len': 20.0, 'type': ['Square Pipe', 'Round Pipe']}, # PYPE Square / Round
        'PYPE R': {'rate': 66.0, 'len': 20.0, 'type': ['Rectangular Pipe']}, # PYPE Rectangular
        'CHANNEL': {'rate': 62.0, 'len': 20.0, 'type': ['Channel']},
        'GARDER': {'rate': 63.0, 'len': 20.0, 'type': ['GARDER']}, # Renamed from I Beam to GARDER
        'SHEET': {'rate': 80.0, 'len': 1.0, 'type': ['Sheet']}, # Rate ~80
        'PROFILE': {'rate': 100.0, 'len': 1.0, 'type': ['Profile Sheet']} # Rate ~100 (default, overridden later)
    }

    lines = text.split('\n')
    current_section = None
    
    # State for multi-line PYPE R parsing
    pype_r_base_dim = None
    pype_r_variants_buffer = []

    for line in lines:
        line = line.strip()
        if not line: continue
        
        # Detect Header
        u_line = line.upper()
        if "PATTI" in u_line: 
            current_section = 'PATTI'
            pype_r_base_dim = None # Reset state
        elif "ANGLE" in u_line: 
            current_section = 'ANGLE'
            pype_r_base_dim = None
        elif "BAR SQUARE" in u_line: 
            current_section = 'BAR'
            pype_r_base_dim = None
        elif "PYPE SQUARE" in u_line: 
            current_section = 'PYPE S'
            pype_r_base_dim = None
        elif "PYPE RECTANGULAR" in u_line: 
            current_section = 'PYPE R'
            pype_r_base_dim = None # Reset for new section
            pype_r_variants_buffer = []
        elif "CHANNEL" in u_line: 
            current_section = 'CHANNEL'
            pype_r_base_dim = None
        elif "GARDER" in u_line: 
            current_section = 'GARDER'
            pype_r_base_dim = None
        elif "SHEET" in u_line and "PROFILE" not in u_line: 
            current_section = 'SHEET'
            pype_r_base_dim = None
        elif "PROFILE SHEET" in u_line: 
            current_section = 'PROFILE'
            pype_r_base_dim = None
        elif "CNC" in u_line: 
            current_section = 'CNC'
            pype_r_base_dim = None
        
        if not current_section or "CNC" in current_section: continue
        # Skip header lines
        if any(x in u_line for x in ["PATTI", "ANGLE", "BAR SQUARE", "PYPE", "CHANNEL", "GARDER", "SHEET", "PROFILE"]): continue

        meta = sec_meta.get(current_section)
        if not meta: continue

        # --- Parsing Logic per Section ---
        
        # PATTI, ANGLE, BAR, CHANNEL, GARDER
        if current_section in ['PATTI', 'ANGLE', 'BAR', 'CHANNEL', 'GARDER']:
            # This block should not process PYPE S or PYPE R, so the check is redundant here.
            # if current_section in ['PYPE S', 'PYPE R']: continue 
            
            clean_line = line.replace('mm.', '').replace('kg', '')
            parts = re.split(r'\.\.+', clean_line)
            
            if len(parts) >= 2:
                dim = parts[0].strip()
                weight_str = re.search(r'([\d\.]+)', parts[1])
                if weight_str:
                    weight = float(weight_str.group(1))
                    rate = (weight / meta['len']) * meta['rate']
                    for t in meta['type']:
                         add_item(f"{t} {dim}", t, dim, rate, 'ft')
                         
        # PYPE S (Square/Round)
        if current_section == 'PYPE S':
            parts = re.split(r'\.\.+', line)
            if len(parts) >= 2:
                base_dim = parts[0].strip().replace('"', ' inch')
                variants = parts[1].split('/')
                for v in variants:
                    match = re.search(r'([\d\.]+)\s*\(?([^\)]+)\)?', v)
                    if match:
                        w = float(match.group(1))
                        thick = match.group(2).replace(')', '').replace('kg', '').strip()
                        thick = thick.lstrip('(')
                        full_dim = f"{base_dim} ({thick})"
                        rate = (w / meta['len']) * meta['rate']
                        add_item(f"Square Pipe {full_dim}", "Square Pipe", full_dim, rate, 'ft')
                        add_item(f"Round Pipe {full_dim}", "Round Pipe", full_dim, rate, 'ft')

        # PYPE R (Rectangular) - Handle multi-line variants
        if current_section == 'PYPE R':
            if '..' in line: # This is a new base dimension line
                if pype_r_base_dim and pype_r_variants_buffer: # Process previous entry if any
                    full_variants_str = "/".join(pype_r_variants_buffer)
                    for v in full_variants_str.split('/'):
                        match = re.search(r'([\d\.]+)[kg]*\s*\(?([^\)]+)\)?', v)
                        if match:
                            w = float(match.group(1))
                            thick = match.group(2).replace(')', '').replace('kg', '').strip()
                            thick = thick.lstrip('(')
                            full_dim = f"{pype_r_base_dim} ({thick})"
                            rate = (w / meta['len']) * meta['rate']
                            add_item(f"Rectangular Pipe {full_dim}", "Rectangular Pipe", full_dim, rate, 'ft')
                
                parts = re.split(r'\.\.+', line)
                pype_r_base_dim = parts[0].strip()
                pype_r_variants_buffer = [parts[1]]
            elif pype_r_base_dim: # This is a continuation line for the current base_dim
                pype_r_variants_buffer.append(line.strip())
            
    # After loop, process any remaining PYPE R buffered items
    if current_section == 'PYPE R' and pype_r_base_dim and pype_r_variants_buffer:
        full_variants_str = "/".join(pype_r_variants_buffer)
        for v in full_variants_str.split('/'):
            match = re.search(r'([\d\.]+)[kg]*\s*\(?([^\)]+)\)?', v)
            if match:
                w = float(match.group(1))
                thick = match.group(2).replace(')', '').replace('kg', '').strip()
                thick = thick.lstrip('(')
                full_dim = f"{pype_r_base_dim} ({thick})"
                rate = (w / meta['len']) * meta['rate']
                add_item(f"Rectangular Pipe {full_dim}", "Rectangular Pipe", full_dim, rate, 'ft')


        # SHEET
        if current_section == 'SHEET':
            parts = re.split(r'\.\.+', line)
            if len(parts) >= 2:
                sheet_dim = parts[0].strip() 
                matches = re.findall(r'\(([^)]+)\)\s*([\d\.]+)kg?', line)
                for gage, w in matches:
                    w = float(w)
                    full_dim = f"{sheet_dim} - {gage}"
                    rate = w * meta['rate']
                    add_item(f"Sheet {full_dim}", "Sheet", full_dim, rate, 'pcs')

        # PROFILE SHEET
        if current_section == 'PROFILE':
             parts = re.split(r'\.\.+', line)
             if len(parts) >= 2:
                 thick = parts[0].strip()
                 
                 kg_rate_match = re.search(r'\((\d+)\s*per kg\)', line)
                 kg_rate = float(kg_rate_match.group(1)) if kg_rate_match else 100.0 # Default if not found
                 
                 w_match = re.search(r'Wt\s*([\d\.]+)\s*kg', parts[1])
                 if w_match:
                     w_per_ft = float(w_match.group(1))
                     rate = w_per_ft * kg_rate
                     add_item(f"Profile Sheet {thick}", "Profile Sheet", thick, rate, 'ft')
                 
                 # Also parse the length-based weights for profile sheets
                 length_weights = re.findall(r'(\d+)ft\s*\(([\d\.]+)kg\)', line)
                 for length_str, weight_str in length_weights:
                     length = float(length_str)
                     weight = float(weight_str)
                     # Calculate rate per piece (length * ft_rate)
                     # Assuming the 'per kg' rate applies to these as well
                     rate_per_piece = weight * kg_rate
                     add_item(f"Profile Sheet {thick} {length_str}ft", "Profile Sheet", f"{thick} {length_str}ft", rate_per_piece, 'pcs')


    return inventory

data = parse_data(raw_data)

with open('inventory_import.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['item_name', 'base_rate', 'unit', 'item_type', 'dimension'])
    writer.writeheader()
    writer.writerows(data)

print(f"Generated {len(data)} items.")
