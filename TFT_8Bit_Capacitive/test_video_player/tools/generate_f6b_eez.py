import json
import uuid
import os
import subprocess

BASE_DIR = r"C:\Users\Keneth\Desktop\S3G4 LAB\TFT_8Bit_Capacitive\test_video_player"
PROJ_PATH = os.path.join(BASE_DIR, "video_player", "video_player.eez-project")

with open(PROJ_PATH, 'r', encoding='utf-8') as f:
    proj = json.load(f)

# Helper functions for EEZ Studio JSON tree
def uid():
    return str(uuid.uuid4())

def make_style_ref():
    return {"objID": uid(), "conditionalStyles": [], "childStyles": []}

def make_local_styles(part_defs=None):
    return {"objID": uid(), "definition": part_defs or {}}

def make_event_handler(event_name, action_name):
    return {
        "objID": uid(),
        "eventName": event_name,
        "handlerType": "action",
        "action": action_name
    }

def make_container(left, top, width, height, identifier=None, use_style=None, hidden=False, clickable=False, bg_color=None, bg_opa=255, border_width=0, border_color=None, radius=0, children=None, event_handlers=None, scrollbar_mode="off"):
    local_def = {}
    main_def = {}
    if bg_color is not None:
        main_def["bg_color"] = bg_color
        main_def["bg_opa"] = bg_opa
    if border_width > 0:
        main_def["border_width"] = border_width
        if border_color:
            main_def["border_color"] = border_color
    if radius > 0:
        main_def["radius"] = radius
    main_def["pad_top"] = 0
    main_def["pad_bottom"] = 0
    main_def["pad_left"] = 0
    main_def["pad_right"] = 0
    if main_def:
        local_def["MAIN"] = {"DEFAULT": main_def}

    flags = "PRESS_LOCK|CLICK_FOCUSABLE|GESTURE_BUBBLE|SNAPPABLE"
    if clickable:
        flags = "CLICKABLE|" + flags

    obj = {
        "objID": uid(),
        "type": "LVGLContainerWidget",
        "left": left,
        "top": top,
        "width": width,
        "height": height,
        "leftUnit": "px",
        "topUnit": "px",
        "widthUnit": "px",
        "heightUnit": "px",
        "style": make_style_ref(),
        "widgetFlags": flags,
        "flagScrollbarMode": scrollbar_mode,
        "hiddenFlagType": "literal",
        "hiddenFlag": hidden,
        "localStyles": make_local_styles(local_def),
        "eventHandlers": event_handlers or [],
        "children": children or []
    }
    if identifier:
        obj["identifier"] = identifier
    if use_style:
        obj["useStyle"] = use_style
    return obj

def make_label(left, top, width, height, text="", font=None, color=None, align="LEFT", identifier=None, hidden=False, long_mode="CLIP"):
    main_def = {}
    if font:
        main_def["text_font"] = font
    if color:
        main_def["text_color"] = color
    if align != "LEFT":
        main_def["text_align"] = align
    local_def = {"MAIN": {"DEFAULT": main_def}} if main_def else {}

    obj = {
        "objID": uid(),
        "type": "LVGLLabelWidget",
        "left": left,
        "top": top,
        "width": width,
        "height": height,
        "leftUnit": "px",
        "topUnit": "px",
        "widthUnit": "px",
        "heightUnit": "px",
        "style": make_style_ref(),
        "widgetFlags": "CLICKABLE",
        "flagScrollbarMode": "off",
        "hiddenFlagType": "literal",
        "hiddenFlag": hidden,
        "localStyles": make_local_styles(local_def),
        "eventHandlers": [],
        "children": [],
        "text": text,
        "textType": "literal",
        "longMode": long_mode
    }
    if identifier:
        obj["identifier"] = identifier
    return obj

