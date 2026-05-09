import requests
import random

random.seed(42)
n, p = 200, 20

rows = []
for i in range(n):
    sig = random.gauss(0, 3)
    row = []
    for j in range(p):
        noise_val = random.gauss(0, 0.5)
        if j < 5:
            row.append(noise_val + sig)
        else:
            row.append(noise_val)
    rows.append(row)

header = ",".join(["Stock_" + chr(65+i) for i in range(p)])
lines = [header]
for row in rows:
    lines.append(",".join(["%.6f" % v for v in row]))
csv_data = "\n".join(lines)

files = {"file": ("signal_test.csv", csv_data, "text/csv")}
data = {"scale": "1.0", "fill_strategy": "zero", "standardize": "true"}
r = requests.post("http://127.0.0.1:8000/api/rmt/upload", files=files, data=data)
d = r.json()
print("outlier_eigenvectors count:", len(d.get("outlier_eigenvectors", [])))
if len(d.get("outlier_eigenvectors", [])) > 0:
    oe = d["outlier_eigenvectors"][0]
    print("Has vector:", "vector" in oe)
    if "vector" in oe:
        print("Vector length:", len(oe["vector"]))
