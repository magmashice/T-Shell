from pathlib import Path
p = Path('core/payload_generator.py')
lines = p.read_text().splitlines()
for i in range(75, 90):
    print(f'{i+1}: {repr(lines[i])}')