def make_button(left, top, width, height, identifier=None, use_style="st_icon_btn", action_name=None, children=None, hidden=False):
    evts = [make_event_handler("CLICKED", action_name)] if action_name else []
    obj = {
        "objID": uid(),
        "type": "LVGLButtonWidget",
        "left": left,
        "top": top,
        "width": width,
        "height": height,
        "leftUnit": "px",
        "topUnit": "px",
        "widthUnit": "px",
        "heightUnit": "px",
        "style": make_style_ref(),
        "widgetFlags": "CLICKABLE|PRESS_LOCK|CLICK_FOCUSABLE|GESTURE_BUBBLE|SNAPPABLE",
        "flagScrollbarMode": "off",
        "hiddenFlagType": "literal",
        "hiddenFlag": hidden,
        "localStyles": make_local_styles(),
        "eventHandlers": evts,
        "children": children or []
    }
    if identifier:
        obj["identifier"] = identifier
    if use_style:
        obj["useStyle"] = use_style
    return obj

def make_image(left, top, width, height, image_name, recolor="c_text", recolor_opa=255, identifier=None):
    local_def = {}
    if recolor:
        local_def["MAIN"] = {"DEFAULT": {"image_recolor": recolor, "image_recolor_opa": recolor_opa}}
    obj = {
        "objID": uid(),
        "type": "LVGLImageWidget",
        "left": left,
        "top": top,
        "width": width,
        "height": height,
        "leftUnit": "px",
        "topUnit": "px",
        "widthUnit": "px",
        "heightUnit": "px",
        "style": make_style_ref(),
        "widgetFlags": "CLICKABLE",
        "flagScrollbarMode": "off",
        "hiddenFlagType": "literal",
        "hiddenFlag": False,
        "localStyles": make_local_styles(local_def),
        "eventHandlers": [],
        "children": [],
        "image": image_name,
        "setPivot": False,
        "zoom": 256,
        "angle": 0,
        "innerAlign": "CENTER"
    }
    if identifier:
        obj["identifier"] = identifier
    return obj

def make_slider(left, top, width, height, identifier=None, use_style="st_seek", min_val=0, max_val=1000, value=0, action_name=None):
    evts = [make_event_handler("VALUE_CHANGED", action_name)] if action_name else []
    obj = {
        "objID": uid(),
        "type": "LVGLSliderWidget",
        "left": left,
        "top": top,
        "width": width,
        "height": height,
        "leftUnit": "px",
        "topUnit": "px",
        "widthUnit": "px",
        "heightUnit": "px",
        "style": make_style_ref(),
        "widgetFlags": "CLICKABLE|PRESS_LOCK|CLICK_FOCUSABLE|GESTURE_BUBBLE|SNAPPABLE",
        "flagScrollbarMode": "off",
        "hiddenFlagType": "literal",
        "hiddenFlag": False,
        "localStyles": make_local_styles(),
        "eventHandlers": evts,
        "children": [],
        "min": min_val,
        "minType": "literal",
        "max": max_val,
        "maxType": "literal",
        "mode": "NORMAL",
        "value": str(value),
        "valueType": "literal",
        "previewValue": str(value),
        "valueLeft": 0,
        "valueLeftType": "literal",
        "previewValueLeft": "0"
    }
    if identifier:
        obj["identifier"] = identifier
    if use_style:
        obj["useStyle"] = use_style
    return obj

def make_bar(left, top, width, height, identifier=None, min_val=0, max_val=1000, value=0, hidden=False, bg_color="c_line", indic_color="c_accent", radius=3):
    local_def = {
        "MAIN": {"DEFAULT": {"bg_color": bg_color, "bg_opa": 255, "radius": radius}},
        "INDICATOR": {"DEFAULT": {"bg_color": indic_color, "bg_opa": 255, "radius": radius}}
    }
    obj = {
        "objID": uid(),
        "type": "LVGLBarWidget",
        "left": left,
        "top": top,
        "width": width,
        "height": height,
        "leftUnit": "px",
        "topUnit": "px",
        "widthUnit": "px",
        "heightUnit": "px",
        "style": make_style_ref(),
        "widgetFlags": "CLICKABLE",
        "flagScrollbarMode": "off",
        "hiddenFlagType": "literal",
        "hiddenFlag": hidden,
        "localStyles": make_local_styles(local_def),
        "eventHandlers": [],
        "children": [],
        "min": min_val,
        "minType": "literal",
        "max": max_val,
        "maxType": "literal",
        "mode": "NORMAL",
        "value": str(value),
        "valueType": "literal"
    }
    if identifier:
        obj["identifier"] = identifier
    return obj

