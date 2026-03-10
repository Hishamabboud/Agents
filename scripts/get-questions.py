import re
import json

with open("/tmp/greenhouse-response.html") as f:
    html = f.read()

match = re.search(r"window\.__remixContext = ({.*?});\s*</script>", html, re.DOTALL)
if match:
    ctx = json.loads(match.group(1))
    job_data = ctx["state"]["loaderData"]["routes/$url_token_.jobs_.$job_post_id"]

    print("Submit path:", job_data.get("submitPath"))
    print("\n=== All Questions ===")
    for i, q in enumerate(job_data["jobPost"]["questions"]):
        print(f"\nQuestion {i}: {q.get('label', 'NO LABEL')} (required={q.get('required', False)})")
        for field in q.get("fields", []):
            print(f"  Field name: {field['name']}, type: {field['type']}")
            if "values" in field:
                for v in field["values"]:
                    print(f"    Option: value={v['value']} label={v['label']}")

    print("\n=== Education Config ===")
    edu = job_data["jobPost"].get("education_config", {})
    print(json.dumps(edu, indent=2))
