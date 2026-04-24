import flet as ft
import os
import tkinter as tk
from tkinter import filedialog, colorchooser
from PIL import Image, ImageDraw, ImageFont
import io, base64

def abrir_gerador_capa(page: ft.Page, titulo_evento: str):
    DEFAULT_BG = r"L:\transmissoes\assets\Capa de transmissão 2026.png"
    EDGE = 14

    state = {
        "img_bg": None, "bg_color": "#FFFFFF",
        "layers": [{
            "text": titulo_evento, "font_size": 60, "font_color": "#000000",
            "box_x": 100, "box_y": 180, "box_w": 1080, "box_h": 360,
            "letter_spacing": 0, "word_spacing": 0, "stroke_width": 0,
            "bold": True, "font_family": "Arial", "alignment": "Centralizado"
        }],
        "idx": 0, "fc": {}, "bboxes": []
    }

    if os.path.exists(DEFAULT_BG):
        try: state["img_bg"] = Image.open(DEFAULT_BG)
        except: pass

    def rs():
        if hasattr(Image, "Resampling"): return Image.Resampling.LANCZOS
        return getattr(Image, "LANCZOS", Image.ANTIALIAS)

    def gf(name, size, bold):
        k = f"{name}_{size}_{bold}"
        if k in state["fc"]: return state["fc"][k]
        fm = {"Arial":("arial.ttf","arialbd.ttf"),"Impact":("impact.ttf","impact.ttf"),
              "Verdana":("verdana.ttf","verdanab.ttf"),"Georgia":("georgia.ttf","georgiab.ttf"),
              "Times New Roman":("times.ttf","timesbd.ttf"),"Courier New":("cour.ttf","courbd.ttf")}
        r, b = fm.get(name, fm["Arial"])
        try: f = ImageFont.truetype(b if bold else r, int(size)); state["fc"][k] = f; return f
        except:
            try: return ImageFont.truetype("arial.ttf", int(size))
            except: return ImageFont.load_default()

    def mt(draw, txt, font):
        try: b = draw.textbbox((0,0), txt, font=font); return b[2]-b[0]
        except: return draw.textsize(txt, font=font)[0]

    def render(final=False):
        W, H = 1280, 720
        if state["img_bg"]:
            img = state["img_bg"].copy(); ratio = img.width/img.height; tr = W/H
            if ratio > tr: nh = H; nw = int(H*ratio)
            else: nw = W; nh = int(W/ratio)
            img = img.resize((nw, nh), rs())
            img = img.crop(((nw-W)//2, (nh-H)//2, (nw-W)//2+W, (nh-H)//2+H))
        else: img = Image.new("RGB", (W, H), state["bg_color"])
        draw = ImageDraw.Draw(img); state["bboxes"] = []

        for i, ly in enumerate(state["layers"]):
            font = gf(ly["font_family"], ly["font_size"], ly["bold"])
            ls, ws = ly["letter_spacing"], ly["word_spacing"]
            bx, by, bw, bh = ly["box_x"], ly["box_y"], ly["box_w"], ly["box_h"]
            lines = []
            for p in ly["text"].split('\n'):
                if not p: lines.append(""); continue
                cur = []
                for w in p.split(' '):
                    t = " ".join(cur+[w]) if cur else w
                    tw = mt(draw, t, font) + (len(t)-1)*ls + t.count(' ')*ws
                    if tw < bw - 10: cur.append(w)
                    else:
                        if cur: lines.append(" ".join(cur)); cur = [w]
                        else: lines.append(w)
                if cur: lines.append(" ".join(cur))

            lh = ly["font_size"]*1.2; cy = by
            for line in lines:
                lw = mt(draw, line, font) + (len(line)-1)*ls + line.count(' ')*ws
                if ly["alignment"]=="Centralizado": cx = bx + (bw - lw)/2
                elif ly["alignment"]=="Esquerda": cx = bx
                else: cx = bx + bw - lw
                sw = int(ly["stroke_width"])
                for ch in line:
                    if sw > 0:
                        try: draw.text((cx, cy), ch, font=font, fill=ly["font_color"], stroke_width=sw, stroke_fill="black")
                        except:
                            for ddx, ddy in [(-1,0),(1,0),(0,-1),(0,1)]: draw.text((cx+ddx, cy+ddy), ch, font=font, fill="black")
                            draw.text((cx, cy), ch, font=font, fill=ly["font_color"])
                    else:
                        draw.text((cx+2, cy+2), ch, font=font, fill="black")
                        draw.text((cx, cy), ch, font=font, fill=ly["font_color"])
                    cx += mt(draw, ch, font) + ls + (ws if ch==' ' else 0)
                cy += lh

            # bbox no espaço da preview (640x360 = metade)
            state["bboxes"].append({"x": bx/2, "y": by/2, "w": bw/2, "h": bh/2})

            if not final and i == state["idx"]:
                draw.rectangle([bx-3, by-3, bx+bw+3, by+bh+3], outline="#00BBFF", width=2)
                s = 12
                for seg in [(bx-3,by-3,bx+s,by-3),(bx-3,by-3,bx-3,by+s),
                            (bx+bw+3,by-3,bx+bw+3-s,by-3),(bx+bw+3,by-3,bx+bw+3,by+s),
                            (bx-3,by+bh+3,bx+s,by+bh+3),(bx-3,by+bh+3,bx-3,by+bh+3-s),
                            (bx+bw+3,by+bh+3,bx+bw+3-s,by+bh+3),(bx+bw+3,by+bh+3,bx+bw+3,by+bh+3-s)]:
                    draw.line(seg, fill="#00FFFF", width=4)

        if final: return img
        sm = img.resize((640, 360), rs())
        buf = io.BytesIO(); sm.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode('utf-8')

    def update_img():
        b64 = render()
        img_preview.src = f"data:image/png;base64,{b64}"
        try: img_preview.update()
        except: pass

    def abrir_editor_texto_overlay(ii):
        ly = state["layers"][ii]
        tf_edit = ft.TextField(value=ly["text"], multiline=True, autofocus=True, width=400)
        
        def salvar_edicao(e):
            ly["text"] = tf_edit.value
            state["fc"] = {}
            rebuild()
            refresh()
            dlg_edit.open = False
            page.update()

        dlg_edit = ft.AlertDialog(
            title=ft.Text(f"Editar Texto {ii+1}"),
            content=tf_edit,
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: setattr(dlg_edit, "open", False) or page.update()),
                ft.ElevatedButton("Concluir", bgcolor=ft.Colors.GREEN_700, on_click=salvar_edicao)
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.overlay.append(dlg_edit)
        dlg_edit.open = True
        page.update()

    def rebuild():
        update_img()
        ctrls = [img_preview]
        for i, bb in enumerate(state["bboxes"]):
            x, y, w, h = bb["x"], bb["y"], bb["w"], bb["h"]
            idx = i

            def mk_move(ii):
                def start(e): state["idx"] = ii
                def upd(e):
                    try: dx, dy = e.local_delta.x, e.local_delta.y
                    except: return
                    l = state["layers"][ii]
                    l["box_x"] = max(0, l["box_x"] + dx*2)
                    l["box_y"] = max(0, l["box_y"] + dy*2)
                    update_img(); sync()
                def end(e): rebuild()
                def dbl(e): abrir_editor_texto_overlay(ii)
                return start, upd, end, dbl

            def mk_edge(ii, edge):
                def start(e): state["idx"] = ii
                def upd(e):
                    try: dx, dy = e.local_delta.x, e.local_delta.y
                    except: return
                    l = state["layers"][ii]
                    if edge == "left":
                        l["box_x"] += dx*2; l["box_w"] = max(60, l["box_w"] - dx*2)
                    elif edge == "right":
                        l["box_w"] = max(60, l["box_w"] + dx*2)
                    elif edge == "top":
                        l["box_y"] += dy*2; l["box_h"] = max(30, l["box_h"] - dy*2)
                    elif edge == "bottom":
                        l["box_h"] = max(30, l["box_h"] + dy*2)
                    update_img(); sync()
                def end(e): rebuild()
                return start, upd, end

            # Centro - mover e clipe duplo para editar
            ms, mu, me, md = mk_move(idx)
            inner_w, inner_h = max(w-2*EDGE, 10), max(h-2*EDGE, 10)
            ctrls.append(ft.Container(left=x+EDGE, top=y+EDGE, width=inner_w, height=inner_h,
                content=ft.GestureDetector(on_pan_start=ms, on_pan_update=mu, on_pan_end=me, on_double_tap=md,
                    mouse_cursor=ft.MouseCursor.MOVE,
                    content=ft.Container(width=inner_w, height=inner_h,
                        bgcolor=ft.Colors.with_opacity(0.01, "white")))))

            # Borda esquerda
            es, eu, ee = mk_edge(idx, "left")
            ctrls.append(ft.Container(left=max(x-EDGE,0), top=y, width=EDGE*2, height=h,
                content=ft.GestureDetector(on_pan_start=es, on_pan_update=eu, on_pan_end=ee,
                    mouse_cursor=ft.MouseCursor.RESIZE_LEFT_RIGHT,
                    content=ft.Container(width=EDGE*2, height=h,
                        bgcolor=ft.Colors.with_opacity(0.01, "white")))))
            # Borda direita
            es, eu, ee = mk_edge(idx, "right")
            ctrls.append(ft.Container(left=x+w-EDGE, top=y, width=EDGE*2, height=h,
                content=ft.GestureDetector(on_pan_start=es, on_pan_update=eu, on_pan_end=ee,
                    mouse_cursor=ft.MouseCursor.RESIZE_LEFT_RIGHT,
                    content=ft.Container(width=EDGE*2, height=h,
                        bgcolor=ft.Colors.with_opacity(0.01, "white")))))
            # Borda superior
            es, eu, ee = mk_edge(idx, "top")
            ctrls.append(ft.Container(left=x, top=max(y-EDGE,0), width=w, height=EDGE*2,
                content=ft.GestureDetector(on_pan_start=es, on_pan_update=eu, on_pan_end=ee,
                    mouse_cursor=ft.MouseCursor.RESIZE_UP_DOWN,
                    content=ft.Container(width=w, height=EDGE*2,
                        bgcolor=ft.Colors.with_opacity(0.01, "white")))))
            # Borda inferior
            es, eu, ee = mk_edge(idx, "bottom")
            ctrls.append(ft.Container(left=x, top=y+h-EDGE, width=w, height=EDGE*2,
                content=ft.GestureDetector(on_pan_start=es, on_pan_update=eu, on_pan_end=ee,
                    mouse_cursor=ft.MouseCursor.RESIZE_UP_DOWN,
                    content=ft.Container(width=w, height=EDGE*2,
                        bgcolor=ft.Colors.with_opacity(0.01, "white")))))

        preview_stack.controls = ctrls
        try: preview_stack.update()
        except: pass

    def sync():
        l = state["layers"][state["idx"]]
        sl_font.value = l["font_size"]; sl_x.value = l["box_x"]; sl_y.value = l["box_y"]
        for c in [sl_font, sl_x, sl_y]:
            try:
                if c.page: c.update()
            except: pass

    def atualizar(e=None):
        if not state["layers"]: return
        ly = state["layers"][state["idx"]]
        if e and hasattr(e.control, "label"):
            lb = e.control.label
            if lb == "Título": ly["text"] = e.control.value
            elif lb == "Tamanho": ly["font_size"] = max(8, int(e.control.value or 8))
            elif lb == "Borda": ly["stroke_width"] = int(e.control.value or 0)
            elif lb == "Esp. Letras": ly["letter_spacing"] = float(e.control.value or 0)
            elif lb == "Esp. Palavras": ly["word_spacing"] = float(e.control.value or 0)
            elif lb == "Pos X": ly["box_x"] = float(e.control.value or 0)
            elif lb == "Pos Y": ly["box_y"] = float(e.control.value or 0)
            elif lb == "Cor Fonte": ly["font_color"] = e.control.value
            elif lb == "Cor Fundo": state["bg_color"] = e.control.value
            elif lb == "Fonte": ly["font_family"] = e.control.value
            elif lb == "Negrito": ly["bold"] = e.control.value
            elif lb == "Alinhamento": ly["alignment"] = e.control.value
        state["fc"] = {}; rebuild(); refresh()

    def adicionar(e):
        state["layers"].append({"text":"Novo Texto","font_size":40,"font_color":"#000000",
            "box_x":200,"box_y":350,"box_w":880,"box_h":200,
            "letter_spacing":0,"word_spacing":0,"stroke_width":0,"bold":False,
            "font_family":"Arial","alignment":"Centralizado"})
        state["idx"] = len(state["layers"])-1; rebuild(); refresh()

    def remover(e):
        if len(state["layers"]) > 1:
            state["layers"].pop(state["idx"]); state["idx"] = max(0, state["idx"]-1)
            rebuild(); refresh()

    def mudar_camada(e):
        state["idx"] = int(e.control.value.replace("Texto ",""))-1; rebuild(); refresh()

    def refresh():
        l = state["layers"][state["idx"]]
        tf_titulo.value = l["text"]; sl_font.value = l["font_size"]; sl_stroke.value = l["stroke_width"]
        sl_letter.value = l["letter_spacing"]; sl_word.value = l["word_spacing"]
        sl_x.value = l["box_x"]; sl_y.value = l["box_y"]; tf_color.value = l["font_color"]
        dd_font.value = l["font_family"]; sw_bold.value = l["bold"]; dd_align.value = l["alignment"]
        dd_layers.options = [ft.dropdown.Option(f"Texto {j+1}") for j in range(len(state["layers"]))]
        dd_layers.value = f"Texto {state['idx']+1}"
        for c in [tf_titulo, sl_font, sl_stroke, sl_letter, sl_word, sl_x, sl_y, tf_color, dd_font, sw_bold, dd_align, dd_layers]:
            try:
                if c.page: c.update()
            except: pass

    def abrir_bg(e):
        r = tk.Tk(); r.withdraw(); r.attributes("-topmost", True)
        p = filedialog.askopenfilename(filetypes=[("Imagens","*.png;*.jpg;*.jpeg")]); r.destroy()
        if p:
            try: state["img_bg"] = Image.open(p); rebuild()
            except: pass

    def remover_bg(e): state["img_bg"] = None; rebuild()

    def abrir_cor(e):
        is_f = "Fonte" in e.control.tooltip
        ctrl = tf_color if is_f else tf_bgcolor
        r = tk.Tk(); r.withdraw(); r.attributes("-topmost", True)
        c = colorchooser.askcolor(initialcolor=ctrl.value)[1]; r.destroy()
        if c:
            ctrl.value = c.upper()
            if is_f: state["layers"][state["idx"]]["font_color"] = c.upper()
            else: state["bg_color"] = c.upper()
            rebuild()
            try: ctrl.update()
            except: pass

    def salvar(e):
        r = tk.Tk(); r.withdraw(); r.attributes("-topmost", True)
        p = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG","*.png")], initialfile="capa.png"); r.destroy()
        if p:
            try:
                render(True).save(p)
                dlg.open = False
                page.update()
                
                # Mostrar diálogo de sucesso com opção de abrir pasta
                def abrir_pasta(e):
                    pasta = os.path.dirname(p)
                    if os.name == 'nt': os.startfile(pasta)
                    success_dlg.open = False
                    page.update()

                success_dlg = ft.AlertDialog(
                    title=ft.Text("Sucesso!"),
                    content=ft.Text("Capa salva com sucesso!\nDeseja abrir a pasta onde o arquivo foi salvo?"),
                    actions=[
                        ft.TextButton("Não", on_click=lambda _: [setattr(success_dlg, "open", False), page.update()]),
                        ft.ElevatedButton("Abrir Pasta", icon=ft.Icons.FOLDER_OPEN, bgcolor=ft.Colors.GREEN_700, on_click=abrir_pasta)
                    ],
                    actions_alignment=ft.MainAxisAlignment.END
                )
                page.overlay.append(success_dlg)
                success_dlg.open = True
                page.update()
            except: pass

    # --- UI ---
    dd_layers = ft.Dropdown(label="Selecionar Camada", value="Texto 1", options=[ft.dropdown.Option("Texto 1")], on_select=mudar_camada, width=200, dense=True)
    tf_titulo = ft.TextField(label="Título", value=state["layers"][0]["text"], multiline=True, on_change=atualizar, height=70)
    sl_font   = ft.Slider(min=8, max=300, value=60, label="Tamanho", on_change=atualizar)
    sl_stroke = ft.Slider(min=0, max=20, value=0, label="Borda", on_change=atualizar)
    sl_letter = ft.Slider(min=-10, max=50, value=0, label="Esp. Letras", on_change=atualizar)
    sl_word   = ft.Slider(min=-10, max=100, value=0, label="Esp. Palavras", on_change=atualizar)
    sl_x      = ft.Slider(min=0, max=1280, value=100, label="Pos X", on_change=atualizar)
    sl_y      = ft.Slider(min=0, max=720, value=180, label="Pos Y", on_change=atualizar)
    tf_color  = ft.TextField(label="Cor Fonte", value="#000000", width=120, on_change=atualizar)
    tf_bgcolor = ft.TextField(label="Cor Fundo", value="#FFFFFF", width=120, on_change=atualizar)
    dd_font   = ft.Dropdown(label="Fonte", options=[ft.dropdown.Option(f) for f in ["Arial","Impact","Verdana","Georgia"]], value="Arial", width=145, on_select=atualizar)
    sw_bold   = ft.Switch(label="Negrito", value=True, on_change=atualizar)
    dd_align  = ft.Dropdown(label="Alinhamento", options=[ft.dropdown.Option(o) for o in ["Esquerda","Centralizado","Direita"]], value="Centralizado", width=150, on_select=atualizar)

    img_preview = ft.Image(src="", width=640, height=360, fit="contain")
    preview_stack = ft.Stack([img_preview], width=640, height=360)
    rebuild()

    content = ft.Column([
        ft.Row([dd_layers, ft.IconButton(ft.Icons.ADD, on_click=adicionar, tooltip="Novo Texto"),
                ft.IconButton(ft.Icons.DELETE, on_click=remover, tooltip="Remover", icon_color="red")], spacing=5),
        tf_titulo,
        ft.Row([dd_font, sw_bold, dd_align], spacing=8, wrap=True),
        ft.Row([ft.Column([ft.Text("Pos X", size=9), sl_x], expand=1),
                ft.Column([ft.Text("Pos Y", size=9), sl_y], expand=1)], spacing=10),
        ft.Row([ft.Column([ft.Text("Tamanho", size=9), sl_font], expand=1),
                ft.Column([ft.Text("Borda", size=9), sl_stroke], expand=1)], spacing=10),
        ft.Row([ft.Column([ft.Text("Letras", size=9), sl_letter], expand=1),
                ft.Column([ft.Text("Palavras", size=9), sl_word], expand=1)], spacing=10),
        ft.Row([tf_bgcolor, ft.IconButton(ft.Icons.PALETTE, on_click=abrir_cor, tooltip="Cor Fundo"),
                ft.IconButton(ft.Icons.IMAGE, on_click=abrir_bg, tooltip="Trocar Imagem"),
                ft.IconButton(ft.Icons.HIDE_IMAGE, on_click=remover_bg, tooltip="Remover Imagem", icon_color="red"),
                ft.Container(width=10), tf_color,
                ft.IconButton(ft.Icons.PALETTE, on_click=abrir_cor, tooltip="Cor Fonte")], alignment="center"),
        ft.Container(content=preview_stack, bgcolor="black", border_radius=10, padding=2, alignment=ft.Alignment(0,0))
    ], tight=True, spacing=8, width=660, scroll=ft.ScrollMode.ADAPTIVE)

    dlg = ft.AlertDialog(title=ft.Text("Gerador de Capas Pro"), content=content,
        actions=[ft.ElevatedButton("Cancelar", on_click=lambda _: fd(dlg), bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE),
                 ft.ElevatedButton("Salvar PNG", icon=ft.Icons.SAVE, on_click=salvar, bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE)],
        shape=ft.RoundedRectangleBorder(radius=15))
    def fd(d): d.open = False; page.update()
    page.overlay.append(dlg); dlg.open = True; page.update()