def make_switch(left, top, width, height, identifier=None, action_name=None):
    evts = [make_event_handler("VALUE_CHANGED", action_name)] if action_name else []
    obj = {
        "objID": uid(),
        "type": "LVGLSwitchWidget",
        "left": left,
        "top": top,
        "width": width,
        "height": height,
        "leftUnit": "px",
        "topUnit": "px",
        "widthUnit": "px",
        "heightUnit": "px",
        "style": make_style_ref(),
        "widgetFlags": "CLICKABLE|CHECKABLE|PRESS_LOCK|CLICK_FOCUSABLE|GESTURE_BUBBLE|SNAPPABLE",
        "flagScrollbarMode": "off",
        "hiddenFlagType": "literal",
        "hiddenFlag": False,
        "localStyles": make_local_styles(),
        "eventHandlers": evts,
        "children": []
    }
    if identifier:
        obj["identifier"] = identifier
    return obj

def make_dropdown(left, top, width, height, options_str, identifier=None, action_name=None):
    evts = [make_event_handler("VALUE_CHANGED", action_name)] if action_name else []
    obj = {
        "objID": uid(),
        "type": "LVGLDropdownWidget",
        "left": left,
        "top": top,
        "width": width,
        "height": height,
        "leftUnit": "px",
        "topUnit": "px",
        "widthUnit": "px",
        "heightUnit": "px",
        "style": make_style_ref(),
        "widgetFlags": "CLICKABLE|PRESS_LOCK|CLICK_FOCUSABLE|GESTURE_BUBBLE|SNAPPABLE",
        "flagScrollbarMode": "off",
        "hiddenFlagType": "literal",
        "hiddenFlag": False,
        "localStyles": make_local_styles(),
        "eventHandlers": evts,
        "children": [],
        "options": options_str,
        "optionsType": "literal",
        "selected": 0,
        "selectedType": "literal"
    }
    if identifier:
        obj["identifier"] = identifier
    return obj

# 1. Update ui.c build template to use lv_screen_load without fade delay
for bf in proj.get('settings', {}).get('build', {}).get('files', []):
    if bf.get('fileName') == 'ui.c':
        t = bf.get('template', '')
        t = t.replace('lv_scr_load_anim(screen, LV_SCR_LOAD_ANIM_FADE_IN, 200, 0, false);', 'lv_screen_load(screen);')
        bf['template'] = t

