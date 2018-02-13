import collections
import numpy
import os
import sys


# Assumptions - CMTE_ID is of 9 characters
# ZIP_CODE is 5 characters only
# TRANSACTION_DT are correct in the 'mmddyy' format

donor_type = collections.defaultdict()
recipients = collections.defaultdict()
donations = collections.defaultdict()


def lengths_assumed(cmte, zip_code, tr_dt):
    if len(cmte) == 9 and len(zip_code) == 5 and len(tr_dt) == 4:
        return True
    else:
        return False


def not_empty(name, cmte, tr_amt, tr_dt, other_id):
    if name != "" and cmte != "" and cmte != "" and tr_amt != "" and tr_dt != "" and other_id == "":
        return True
    else:
        return False


def clean_line(line):
    fields = line.split("|")

    cmte = fields[0]
    name = fields[7]
    zip_code = fields[10][0:5]
    tr_amt = fields[14]
    tr_dt = fields[13][4:]
    other_id = fields[15]
    unique_id = ""
    unique_id_yr = ""
    cmte_zip_yr = ""
    new_line = ""

    if not_empty(name, cmte, tr_amt, tr_dt, other_id) and lengths_assumed(cmte, zip_code, tr_dt):
        unique_id = name + zip_code
        unique_id_yr = name + zip_code + tr_dt
        cmte_zip_yr = cmte + zip_code + tr_dt
        new_line = {cmte, name, zip_code, tr_amt, tr_dt}
    return new_line, unique_id, unique_id_yr, cmte_zip_yr, tr_amt


def percentile_fn(lst):
    lst = sorted(lst)
    return numpy.percentile(lst, 30, interpolation="nearest")  # return 30th percentile using nearest rank method


def write_line(cmte_zip_yr, total_amt, count, output_file):
    # strip required values to output format

    recipient_id = cmte_zip_yr[:9]
    zip_code = cmte_zip_yr[9:14]
    yr = cmte_zip_yr[14:]
    percentile30 = percentile_fn(sum(total_amt, []))
    total_donations = sum(sum(total_amt, []))

    output_line = str(recipient_id) + "|" + str(zip_code) + "|" + str(yr) + "|" + str(
        percentile30) + "|" + str(total_donations) + "|" + str(count) + "\n"

    if not os.path.exists(output_file):
        write_fp = open(output_file, "w+")
        write_fp.write(output_line)
    else:
        write_fp = open(output_file, "a+")
        write_fp.write(output_line)
    write_fp.close()


def main(argv):
    if len(argv) < 2:
        sys.exit(2)
    else:
        input_file = argv[0]
        percent_file = argv[1]
        output_file = argv[2]

    with open(input_file, 'r') as fp:
        for line in fp:
            total_amt = []
            count = 0
            newline, unique_id, unique_id_yr, cmte_zip_yr, tr_amt = clean_line(line)

            # Collect donor information
            if unique_id not in donor_type:
                donor_type[unique_id] = "non-repeat"
            else:
                donor_type[unique_id] = "repeat"

            if unique_id not in recipients:
                recipients[unique_id] = [cmte_zip_yr]
            else:
                recipients[unique_id].append(cmte_zip_yr)

            if unique_id not in donations:
                donations[unique_id_yr] = [int(tr_amt)]
            else:
                donations[unique_id_yr].append(int(tr_amt))

            if donor_type[unique_id] == 'repeat':
                count = 0
                total_amt = []
                # Check if the recipient of current line corresponds to donations from any donors of type 'repeat'
                for unique_id in recipients.keys():
                    if cmte_zip_yr in recipients[unique_id] and donor_type[unique_id] == 'repeat':
                        count = count + 1
                        year = cmte_zip_yr[14:]
                        same_year = unique_id + year
                        total_amt.append(donations[same_year])

            if count != 0:
                write_line(cmte_zip_yr, total_amt, count, output_file)


if __name__ == "__main__":
    main(sys.argv[1:])
