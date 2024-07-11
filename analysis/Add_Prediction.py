#! /usr/bin/env python3

import csv

# Script operates on aggregated csv file containing one measurement per line
# It enhances the agg file by adding a prediction for the maf, or e.g. decides whether a resolver is vulnerable

def required_fields_present(camp, row):
  # Make sure all required fields are present
  for p_type in [p[0] for p in camp]:
    for f in required_fields[p_type]:
      if row[f] == "":
        return False
  return True

MAF_R = {
  ("FO", "FO"): lambda x, y: 1 + x + x*y,
  ("FOs", "FO"): lambda x, y: 1 + x + x*y,
  ("FOs", "FOs"): lambda x, y: 1 + x + x*y,
  ("FO", "RC"): lambda x, y: 1 + x + x*y,
  ("FO", "WC"): lambda x, y: 1 + x + x*y,
  ("FO", "QM"): lambda x, y: 1 + x + x*y,
  ("FO", "DD"): lambda x, y: 1 + x + x*y,
  ("RC", "QM"): lambda x, y: x*y,
  ("RC", "DD"): lambda x, y: 1 + x + x*y,
  ("WC", "FO"): lambda x, y: 2*x + x*y,
  ("WC", "RC"): lambda x, y: x + 2*x*y,
  ("WC", "QM"): lambda x, y: x*y,
  ("WC", "DD"): lambda x, y: 1 + x + x*y,
  ("DD", "FO"): lambda x, y: 1 + x + x*y,
  ("DD", "RC"): lambda x, y: 2 * x * y,
  ("DD", "WC"): lambda x, y: 1 + x + x*y,
  ("DD", "QM"): lambda x, y: 1 + x + x*y,
  ("DD", "DD"): lambda x, y: 2*x + x*y
}

# Formulas to limit the effective dimension of a CAMP derivative, and the fields required to compute them
# 'dim' is the dimension of the CAMP derivative that was installed in the attack pattern
# 'dat' is the row of the aggregated csv file containing the measurement data of other patterns for the resolvers
LIM = {
  #"FO": lambda dim, dat: min(dim, int(dat['ffail_ns_tried'])) * float(dat['ffail_mean_tries']),
  #"FO": lambda dim, dat: min(dim, int(dat['fsucc_ns_tried'])) * float(dat['fsucc_mean_tries']),
  "FO": lambda dim, dat: min(dim, int(dat['fsucc_ns_tried'])) * ((float(dat['fsucc_mean_tries']) + float(dat['ffail_mean_tries'])) / 2),
  "QM": lambda dim, dat: min(dim, int(dat['qmin_iter']) + 1),
  "WC": lambda dim, dat: min(dim, int(dat['cc_tot'])) * float(dat['cc_mean_tries'])
}
required_fields = {
  "FO": ["ffail_total", "ffail_ns_tried", "ffail_mean_tries"],
  "WC": ["cc_tot", "cc_mean_tries", "cc_length"],
  "QM": ["qmin_iter"]
}

if __name__ == "__main__":

  import argparse

  # Add arg for input csv and output csv
  parser = argparse.ArgumentParser(description='Add prediction to the input csv')
  parser.add_argument('input_csv', type=str, help='Input csv file')
  parser.add_argument('output_csv', type=str, help='Output csv file')


  args = parser.parse_args()




  # Read input csv in streamline fashion
  with open(args.input_csv, 'r') as input_csv:
    with open(args.output_csv, 'w') as output_csv:

      reader = csv.DictReader(input_csv)

      header = reader.fieldnames
      maf_fields = [f for f in header if f.startswith("maf_amp_")]
      assert len(maf_fields) == 1, "Expected exactly one maf field, multiple not implemented"
      
      comp = maf_fields[0].split("_")[-1]
      mf = comp.split("-")

      # Parse header
      #camp = (("FO", 8), ("FO", 8))
      base_camp = (
        (mf[0][0:2], int(mf[0][2:])),
        (mf[1][0:2], int(mf[1][2:]))
        )

      writer = csv.DictWriter(output_csv, fieldnames=reader.fieldnames + ['pred_'+comp])

      # Write header
      writer.writeheader()

      # Write rows
      for row in reader:
        prediction = None

        if not required_fields_present(base_camp, row):
          continue

        camp = []
        # Limit dimension
        for p_type, dim in base_camp:
          if p_type in LIM:
            x = LIM[p_type](dim, row)
            camp.append((p_type, x))
          else:
            assert False, f"{p_type} not implemented"
        camp = tuple(camp)

        prediction = MAF_R[(camp[0][0], camp[1][0])](camp[0][1], camp[1][1])
        row['pred_'+comp] = prediction
        writer.writerow(row)