# 2. Add overlays to scr_player
for page in proj['userPages']:
    if page['name'] == 'scr_player':
        root_screen = page['components'][0]
        # Check existing children identifiers
        existing_ids = {c.get('identifier') for c in root_screen.get('children', [])}
        
        # ovl_lock: 0, 0, 480, 320, hidden
        if 'ovl_lock' not in existing_ids:
            root_screen['children'].append(
                make_container(0, 0, 480, 320, identifier="ovl_lock", hidden=True, clickable=True)
            )
        
        # ovl_brightness: 16, 70, 40, 180, hidden, use_style="st_card"
        if 'ovl_brightness' not in existing_ids:
            ovl_b_children = [
                make_image(10, 6, 20, 20, "brightness", recolor="c_text"),
                make_bar(12, 32, 16, 120, identifier="bar_brightness", min_val=10, max_val=100, value=70, radius=8),
                make_label(0, 158, 40, 16, text="70%", font="montserrat_12", color="c_text", align="CENTER", identifier="lbl_bri")
            ]
            root_screen['children'].append(
                make_container(16, 70, 40, 180, identifier="ovl_brightness", use_style="st_card", hidden=True, children=ovl_b_children)
            )
        
        # ovl_seek_hint: 316, 116, 100, 88, hidden, use_style="st_card", radius=44
        if 'ovl_seek_hint' not in existing_ids:
            ovl_s_children = [
                make_image(38, 20, 24, 24, "seek_fwd", recolor="c_text", identifier="img_seek_hint"),
                make_label(0, 50, 100, 20, text="+10 s", font="montserrat_14", color="c_text", align="CENTER", identifier="lbl_seek_hint")
            ]
            root_screen['children'].append(
                make_container(316, 116, 100, 88, identifier="ovl_seek_hint", use_style="st_card", radius=44, hidden=True, children=ovl_s_children)
            )
            
        # ovl_stats: 12, 52, 212, 172, hidden, use_style="st_card"
        if 'ovl_stats' not in existing_ids:
            ovl_st_children = [
                make_label(12, 11, 100, 18, text="Rendimiento", font="montserrat_14", color="c_text"),
                make_button(168, 0, 44, 36, identifier="btn_stats_close", action_name="open_stats", children=[
                    make_image(14, 10, 16, 16, "close", recolor="c_muted")
                ]),
                make_label(12, 38, 80, 14, text="Presentados", font="montserrat_12", color="c_muted"),
                make_label(110, 38, 90, 14, text="30.0 fps", font="montserrat_12", color="c_accent", align="RIGHT", identifier="lbl_stat_pres"),
                make_label(12, 56, 80, 14, text="Decodificados", font="montserrat_12", color="c_muted"),
                make_label(110, 56, 90, 14, text="30.0 fps", font="montserrat_12", color="c_text", align="RIGHT", identifier="lbl_stat_dec"),
                make_label(12, 74, 80, 14, text="Descartados", font="montserrat_12", color="c_muted"),
                make_label(110, 74, 90, 14, text="0", font="montserrat_12", color="c_text", align="RIGHT", identifier="lbl_stat_drop"),
                make_label(12, 92, 80, 14, text="Lectura SD", font="montserrat_12", color="c_muted"),
                make_label(100, 92, 100, 14, text="5.1 / 9.4 ms", font="montserrat_12", color="c_text", align="RIGHT", identifier="lbl_stat_rd"),
                make_label(12, 110, 80, 14, text="Decodificación", font="montserrat_12", color="c_muted"),
                make_label(100, 110, 100, 14, text="21.8 / 27.0 ms", font="montserrat_12", color="c_text", align="RIGHT", identifier="lbl_stat_dec_time"),
                make_label(12, 128, 80, 14, text="Envío al panel", font="montserrat_12", color="c_muted"),
                make_label(110, 128, 90, 14, text="18.9 ms", font="montserrat_12", color="c_text", align="RIGHT", identifier="lbl_stat_blit"),
                make_label(12, 146, 60, 14, text="Archivo", font="montserrat_12", color="c_muted"),
                make_label(75, 146, 125, 14, text="480x320 · MJPEG", font="montserrat_12", color="c_text", align="RIGHT", identifier="lbl_stat_file")
            ]
            root_screen['children'].append(
                make_container(12, 52, 212, 172, identifier="ovl_stats", use_style="st_card", hidden=True, children=ovl_st_children)
            )

