# Drone BOM + spend cube (synthetic, fictional)

All companies, parts and prices are invented. Period: from 2025-11-01 for 12 months.

- products.csv: product families x variants
- bom_lines.csv: engineering BOM. requires_compliant_supplier=Y means that line must come from a supplier
  with compliant_for_gov=Y (regulated variant only)
- parts_master.csv: engineering part master
- suppliers.csv: suppliers with an eligibility flag and evidence type
- sourcing_rules.csv: why each restricted part is restricted, and on what basis
- spend_lines.csv: the spend cube. Descriptions are messy on purpose. uom: EA = each, PR = pair, BX100 = box of 100.
  Some lines are not parts at all.
- service_bom.csv: annual spare/warranty demand by part (spares are bought at plant MEM-SVC)

The _answer_key folder is for grading the matcher and savings math. Do not feed it to the tool.
