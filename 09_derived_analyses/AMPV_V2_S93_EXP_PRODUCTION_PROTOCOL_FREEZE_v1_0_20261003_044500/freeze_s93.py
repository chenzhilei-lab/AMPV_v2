from pathlib import Path
import json
b=Path(r"F:\AMPV_V2\12_DERIVED_ANALYSES\AMPV_V2_S93_EXP_PRODUCTION_PROTOCOL_FREEZE_v1_0_20261003_044500")
p={"stage":"S93-EXP Production Protocol Freeze","version":"v1.0","status":"PASS_PRODUCTION_AUTHORIZED","user_authorization":True,"task_family":"COMPACT_PSF_PRIMARY","N_base":300,"condition_cells_per_sample":15,"workflows":["A","B","C","E"],"expected_rows":18000,"kappa_ref":[1,2,5,10,20],"C":[0.0,0.6,1.0],"lhs_seed":20261003,"analysis_seed":20261004,"core_sha256":"B55562056BDC6AEBF47E4540F1A9E517280E9A4A6551B265DB7EB994DDD182A7","runner_sha256":"5414E62C3C8366374E2EB9A19029C51277A791060C13B0E0E1E3305AD01A8875","pure_import_pass":True,"original_canonical_modified":False,"original_production_rerun":False}
(b/"S93_PROTOCOL_FREEZE.json").write_text(json.dumps(p,indent=2),encoding="utf-8")
(b/"S93_PROTOCOL_FREEZE.md").write_text("# S93-EXP Production Protocol Freeze v1.0\n\nStatus: PASS_PRODUCTION_AUTHORIZED\n\nUser explicitly authorized COMPACT_PSF_PRIMARY N=300 production.\n\nFrozen core SHA-256: "+p["core_sha256"]+"\n\nFrozen runner SHA-256: "+p["runner_sha256"]+"\n\nExpected output: 300 base identities x 15 condition cells x 4 workflows = 18,000 rows.\n\nExisting AMPV V2 canonical and original production remain untouched.\n",encoding="utf-8")
print("S93_FREEZE_PASS")