# 3. Build scr_queue if not exists
existing_pages = {p['name']: p for p in proj['userPages']}
if 'scr_queue' not in existing_pages:
    q_footer_children = [
        make_button(12, 0, 44, 44, identifier="btn_q_repeat", action_name="cycle_repeat", children=[
            make_image(12, 12, 20, 20, "repeat", recolor="c_muted", identifier="img_q_repeat")
        ]),
        make_button(60, 0, 44, 44, identifier="btn_q_shuffle", action_name="toggle_shuffle", children=[
            make_image(12, 12, 20, 20, "shuffle", recolor="c_muted", identifier="img_q_shuffle")
        ]),
        make_label(112, 14, 140, 16, text="Repetir todo", font="montserrat_12", color="c_muted", identifier="lbl_q_mode")
    ]
    
    q_sheet_children = [
        make_label(16, 12, 120, 20, text="A continuación", font="montserrat_14", color="c_text", identifier="lbl_queue_title"),
        make_button(216, 0, 44, 44, identifier="btn_queue_close", action_name="close_queue", children=[
            make_image(13, 13, 18, 18, "close", recolor="c_text")
        ]),
        make_container(0, 44, 260, 232, identifier="queue_list", scrollbar_mode="auto"),
        make_container(0, 276, 260, 44, identifier="queue_footer", use_style="st_bar", children=q_footer_children)
    ]
    
    scr_queue_comp = {
        "objID": uid(),
        "type": "LVGLScreenWidget",
        "left": 0, "top": 0, "width": 480, "height": 320,
        "leftUnit": "px", "topUnit": "px", "widthUnit": "px", "heightUnit": "px",
        "useStyle": "st_screen",
        "style": make_style_ref(),
        "widgetFlags": "CLICKABLE|PRESS_LOCK|CLICK_FOCUSABLE|GESTURE_BUBBLE|SNAPPABLE",
        "flagScrollbarMode": "off",
        "hiddenFlagType": "literal",
        "hiddenFlag": False,
        "localStyles": make_local_styles(),
        "eventHandlers": [],
        "children": [
            make_container(0, 0, 220, 320, identifier="queue_scrim", clickable=True, bg_color="0x000000", bg_opa=153, event_handlers=[make_event_handler("CLICKED", "close_queue")]),
            make_container(220, 0, 260, 320, identifier="queue_sheet", use_style="st_card", children=q_sheet_children)
        ]
    }
    
    proj['userPages'].append({
        "objID": uid(),
        "name": "scr_queue",
        "left": 0, "top": 0, "width": 480, "height": 320,
        "createAtStart": True,
        "deleteOnScreenUnload": False,
        "components": [scr_queue_comp]
    })
    print("Added scr_queue")

