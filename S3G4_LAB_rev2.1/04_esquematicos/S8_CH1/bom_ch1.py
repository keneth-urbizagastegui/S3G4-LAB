"""BOM de CH1 con precios aproximados de LCSC (consultados con pcbparts el 4 oct 2026).
Precio = el de 1 unidad de LCSC salvo que se indique. Todos los códigos consultados con pcbparts el 4 oct 2026; 'basic' incluye las 'preferred' (sin cargo por referencia).
Ejecutar: python bom_ch1.py  -> escribe CH1_BOM_precios.csv e imprime el resumen."""
import csv, os
# (bloque, refs, descripción, LCSC, precio_unidad_USD, tipo, nota)
# tipo: ext = extendida (cargo por referencia en JLCPCB), basic, gen = genérico (código por elegir), dnp
L = [
 ("Entrada", "J101", "BNC Kinghelm KH-BNC50-3511", "C2837587", 0.9315, "ext", "THT"),
 ("Entrada", "R101 R102", "549 kΩ 0.1 % 25 ppm 1206 (Yageo RT1206BRD07549KL)", "C870790", 0.0574, "ext", ""),
 ("Entrada", "C101", "20 pF ±2 % C0G 250 V 0603 (Murata)", "C3845779", 0.18, "ext", ""),
 ("Entrada", "C102", "15 pF ±2 % C0G 250 V 0805 (Murata)", "C3836120", 0.4861, "ext", "355 en stock"),
 ("Entrada", "VC101", "Trimmer SEHWA 2–6 pF 100 V", "C22468120", 0.4942, "ext", ""),
 ("Entrada", "C103", "Hueco DNP 0603", "", 0.0, "dnp", "no se monta"),
 ("Entrada", "R103", "11.0 kΩ 0.1 % 25 ppm 0805 (Yageo RT0805BRD0711KL)", "C865156", 0.0501, "ext", ""),
 ("Entrada", "C104", "1 nF ±1 % C0G 50 V 0603 (FH)", "C507408", 0.0298, "ext", ""),
 ("Entrada", "C105", "68 pF ±5 % C0G 50 V 0603 (Samsung)", "C28262", 0.0187, "basic", "preferred"),
 ("Entrada", "R104 R105", "49.9 kΩ 1 % 1206 200 V (Uni-Royal)", "C18017", 0.0084, "ext", ""),
 ("Entrada", "C106", "C_S 1.2 nF C0G 630 V 1206 (Walsin)", "C3851387", 0.0675, "ext", ""),
 ("Entrada", "R106", "R_EQ 10 MΩ 1 % 1206 200 V (Uni-Royal)", "C26119", 0.0056, "ext", ""),
 ("Entrada", "C107", "C_EQ ≈ 8.2 pF C0G 1 kV 1206 (CCTC)", "C54431614", 0.0064, "ext", "seleccionado en prueba"),
 ("Relé", "K101", "Relé TQ2SA-5V-Z (Panasonic, SMD)", "C22686", 1.5623, "ext", ""),
 ("Relé", "Q101", "2N7002 SOT-23", "C8545", 0.0178, "basic", ""),
 ("Relé", "D104", "1N4148W SOD-123", "C81598", 0.0123, "basic", ""),
 ("Relé", "R135", "100 Ω 1 % 0603", "C22775", 0.0031, "basic", "0603 en vez de 0402"),
 ("Relé", "R136", "100 kΩ 1 % 0603", "C25803", 0.0031, "basic", "0603 en vez de 0402"),
 ("Protección y acoplo", "D101", "BAV199 Nexperia SOT-23", "C40919", 0.0425, "ext", ""),
 ("Protección y acoplo", "SW101", "SS23H37L6 DP3T deslizante", "C883267", 0.3422, "ext", "THT; 442 en stock"),
 ("Protección y acoplo", "C108", "C_AC 1.8 nF ±5 % C0G 50 V 0603 (Murata)", "C97878", 0.0222, "ext", ""),
 ("Protección y acoplo", "R107", "R_BIAS 10 MΩ 1 % 0603 (Uni-Royal)", "C7250", 0.0037, "basic", "ve ≤ 6 V"),
 ("Protección y acoplo", "R108", "R_PROT 1 kΩ 1 % 0603", "C21190", 0.0026, "basic", ""),
 ("Protección y acoplo", "R133 R134", "Pull-ups 10 kΩ 1 % 0603", "C25804", 0.0018, "basic", "0603 en vez de 0402"),
 ("Buffer", "U101", "OPA810IDBVR SOT-23-5", "C2833513", 3.079, "ext", ""),
 ("Escalera", "R109 R137", "RL1 = 1 kΩ ∥ 1 kΩ (499 Ω) 1 % 0603", "C21190", 0.0026, "basic", "§2.10"),
 ("Escalera", "R110", "RL2 = 270 Ω ∥ (249 Ω) 1 % 0603", "C22966", 0.002, "basic", "§2.10"),
 ("Escalera", "R140", "RL2 = ∥ 3.3 kΩ 1 % 0603", "C22978", 0.002, "basic", "§2.10"),
 ("Escalera", "R111", "RL3 150 Ω 1 % 0603", "C22808", 0.0017, "basic", ""),
 ("Escalera", "R112", "RL4 49.9 Ω 1 % 0603", "C23185", 0.0021, "basic", ""),
 ("Escalera", "R113 R143 R114 R144", "RL5, RL6 = 49.9 Ω ∥ 49.9 Ω (24.9 Ω) 1 % 0603", "C23185", 0.0021, "basic", "§2.10"),
 ("Escalera", "R115", "12.4 kΩ 0.1 % 50 ppm 0402 (Yageo RT0402BRE0712K4L)", "C853011", 0.0205, "ext", "VCHECK"),
 ("Escalera", "R116", "100 Ω 0.1 % 50 ppm 0402 (Ever Ohms)", "C332259", 0.0144, "ext", "VCHECK"),
 ("Escalera", "U102", "74HC4051D Nexperia SOIC-16", "C9386", 0.2146, "ext", ""),
 ("Ganancia", "U103", "AD8039ARZ-REEL7 SOIC-8", "C96525", 4.638, "ext", ""),
 ("Ganancia", "R117 R120", "R_SER 470 Ω 1 % 0603", "C23179", 0.0023, "basic", ""),
 ("Ganancia", "D102 D103", "BAV99 Nexperia SOT-23", "C2500", 0.0124, "basic", ""),
 ("Ganancia", "R118", "RF1 1.00 kΩ 1 % 0603", "C21190", 0.0026, "basic", ""),
 ("Ganancia", "R119 R122", "RG1, RG2 = 270 Ω ∥ (249 Ω) 1 % 0603", "C22966", 0.002, "basic", "§2.10"),
 ("Ganancia", "R141 R142", "RG1, RG2 = ∥ 3.3 kΩ 1 % 0603", "C22978", 0.002, "basic", "§2.10"),
 ("Ganancia", "R121", "RF2 = 2.2 kΩ + (2.26 kΩ) 1 % 0603", "C4190", 0.002, "basic", "§2.10"),
 ("Ganancia", "R145", "RF2 = + 68 Ω 1 % 0603", "C27592", 0.0013, "basic", "§2.10"),
 ("Filtro", "U105", "AD8039ARZ-REEL7 SOIC-8", "C96525", 4.638, "ext", "misma referencia que U103"),
 ("Filtro", "R123 R124", "1.1 kΩ + (1.11 kΩ) 1 % 0603", "C22764", 0.0018, "basic", "§2.10; preferred"),
 ("Filtro", "R148 R149", "+ 10 Ω 1 % 0603", "C22859", 0.002, "basic", "§2.10"),
 ("Filtro", "R125 R138 R126 R139", "1 kΩ ∥ 1 kΩ (499 Ω) 1 % 0603", "C21190", 0.0026, "basic", "§2.10"),
 ("Filtro", "C109 C112", "56 pF ±5 % C0G 50 V 0603 (Samsung)", "C39148", 0.0112, "basic", "preferred"),
 ("Filtro", "C110", "47 pF ±5 % C0G 50 V 0603 (Samsung)", "C1671", 0.0064, "basic", ""),
 ("Filtro", "C111", "220 pF ±5 % C0G 100 V 0603 (Murata)", "C388907", 0.0179, "ext", "la basic C1603 es X7R: no sirve"),
 ("Etapa final", "U106", "OPA836IDBVR SOT-23-6", "C111589", 2.2321, "ext", ""),
 ("Etapa final", "R127 R129 R130", "R_IN, R_F, VMID 10.0 kΩ 1 % 0603", "C25804", 0.0018, "basic", ""),
 ("Etapa final", "R128", "R_OFF = 7.5 kΩ + (8.06 kΩ) 1 % 0603", "C23234", 0.002, "basic", "§2.10"),
 ("Etapa final", "R146", "R_OFF = + 560 Ω 1 % 0603", "C23204", 0.002, "basic", "§2.10"),
 ("Etapa final", "R131", "VMID = 5.1 kΩ + (5.23 kΩ) 1 % 0603", "C23186", 0.002, "basic", "§2.10"),
 ("Etapa final", "R147", "VMID = + 120 Ω 1 % 0603", "C22787", 0.002, "basic", "§2.10"),
 ("Etapa final", "C113", "C_F 1 pF C0G 50 V 0603 (FOJAN)", "C5137611", 0.0041, "ext", ""),
 ("Etapa final", "C114", "1 µF X5R 50 V 0603 (Samsung)", "C15849", 0.0168, "basic", ""),
 ("Etapa final", "R132", "R_ADC 68 Ω 1 % 0603", "C27592", 0.0013, "basic", "preferred"),
 ("Etapa final", "C115", "C_ADC 470 pF ±5 % C0G 50 V 0603 (FH)", "C36252", 0.0097, "ext", ""),
 ("Desacoplo", "C116 C117 C118 C119 C120 C121 C122 C123 C124", "100 nF X7R 16 V 0402 (Samsung)", "C1525", 0.0045, "basic", ""),
 ("Desacoplo", "C125 C126", "10 µF X5R 25 V 0805 (Samsung)", "C15850", 0.0651, "basic", ""),
]
here = os.path.dirname(os.path.abspath(__file__))
rows = []
for blk, refs, desc, lcsc, pu, tipo, nota in L:
    q = len(refs.split())
    rows.append(dict(bloque=blk, refs=refs, cant=q, descripcion=desc, lcsc=lcsc, tipo=tipo,
                     precio_unidad_usd=round(pu, 4), subtotal_usd=round(q * pu, 4), nota=nota))
with open(os.path.join(here, "CH1_BOM_precios.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
tot = sum(r["subtotal_usd"] for r in rows)
piezas = sum(r["cant"] for r in rows if r["tipo"] != "dnp")
print(f"Piezas montadas: {piezas}   Líneas: {len(rows)}   Total CH1: {tot:.2f} USD")
blk = {}
for r in rows: blk[r["bloque"]] = blk.get(r["bloque"], 0) + r["subtotal_usd"]
for k, v in blk.items(): print(f"  {k:22s} {v:6.2f} USD  ({100*v/tot:4.1f} %)")
amps = sum(r["subtotal_usd"] for r in rows if r["refs"] in ("U101", "U103", "U105", "U106"))
print(f"Amplificadores: {amps:.2f} USD ({100*amps/tot:.0f} %)")
ext = {r["lcsc"] for r in rows if r["tipo"] == "ext"}
assert not any(r["lcsc"] in ("por elegir",) for r in rows), "quedan códigos por elegir"
print(f"Referencias extendidas distintas (conocidas): {len(ext)}")
