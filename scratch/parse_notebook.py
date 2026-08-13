import json

with open('dr-s-medicine-prescription-prediction-model-99.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Print ALL cell outputs to find the 78 class names
print("=== All cells with outputs ===")
for i, cell in enumerate(nb['cells']):
    outputs = cell.get('outputs', [])
    if outputs:
        src = ''.join(cell['source'])
        print(f"\n--- Cell {i} source ---")
        print(src[:300])
        print("--- outputs ---")
        for out in outputs:
            data = out.get('data', {})
            text = data.get('text/plain', '')
            html = data.get('text/html', '')
            print(f"text: {text[:2000]}")
            if html:
                print(f"html: {html[:1000]}")
