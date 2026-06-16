with open("modified.txt", "r") as old:
    with open("fixed.txt", "w") as new:

        current_segment = ""

        for line in old:

            stripped = line.strip()

            # preserve blank line between messages
            if stripped == "":

                if current_segment:
                    new.write(current_segment + "\n")
                    current_segment = ""

                new.write("\n")
                continue

            # real HL7 segment
            if stripped.startswith(("MSH", "PID", "OBR", "OBX")):

                if current_segment:
                    new.write(current_segment + "\n")

                current_segment = stripped

            else:
                # waveform continuation line
                current_segment += stripped

        if current_segment:
            new.write(current_segment + "\n")