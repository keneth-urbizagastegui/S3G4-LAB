# Uso (desde 04_esquematicos/kicad): python lib/gen/gen_sym_er_tft035.py lib/s3g4.kicad_sym   (SOBRESCRIBE la librería: integrar a mano si ya tiene más símbolos)
# Símbolo ER-TFT035IPS-6-4405 (JP1, 40 pines). Patillaje: datasheet p.11-12, apartado 4.1.
import sys
NAME="ER-TFT035IPS-6-4405"
DS="${KIPRJMOD}/../../TFT_8Bit_Capacitive/ER-TFT035IPS-6-4405_Datasheet.pdf"
FP="s3g4:ER-TFT035IPS-6-4405_PinSocket_2x20_P2.54mm"
P=2.54
# (número, nombre, tipo); None = hueco
left=[(2,"VDD","power_in"),None,
      (21,"~{RESET}","input"),(23,"LCD_~{CS}","input"),(25,"D/~{C}","input"),(24,"~{WR}/SCL","input"),
      (26,"~{RD}","input"),(22,"TE","output"),(29,"BL_ON","input"),None,
      (27,"LCD_SDI","bidirectional"),(28,"LCD_SDO","output"),None,
      (30,"CTP_SCL/RTP_~{CS}","input"),(31,"CTP_SDA/RTP_~{PEN}","bidirectional"),(39,"CTP_~{INT}/FLASH_~{HOLD}","output")]
right=[(3+i,"DB%d"%i,"bidirectional") for i in range(18)]+[None,
      (33,"SCL","input"),(34,"SDI","input"),(32,"SDO","output"),
      (35,"SD_~{CS}","input"),(36,"FONT_~{CS}","input"),(37,"FLASH_~{CS}","input"),(38,"FLASH_~{WP}","input")]
rows=max(len(left)+3,len(right))           # +3: hueco y dos VSS abajo a la izquierda
top=(rows-1)/2*P; top=round(top/P)*P
bot=top-(rows-1)*P
left=left+[None]*(rows-len(left)-2)+[(1,"VSS","power_in"),(40,"VSS","power_in")]
W=17.78
f=lambda v:("%.3f"%v).rstrip('0').rstrip('.')
fx='(effects (font (size 1.27 1.27)))'
pins=[]
def pin(n,name,typ,x,y,ang):
    hide=' (hide yes)' if (n==40) else ''
    pins.append(f'\t\t\t(pin {typ} line (at {f(x)} {f(y)} {ang}) (length 5.08){hide} (name "{name}" {fx}) (number "{n}" {fx}))')
for i,p in enumerate(left):
    if p: pin(p[0],p[1],p[2],-W-5.08,top-i*P,0)
for i,p in enumerate(right):
    if p: pin(p[0],p[1],p[2],W+5.08,top-i*P,180)
# VSS pin 40: visible también (dos pines a GND); quitar hide
pins=[s.replace(' (hide yes)','') for s in pins]
def prop(k,v,x,y,hide=False):
    return f'\t\t(property "{k}" "{v}" (at {f(x)} {f(y)} 0){" (hide yes)" if hide else ""} {fx})'
out=f'''(kicad_symbol_lib
	(version 20251024)
	(generator "s3g4_gen_sym")
	(generator_version "10.0")
	(symbol "{NAME}"
		(exclude_from_sim no) (in_bom yes) (on_board yes)
{prop("Reference","DS",0,top+3.81)}
{prop("Value",NAME,0,bot-3.81)}
{prop("Footprint",FP,0,bot-6.35,True)}
{prop("Datasheet",DS,0,0,True)}
{prop("Description","Display TFT IPS 3.5in 320x480, ILI9488, tactil capacitivo FT6236 (I2C), placa breakout con conector JP1 2x20 2.54mm. Montado sobre zocalo hembra 2x20 y 4 separadores M2.5 x 11mm (comprar aparte)",0,0,True)}
{prop("MPN",NAME,0,0,True)}
{prop("Manufacturer","EastRising (BuyDisplay)",0,0,True)}
{prop("LCSC","",0,0,True)}
{prop("ki_keywords","TFT LCD display ILI9488 FT6236 8080 3.5in",0,0,True)}
		(symbol "{NAME}_0_1"
			(rectangle (start {f(-W)} {f(top+1.27)}) (end {f(W)} {f(bot-1.27)}) (stroke (width 0.254) (type default)) (fill (type background)))
		)
		(symbol "{NAME}_1_1"
{chr(10).join(pins)}
		)
		(embedded_fonts no)
	)
)
'''
open(sys.argv[1],'w',encoding='utf-8',newline='\n').write(out)
nums=sorted(p[0] for p in left+right if p)
assert nums==list(range(1,41)),nums
print('ok rows',rows,'top',top,'bot',bot)
