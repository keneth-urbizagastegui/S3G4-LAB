# Uso (desde 04_esquematicos/kicad): python lib/gen/gen_fp_er_tft035.py lib/s3g4.pretty/ER-TFT035IPS-6-4405_PinSocket_2x20_P2.54mm.kicad_mod 11 "95.2 -9.07 11.8" "0 0 -90"
# Offset/rotación del STEP verificados con kicad-cli pcb render el 2026-10-01.
# Genera la huella ER-TFT035IPS-6-4405 montado sobre zócalo hembra 2x20.
# Cotas: datasheet ER-TFT035IPS-6-4405, p. 9 (3.3, CTP + pin header), vista frontal.
import sys
P=2.54
# Origen = pin 1. Vista desde arriba de la placa base = vista frontal del display.
EDGE_L=-1.50; EDGE_R=EDGE_L+96.70        # PCB display 96.70 x 66.40; columna impar a 1.50 del borde
EDGE_T=-19*P-9.07; EDGE_B=EDGE_T+66.40   # fila 39/40 a 9.07 del borde superior
HX=(EDGE_L+12.50, EDGE_L+12.50+77.20)     # agujeros: 12.50 del borde, separación 77.20
HY=(EDGE_T+2.00, EDGE_T+2.00+62.40)       # 2.00 del borde, separación 62.40
DISP_Z=float(sys.argv[2]) if len(sys.argv)>2 else 11.0
MODEL_OFF=sys.argv[3] if len(sys.argv)>3 else "0 0 0"
MODEL_ROT=sys.argv[4] if len(sys.argv)>4 else "0 0 0"
f=lambda v: ("%.3f"%v).rstrip('0').rstrip('.')
o=[]
def line(x1,y1,x2,y2,layer,w):
    o.append(f'\t(fp_line (start {f(x1)} {f(y1)}) (end {f(x2)} {f(y2)}) (stroke (width {w}) (type solid)) (layer "{layer}"))')
def rect(x1,y1,x2,y2,layer,w):
    o.append(f'\t(fp_rect (start {f(x1)} {f(y1)}) (end {f(x2)} {f(y2)}) (stroke (width {w}) (type solid)) (fill no) (layer "{layer}"))')
def circ(x,y,r,layer,w):
    o.append(f'\t(fp_circle (center {f(x)} {f(y)}) (end {f(x+r)} {f(y)}) (stroke (width {w}) (type solid)) (fill no) (layer "{layer}"))')
def text(s,x,y,layer,size=1):
    o.append(f'\t(fp_text user "{s}" (at {f(x)} {f(y)} 0) (layer "{layer}") (effects (font (size {size} {size}) (thickness {f(size*0.15)}))))')
name="ER-TFT035IPS-6-4405_PinSocket_2x20_P2.54mm"
o.append(f'(footprint "{name}"\n\t(version 20260206)\n\t(generator "s3g4_gen_fp")\n\t(layer "F.Cu")')
o.append('\t(descr "Display EastRising/BuyDisplay ER-TFT035IPS-6-4405 (3.5in IPS, ILI9488, CTP) sobre zocalo hembra 2x20 2.54mm (JP1) y 4 separadores M2.5 x 11mm. Cotas: datasheet p.9, apartado 3.3, vista frontal. Display a 11mm (zocalo 8.5 + plastico tira macho 2.5)")')
o.append('\t(tags "display TFT 3.5in ER-TFT035IPS-6-4405 ILI9488 pin socket 2x20 standoff M2.5")')
for prop,val,y,lay,hide in (("Reference","REF**",EDGE_T-1.5,"F.SilkS",False),("Value",name,EDGE_B+1.5,"F.Fab",False),
        ("Datasheet","${KIPRJMOD}/../../TFT_8Bit_Capacitive/ER-TFT035IPS-6-4405_Datasheet.pdf",0,"F.Fab",True),
        ("Description","Display 3.5in ER-TFT035IPS-6-4405 sobre zocalo 2x20 y separadores M2.5",0,"F.Fab",True)):
    o.append(f'\t(property "{prop}" "{val}" (at {f(1.27 if prop!="Reference" else 1.27)} {f(y)} 0) (layer "{lay}"){" (hide yes)" if hide else ""} (effects (font (size 1 1) (thickness 0.15))))')
