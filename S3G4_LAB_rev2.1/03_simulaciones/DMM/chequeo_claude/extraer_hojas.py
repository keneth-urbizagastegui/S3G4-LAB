"""Vuelca el texto por pagina de las hojas citadas (solo lectura) a una carpeta de salida."""
import fitz, sys
from pathlib import Path
src = Path(r"C:\Users\Keneth\Desktop\S3G4 LAB\datasheet - componentes")
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
for n in ("ptctl","SMAJ12CA","DF08S","BAV199","74HC_HCT4051","opa2188","tlv2372","BSS84","C46047"):
    d = fitz.open(src/f"{n}.pdf")
    with open(out/f"{n}.txt","w",encoding="utf-8") as f:
        for i,p in enumerate(d,1):
            f.write(f"\n=====PAGINA {i}=====\n"+p.get_text())
    print(n, len(d))
