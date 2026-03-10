import re
import json

with open("/tmp/greenhouse-response.html") as f:
    html = f.read()

# Find the remix context
match = re.search(r"window\.__remixContext = ({.*?});\s*</script>", html, re.DOTALL)
if match:
    ctx_str = match.group(1)
    try:
        ctx = json.loads(ctx_str)
        # Deep search for relevant keys
        def find_keys(obj, search_terms, path=""):
            results = []
            if isinstance(obj, dict):
                for k, v in obj.items():
                    new_path = f"{path}.{k}" if path else k
                    if any(t.lower() in k.lower() for t in search_terms):
                        results.append((new_path, str(v)[:200]))
                    results.extend(find_keys(v, search_terms, new_path))
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    results.extend(find_keys(item, search_terms, f"{path}[{i}]"))
            return results

        interesting = find_keys(ctx, ["token", "id", "board", "job", "post", "question", "field", "answer", "url", "action", "submit"])
        for path, val in interesting:
            print(f"{path}: {val}")

    except Exception as e:
        print("JSON parse error:", e)
        # Try to find specific patterns
        tokens = re.findall(r'"token"\s*:\s*"([^"]+)"', ctx_str)
        print("Tokens:", tokens[:5])
        ids = re.findall(r'"id"\s*:\s*([0-9]+)', ctx_str)
        print("IDs:", ids[:10])
else:
    print("No remix context found")

# Look for the submit URL in the HTML
print("\n--- Looking for submit/application URLs ---")
submit_urls = re.findall(r'action=["\']([^"\']+)["\']', html)
print("Form actions:", submit_urls)

# Look for boards.greenhouse.io API in script sources
scripts_src = re.findall(r'src=["\']([^"\']+)["\']', html)
print("Script sources:", [s for s in scripts_src if "greenhouse" in s][:5])

# Look for questions array
questions_match = re.findall(r'"questions"\s*:\s*(\[.*?\])', html, re.DOTALL)
for q in questions_match[:2]:
    try:
        qs = json.loads(q)
        for question in qs:
            print("Question:", question.get("label", ""), "| field:", question.get("name", ""), "| required:", question.get("required", ""))
    except Exception as e:
        print("Could not parse questions:", e)
        print(q[:300])