o.append('\t(attr through_hole)')
# F.Fab: contorno de la PCB del display, zócalo, agujeros
rect(EDGE_L,EDGE_T,EDGE_R,EDGE_B,"F.Fab",0.1)
rect(-1.27,1.27,3.81,-19*P-1.27,"F.Fab",0.1)
line(-1.27,0.27,-0.27,1.27,"F.Fab",0.1)
for x in HX:
    for y in HY: circ(x,y,1.4,"F.Fab",0.1)
text("${REFERENCE}",(EDGE_L+EDGE_R)/2,(EDGE_T+EDGE_B)/2,"F.Fab",2)
text("Display 96.7x66.4 a 11 mm",(EDGE_L+EDGE_R)/2,(EDGE_T+EDGE_B)/2+3,"F.Fab",1)
# Silk: contorno del display (zona tapada) y del zócalo, marca de pin 1
g=0.15
xl,xr,yt,yb=EDGE_L-g,EDGE_R+g,EDGE_T-g,EDGE_B+g
line(xl,yt,xl,yb,"F.SilkS",0.12); line(xr,yt,xr,yb,"F.SilkS",0.12)
cut=2.8                                   # hueco alrededor de los pads de 5 mm
for y in (yt,yb):
    xs=[xl,HX[0]-cut,HX[0]+cut,HX[1]-cut,HX[1]+cut,xr]
    for a,b in zip(xs[::2],xs[1::2]): line(a,y,b,y,"F.SilkS",0.12)
rect(-1.27-g,1.27+g,3.81+g,-19*P-1.27-g,"F.SilkS",0.12)
line(-1.27-g-0.6,1.27+g+0.6,-1.27-g-0.6,-0.3,"F.SilkS",0.12)
line(-1.27-g-0.6,1.27+g+0.6,0.3,1.27+g+0.6,"F.SilkS",0.12)
# Courtyard: proyección del display
c=0.25
rect(EDGE_L-c,EDGE_T-c,EDGE_R+c,EDGE_B+c,"F.CrtYd",0.05)
# Pads JP1: impares en x=0, pares en x=+2.54; numeración hacia -y
for n in range(1,41):
    row=(n-1)//2; x=0 if n%2 else P; y=-row*P
    shape="rect" if n==1 else "circle"
    o.append(f'\t(pad "{n}" thru_hole {shape} (at {f(x)} {f(y)}) (size 1.7 1.7) (drill 1) (layers "*.Cu" "*.Mask") (remove_unused_layers no))')
# Separadores M2.5: agujero 2.7 metalizado, pad "MP" (pin MP del símbolo, a GND digital)
for x in HX:
    for y in HY:
        o.append(f'\t(pad "MP" thru_hole circle (at {f(x)} {f(y)}) (size 5 5) (drill 2.7) (layers "*.Cu" "*.Mask") (remove_unused_layers no))')
        circ(x,y,2.75,"F.CrtYd",0.05)
o.append('\t(embedded_fonts no)')
o.append('\t(model "${KICAD10_3DMODEL_DIR}/Connector_PinSocket_2.54mm.3dshapes/PinSocket_2x20_P2.54mm_Vertical.step"\n\t\t(offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 180)))')
# Tira macho del display (el STEP de BuyDisplay no la trae): invertida, plástico entre 8.5 y 11 mm
o.append('\t(model "${KICAD10_3DMODEL_DIR}/Connector_PinHeader_2.54mm.3dshapes/PinHeader_2x20_P2.54mm_Vertical.step"\n\t\t(offset (xyz 0 0 11)) (scale (xyz 1 1 1)) (rotate (xyz 180 0 0)))')
o.append(f'\t(model "{sys.argv[5] if len(sys.argv)>5 else "${KIPRJMOD}/lib/3d/ER-TFTM035-6_3D.step"}"\n\t\t(offset (xyz {MODEL_OFF})) (scale (xyz 1 1 1)) (rotate (xyz {MODEL_ROT})))')
o.append(')')
open(sys.argv[1],'w',encoding='utf-8',newline='\n').write('\n'.join(o)+'\n')
print('ok',HX,HY,EDGE_L,EDGE_R,EDGE_T,EDGE_B)