# 4. Build scr_settings if not exists
if 'scr_settings' not in existing_pages:
    # Nav buttons on left
    nav_children = [
        make_button(0, 0, 44, 44, identifier="btn_back_settings", action_name="open_library", children=[
            make_image(12, 12, 20, 20, "back", recolor="c_text")
        ]),
        make_label(44, 13, 100, 18, text="Ajustes", font="montserrat_14", color="c_text"),
        make_button(0, 52, 149, 48, identifier="btn_tab_0", action_name="settings_tab", children=[
            make_label(16, 16, 120, 16, text="Pantalla", font="montserrat_14", color="c_accent", identifier="lbl_tab_0")
        ]),
        make_button(0, 100, 149, 48, identifier="btn_tab_1", action_name="settings_tab", children=[
            make_label(16, 16, 120, 16, text="Reproducción", font="montserrat_14", color="c_text", identifier="lbl_tab_1")
        ]),
        make_button(0, 148, 149, 48, identifier="btn_tab_2", action_name="settings_tab", children=[
            make_label(16, 16, 120, 16, text="Almacenamiento", font="montserrat_14", color="c_text", identifier="lbl_tab_2")
        ]),
        make_button(0, 196, 149, 48, identifier="btn_tab_3", action_name="settings_tab", children=[
            make_label(16, 16, 120, 16, text="Acerca de", font="montserrat_14", color="c_text", identifier="lbl_tab_3")
        ])
    ]
    
    # Tab 0: Pantalla
    tab0_children = [
        make_label(16, 16, 100, 16, text="Brillo", font="montserrat_14", color="c_text"),
        make_label(260, 16, 50, 16, text="100%", font="montserrat_14", color="c_muted", align="RIGHT", identifier="lbl_set_bri_val"),
        make_slider(16, 42, 298, 4, identifier="sld_brightness", min_val=10, max_val=100, value=100, action_name="set_brightness"),
        
        make_label(16, 75, 180, 16, text="Ocultar controles tras", font="montserrat_14", color="c_text"),
        make_dropdown(220, 68, 94, 32, "2 s\n3 s\n5 s\nNunca", identifier="dd_osd_timeout", action_name="set_osd_timeout"),
        
        make_label(16, 130, 200, 16, text="Mostrar FPS en la OSD", font="montserrat_14", color="c_text"),
        make_switch(270, 126, 44, 24, identifier="sw_show_stats", action_name="set_show_stats"),
        
        make_label(16, 185, 200, 16, text="Barra de progreso mínima", font="montserrat_14", color="c_text"),
        make_switch(270, 181, 44, 24, identifier="sw_mini_progress", action_name="set_mini_progress")
    ]
    
    # Tab 1: Reproduccion
    tab1_children = [
        make_label(16, 16, 100, 16, text="Repetir", font="montserrat_14", color="c_text"),
        make_dropdown(180, 10, 134, 32, "Desactivado\nRepetir todo\nRepetir uno", identifier="dd_repeat", action_name="set_repeat"),
        
        make_label(16, 75, 100, 16, text="Aleatorio", font="montserrat_14", color="c_text"),
        make_switch(270, 71, 44, 24, identifier="sw_shuffle", action_name="set_shuffle"),
        
        make_label(16, 125, 200, 16, text="Continuar donde lo dejé", font="montserrat_14", color="c_text"),
        make_label(16, 145, 220, 14, text="Guarda la posición de cada video", font="montserrat_12", color="c_muted"),
        make_switch(270, 130, 44, 24, identifier="sw_resume", action_name="set_resume"),
        
        make_label(16, 195, 200, 16, text="Salto de los botones ⟲ ⟳", font="montserrat_14", color="c_text"),
        make_dropdown(230, 189, 84, 32, "5 s\n10 s\n30 s", identifier="dd_seek_step", action_name="set_seek_step")
    ]
    
    # Tab 2: Almacenamiento
    card_sd_children = [
        make_image(12, 28, 32, 32, "sdcard", recolor="c_muted"),
        make_label(56, 12, 160, 16, text="microSD SDHC 32 GB", font="montserrat_14", color="c_text", identifier="lbl_sd_name"),
        make_label(220, 12, 66, 16, text="FAT32", font="montserrat_12", color="c_muted", align="RIGHT", identifier="lbl_sd_fs"),
        make_bar(56, 36, 230, 6, identifier="bar_sd_usage", min_val=0, max_val=1000, value=250),
        make_label(56, 50, 230, 14, text="Calculando espacio...", font="montserrat_12", color="c_muted", identifier="lbl_sd_free")
    ]
    tab2_children = [
        make_container(16, 16, 298, 88, identifier="card_sd", use_style="st_card", children=card_sd_children),
        make_label(16, 120, 140, 16, text="Velocidad del bus", font="montserrat_14", color="c_text"),
        make_label(180, 120, 134, 16, text="SPI · 20 MHz", font="montserrat_14", color="c_muted", align="RIGHT", identifier="lbl_sd_speed"),
        make_label(16, 165, 160, 16, text="Videos encontrados", font="montserrat_14", color="c_text"),
        make_label(180, 165, 134, 16, text="4 en /videos", font="montserrat_14", color="c_muted", align="RIGHT", identifier="lbl_sd_count"),
        make_button(16, 215, 160, 44, identifier="btn_rescan", use_style="st_card_btn", action_name="rescan", children=[
            make_image(14, 14, 16, 16, "rescan", recolor="c_accent"),
            make_label(38, 14, 115, 16, text="Volver a escanear", font="montserrat_12", color="c_accent")
        ])
    ]
    
    # Tab 3: Acerca de
    tab3_children = [
        make_label(16, 12, 298, 24, text="S3G4 Video", font="montserrat_20", color="c_text"),
        make_label(16, 36, 298, 14, text="Reproductor de video embebido", font="montserrat_12", color="c_muted"),
        make_label(16, 68, 100, 15, text="Firmware", font="montserrat_12", color="c_muted"),
        make_label(180, 68, 134, 15, text="vp-v0.8", font="montserrat_12", color="c_text", align="RIGHT", identifier="lbl_about_fw"),
        make_label(16, 96, 100, 15, text="ESP-IDF", font="montserrat_12", color="c_muted"),
        make_label(180, 96, 134, 15, text="6.0.1", font="montserrat_12", color="c_text", align="RIGHT", identifier="lbl_about_idf"),
        make_label(16, 124, 100, 15, text="LVGL", font="montserrat_12", color="c_muted"),
        make_label(180, 124, 134, 15, text="9.5.0", font="montserrat_12", color="c_text", align="RIGHT", identifier="lbl_about_lvgl"),
        make_label(16, 152, 80, 15, text="Panel", font="montserrat_12", color="c_muted"),
        make_label(100, 152, 214, 15, text="ILI9488 · 8080 8 bits · 16 MHz", font="montserrat_12", color="c_text", align="RIGHT", identifier="lbl_about_panel"),
        make_label(16, 180, 80, 15, text="Sincronía", font="montserrat_12", color="c_muted"),
        make_label(100, 180, 214, 15, text="TE en GPIO 7 · 46 Hz", font="montserrat_12", color="c_text", align="RIGHT", identifier="lbl_about_te"),
        make_button(16, 220, 140, 44, identifier="btn_open_stats", use_style="st_card_btn", action_name="open_stats", children=[
            make_label(10, 14, 120, 16, text="Ver rendimiento", font="montserrat_14", color="c_accent", align="CENTER")
        ])
    ]
    
    panels_container = make_container(150, 0, 330, 320, identifier="settings_panel", children=[
        make_container(0, 0, 330, 320, identifier="panel_tab_0", children=tab0_children),
        make_container(0, 0, 330, 320, identifier="panel_tab_1", hidden=True, children=tab1_children),
        make_container(0, 0, 330, 320, identifier="panel_tab_2", hidden=True, children=tab2_children),
        make_container(0, 0, 330, 320, identifier="panel_tab_3", hidden=True, children=tab3_children)
    ])
    
    scr_settings_comp = {
        "objID": uid(),
        "type": "LVGLScreenWidget",
        "left": 0, "top": 0, "width": 480, "height": 320,
        "leftUnit": "px", "topUnit": "px", "widthUnit": "px", "heightUnit": "px",
        "useStyle": "st_screen",
        "style": make_style_ref(),
        "widgetFlags": "CLICKABLE|PRESS_LOCK|CLICK_FOCUSABLE|GESTURE_BUBBLE|SNAPPABLE",
        "flagScrollbarMode": "off",
        "hiddenFlagType": "literal",
        "hiddenFlag": False,
        "localStyles": make_local_styles(),
        "eventHandlers": [],
        "children": [
            make_container(0, 0, 150, 320, identifier="settings_nav", children=nav_children),
            panels_container
        ]
    }
    
    proj['userPages'].append({
        "objID": uid(),
        "name": "scr_settings",
        "left": 0, "top": 0, "width": 480, "height": 320,
        "createAtStart": True,
        "deleteOnScreenUnload": False,
        "components": [scr_settings_comp]
    })
    print("Added scr_settings")

with open(PROJ_PATH, 'w', encoding='utf-8') as f:
    json.dump(proj, f, indent=4)

print("video_player.eez-project updated successfully.")
