import json, sys
a=json.load(open(sys.argv[1])); b=json.load(open(sys.argv[2]))
ha={x["file"]:x["sha256"] for x in a["files"]}
hb={x["file"]:x["sha256"] for x in b["files"]}
diff=[k for k in sorted(set(ha)|set(hb)) if ha.get(k)!=hb.get(k)]
print("REPRODUCIBLE" if not diff else "DIFFERENCES: "+", ".join(diff))
