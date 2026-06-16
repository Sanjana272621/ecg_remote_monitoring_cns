with open("sample_data2.txt", "r") as original:
    with open("modified.txt", "w") as new:
        org_lines = original.readlines()
        for i in range(len(org_lines)):
            if org_lines[i] == "\n":
                if org_lines[i+1] != "\n":
                    continue 
            if ("61008-9^Body temperature T2^LN" in org_lines[i]) or ("18|NM|18686-6^Respiration rate^LN" in org_lines[i]):
                continue 
            new.write(org_lines[i])
            