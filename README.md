# Drone BOM + spend cube (synthetic, fictional)

All companies, parts and prices are invented. Period: Nov 2025 - Oct 2026.

- products.csv: 4 product families x 2 variants (Government / Commercial)
- bom_lines.csv: engineering BOM, one level of assemblies. requires_compliant_supplier=Y means that line
  must come from a supplier with compliant_for_gov=Y (government variants only)
- parts_master.csv: engineering part master
- suppliers.csv: suppliers with compliance flag, evidence type and checked_on date (stand-in for sourcing evidence)
- sourcing_rules.csv: why each government-required part is restricted: statutory / blue_framework / buyer_imposed
- spend_lines.csv: the spend cube. Descriptions are messy on purpose. Watch the uom column:
  EA = each, PR = pair (price per pair), BX100 = box of 100 (price per box). Some lines are not parts at all.
- service_bom.csv: annual spare/warranty demand by part (spares are bought at the MEM-SVC plant)

The _answer_key folder is for grading your matcher and savings math. Do not feed it to the tool.
