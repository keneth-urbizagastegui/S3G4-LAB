import sys, re, pymupdf, importlib
ST = {
 "w":'fill="none" stroke="#1b2a2e" stroke-width="1.5"', "sym":'fill="none" stroke="#1b2a2e" stroke-width="1.6"',
 "fillsym":'fill="#1b2a2e" stroke="#1b2a2e"', "dot":'fill="#1b2a2e"', "op":'fill="#ffffff" stroke="#1b2a2e" stroke-width="1.7"',
 "ic":'fill="#ffffff" stroke="#1b2a2e" stroke-width="1.5"', "blk":'fill="#ffffff" stroke="#1b2a2e" stroke-width="1.5"',
 "grp":'fill="none" stroke="#5d6d72" stroke-dasharray="5 4"', "blade":'stroke="#1b2a2e" stroke-width="2"',
 "ct":'fill="#ffffff" stroke="#1b2a2e"', "gnd":'stroke="#1b2a2e" stroke-width="1.5"', "railbar":'stroke="#b22d22" stroke-width="2.2"',
 "rail":'font-size="10.5" fill="#b22d22"', "railsm":'font-size="9" fill="#b22d22"', "port":'fill="#d6e8ee" stroke="#12667f"',
 "portt":'font-size="10.5" fill="#1b2a2e"', "tp":'fill="none" stroke="#2f7d54"', "tpt":'font-size="9.5" fill="#2f7d54"',
 "ref":'font-size="11" font-weight="bold" fill="#1b2a2e"', "val":'font-size="10" fill="#5d6d72"', "net":'font-size="10" fill="#a9541c"',
 "pin":'font-size="9.5" fill="#5d6d72"', "pm":'font-size="15" fill="#1b2a2e"', "note":'font-size="10.5" fill="#5d6d72" font-style="italic"',
 "grp-t":'font-size="10.5" fill="#5d6d72"', "hdr":'fill="none" stroke="#6a4fa3" stroke-dasharray="3 2"', "ban":'fill="none" stroke-width="2"'}
def inline(svg):
    return re.sub(r'class="([^"]+)"', lambda m: m.group(0)+" "+ST.get(m.group(1).split()[0],""), svg)
mod = importlib.import_module(sys.argv[1])
for fn in sys.argv[2:]:
    svg = inline(getattr(mod, fn)())
    vb = re.search(r'viewBox="0 0 (\d+) (\d+)"', svg); W,H = vb.groups()
    svg = svg.replace('<svg ', f'<svg height="{H}" ', 1).replace('font-family', 'font-family')
    svg = re.sub(r'(<svg[^>]*>)', r'\1<rect width="100%" height="100%" fill="#ffffff"/>', svg, count=1)
    open(f"view_{fn}.svg","w",encoding="utf-8").write(svg)
    d = pymupdf.open(f"view_{fn}.svg"); pix = d[0].get_pixmap(dpi=96); pix.save(f"view_{fn}.png"); print(fn, pix.width, pix.height)
