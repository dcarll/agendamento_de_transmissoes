import flet as ft
from controllers.transmissao_controller import TransmissaoController
from datetime import datetime, timedelta
from utils.helpers import normalize_date, format_date_br, formatar_data_completa_semana, parse_date, formatar_data_semana, get_status_info, get_status_options
from utils.dialog_helper import mostrar_detalhes_transmissao, abrir_menu_contexto
import asyncio
import os
import tkinter as tk
from tkinter import filedialog

try:
    from docx import Document; from docx.shared import Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from openpyxl import Workbook; from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
except ImportError: pass

class CalendarioView(ft.Column):
    def __init__(self, controller: TransmissaoController, on_edit):
        super().__init__(expand=True, spacing=25, scroll=ft.ScrollMode.ADAPTIVE)
        self.controller = controller
        self.on_edit = on_edit
        self.pagina_atual = 0
        self.itens_por_página = 20
        self.view_mode = "list"
        
        self.txt_busca = ft.TextField(hint_text="Pesquisar...", prefix_icon=ft.Icons.SEARCH, on_change=lambda _: self.reset_and_update(), width=220, height=45, text_size=13, content_padding=ft.padding.only(left=10, right=10), border_radius=10, bgcolor=ft.Colors.WHITE10)
        self.dd_periodo = ft.Dropdown(label="Período", options=[ft.dropdown.Option(o) for o in ["Todos", "A partir de hoje", "Dia", "Semana", "Mês", "Semestre", "Ano"]], value="A partir de hoje", on_select=lambda _: self.reset_and_update(), width=180) # Aumentado de 140 para 180
        self.dd_status = ft.Dropdown(label="Filtrar por Status", options=[ft.dropdown.Option("Todos")] + [ft.dropdown.Option(o) for o in get_status_options()], value="Todos", on_select=lambda _: self.reset_and_update(), width=170)
        self.dd_tipo = ft.Dropdown(label="Tipo", options=[ft.dropdown.Option("Todos"), ft.dropdown.Option("YouTube"), ft.dropdown.Option("StreamYard"), ft.dropdown.Option("Zoom"), ft.dropdown.Option("OBS")], value="Todos", on_select=lambda _: self.reset_and_update(), width=120)
        self.dd_modalidade = ft.Dropdown(label="Modalidade", options=[ft.dropdown.Option("Todos"), ft.dropdown.Option("Online"), ft.dropdown.Option("Presencial"), ft.dropdown.Option("Híbrido")], value="Todos", on_select=lambda _: self.reset_and_update(), width=140)
        self.dd_ordem = ft.Dropdown(label="Ordenar por", options=[ft.dropdown.Option("Data do Evento"), ft.dropdown.Option("Nome do Evento")], value="Data do Evento", on_select=lambda _: self.reset_and_update(), width=200)
        
        self.btn_view_mode = ft.IconButton(ft.Icons.GRID_VIEW if self.view_mode == "list" else ft.Icons.LIST, on_click=self.toggle_view_mode, tooltip="Alternar Visualização")
        self.txt_count = ft.Text("0 eventos encontrados", color=ft.Colors.WHITE70, size=12)
        self.grid_container = ft.Column(expand=True)
        
        self.btn_exportar_excel = ft.ElevatedButton("Excel", icon=ft.Icons.FILE_DOWNLOAD, on_click=self.exportar_excel, style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.GREEN_700), height=40)
        self.btn_exportar_links = ft.ElevatedButton("Links", icon=ft.Icons.LINK, on_click=self.exportar_links, style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.BLUE_700), height=40)

        self.controls = [
            ft.Row([
                ft.Column([ft.Text("Calendário de Transmissões", size=28, weight=ft.FontWeight.BOLD), self.txt_count], spacing=2),
                ft.Row([self.txt_busca, self.dd_periodo, self.dd_status, self.dd_tipo, self.dd_modalidade, self.dd_ordem, self.btn_view_mode], spacing=10)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True),
            ft.Row([ft.Container(expand=True), self.btn_exportar_excel, self.btn_exportar_links], spacing=10),
            ft.Divider(height=10, color=ft.Colors.WHITE10),
            self.grid_container
        ]
        self.init_ui()

    def toggle_view_mode(self, e):
        self.view_mode = "grid" if self.view_mode == "list" else "list"
        self.btn_view_mode.icon = ft.Icons.GRID_VIEW if self.view_mode == "list" else ft.Icons.LIST
        self.init_ui()

    def get_lista_filtrada(self):
        hoje_str = datetime.now().strftime("%Y-%m-%d"); termo = self.txt_busca.value.lower() if self.txt_busca.value else ""
        lista = []
        for t in self.controller.transmissoes:
            if termo and termo not in t.evento.lower() and termo not in t.responsavel.lower(): continue
            if self.dd_status.value != "Todos" and t.status != self.dd_status.value: continue
            if self.dd_tipo.value != "Todos" and t.tipo_transmissao != self.dd_tipo.value: continue
            if self.dd_modalidade.value != "Todos" and t.modalidade != self.dd_modalidade.value: continue
            dt_norm = normalize_date(t.data)
            if self.dd_periodo.value == "A partir de hoje" and dt_norm < hoje_str: continue
            lista.append(t)
        if self.dd_ordem.value == "Data do Evento": lista.sort(key=lambda x: (normalize_date(x.data), x.horario_inicio))
        else: lista.sort(key=lambda x: x.evento.lower())
        return lista

    def init_ui(self):
        lista = self.get_lista_filtrada(); tp = (len(lista) + self.itens_por_página - 1) // self.itens_por_página
        inicio = self.pagina_atual * self.itens_por_página; itens = lista[inicio:inicio+self.itens_por_página]
        self.txt_count.value = f"{len(lista)} eventos encontrados"; self.popular_grid(itens, tp)

    def popular_grid(self, itens, tp):
        if self.view_mode == "list":
            container_itens = ft.Column(spacing=10, expand=True)
            for t in itens: container_itens.controls.append(self.create_event_row(t))
        else:
            container_itens = ft.ResponsiveRow(spacing=20, run_spacing=20)
            for t in itens: container_itens.controls.append(self.create_event_card(t))
        pag = ft.Row([ft.IconButton(ft.Icons.ARROW_BACK_IOS_NEW, on_click=lambda _: self.mudar_pagina(-1), disabled=self.pagina_atual == 0), ft.Text(f"Página {self.pagina_atual + 1} de {max(1, tp)}", weight=ft.FontWeight.BOLD), ft.IconButton(ft.Icons.ARROW_FORWARD_IOS, on_click=lambda _: self.mudar_pagina(1), disabled=self.pagina_atual >= tp - 1)], alignment=ft.MainAxisAlignment.CENTER)
        self.grid_container.controls = [container_itens, ft.Container(height=20), pag]
        try: self.update()
        except: pass

    def create_event_row(self, t):
        s_info = get_status_info(t.status)
        return ft.GestureDetector(
            content=ft.Container(content=ft.Row([ft.Container(content=ft.Text(formatar_data_semana(t.data), weight=ft.FontWeight.BOLD, size=14, color=ft.Colors.BLACK), bgcolor=s_info["color"], padding=10, border_radius=10, width=120, alignment=ft.Alignment(0, 0)), ft.Text(f"{t.horario_inicio} às {t.horario_fim}", weight=ft.FontWeight.BOLD, size=14, width=135, no_wrap=True), ft.Container(content=ft.Text(t.evento, size=16, weight=ft.FontWeight.BOLD), width=400), ft.Column([ft.Text(t.responsavel, size=13, weight=ft.FontWeight.W_500), ft.Text(t.local, size=11, color=ft.Colors.WHITE38)], expand=True, spacing=2), ft.Container(content=ft.Row([ft.Container(bgcolor=s_info["color"], width=10, height=10, border_radius=5), ft.Text(s_info["label"], size=13, color=s_info["color"], weight=ft.FontWeight.BOLD)], spacing=8), width=150), ft.Row([ft.IconButton(ft.Icons.INFO_OUTLINE, icon_size=18, icon_color=ft.Colors.CYAN_200, on_click=lambda _: mostrar_detalhes_transmissao(self.page, t, self.controller, self.atualizar)), ft.IconButton(ft.Icons.EDIT_NOTE, icon_size=18, icon_color=ft.Colors.BLUE_200, on_click=lambda _: self.on_edit(t)), ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_size=18, icon_color=ft.Colors.RED_300, on_click=lambda _: self.confirmar_exclusao(t))], spacing=0)], spacing=20), padding=15, border_radius=12, border=ft.border.all(1, ft.Colors.WHITE10), bgcolor=ft.Colors.WHITE10),
            on_tap=lambda _: mostrar_detalhes_transmissao(self.page, t, self.controller, self.atualizar),
            on_secondary_tap=lambda e: abrir_menu_contexto(self.page, t, self.controller, self.on_edit, self.confirmar_exclusao, self.atualizar),
        )

    def create_event_card(self, t):
        s_info = get_status_info(t.status)
        return ft.Container(col={"sm": 12, "md": 6, "xl": 4}, content=ft.GestureDetector(content=ft.Container(content=ft.Column([ft.Row([ft.Container(content=ft.Text(format_date_br(t.data), size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK), bgcolor=s_info["color"], padding=ft.padding.symmetric(horizontal=10, vertical=5), border_radius=5), ft.Container(expand=True), ft.Text(t.horario_inicio, size=12, weight=ft.FontWeight.BOLD)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), ft.Text(t.evento, size=18, weight=ft.FontWeight.BOLD, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS, height=50), ft.Row([ft.Icon(ft.Icons.PERSON, size=16, color=ft.Colors.WHITE38), ft.Text(t.responsavel, size=13, color=ft.Colors.WHITE70, expand=True)], spacing=10), ft.Row([ft.Icon(ft.Icons.LOCATION_ON, size=16, color=ft.Colors.WHITE38), ft.Text(t.local, size=13, color=ft.Colors.WHITE70, expand=True)], spacing=10), ft.Divider(height=10, color=ft.Colors.WHITE10), ft.Row([ft.Container(content=ft.Row([ft.Container(bgcolor=s_info["color"], width=8, height=8, border_radius=4), ft.Text(s_info["label"], size=11, color=s_info["color"], weight=ft.FontWeight.BOLD)], spacing=5), expand=True), ft.IconButton(ft.Icons.INFO_OUTLINE, icon_size=18, icon_color=ft.Colors.CYAN_200, on_click=lambda _: mostrar_detalhes_transmissao(self.page, t, self.controller, self.atualizar)), ft.IconButton(ft.Icons.EDIT_NOTE, icon_size=18, icon_color=ft.Colors.BLUE_200, on_click=lambda _: self.on_edit(t))], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)], spacing=12), padding=20, border_radius=15, bgcolor=ft.Colors.WHITE10, border=ft.border.all(1, ft.Colors.with_opacity(0.1, ft.Colors.WHITE))), on_tap=lambda _: mostrar_detalhes_transmissao(self.page, t, self.controller, self.atualizar), on_secondary_tap=lambda e: abrir_menu_contexto(self.page, t, self.controller, self.on_edit, self.confirmar_exclusao, self.atualizar)))

    def abrir_pasta(self, caminho):
        try:
            pasta = os.path.dirname(caminho)
            if os.name == 'nt': os.startfile(pasta)
            else: import subprocess; subprocess.run(['open' if os.uname().sysname == 'Darwin' else 'xdg-open', pasta])
        except: pass

    def exportar_excel(self, e):
        r = tk.Tk(); r.withdraw(); r.attributes("-topmost", True); r.focus_force(); path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")], initialfile="calendario.xlsx"); r.destroy()
        if not path: return
        lista = self.get_lista_filtrada()
        async def _ex():
            try:
                def _build():
                    wb = Workbook(); ws = wb.active; ws.title = "Calendário"
                    
                    # Cabeçalhos
                    headers = ["Data", "Início", "Fim", "Evento", "Responsável", "Local", "Tipo", "Modalidade", "Status", "Público", "Duração", "Operador", "Links", "Observações"]
                    
                    # Estilo para o cabeçalho
                    header_font = Font(bold=True, color="FFFFFF")
                    header_fill = PatternFill(start_color="333333", end_color="333333", fill_type="solid")
                    
                    for col_idx, header in enumerate(headers, 1):
                        cell = ws.cell(row=1, column=col_idx, value=header)
                        cell.font = header_font
                        cell.fill = header_fill
                        cell.alignment = Alignment(horizontal="center", vertical="center")

                    # Mapeamento de cores Flet para Hex (OpenPyXL)
                    # Usamos tons um pouco mais pastéis para o Excel
                    status_colors_hex = {
                        ft.Colors.RED_400: "FFCDD2",
                        ft.Colors.AMBER_400: "FFF9C4",
                        ft.Colors.TEAL_400: "B2DFDB",
                        ft.Colors.GREEN_400: "C8E6C9",
                        ft.Colors.PURPLE_400: "E1BEE7",
                        ft.Colors.BROWN: "D7CCC8",
                    }

                    for r_idx, t in enumerate(lista, 2):
                        # Agregando links
                        links = []
                        if t.link_youtube: links.append(f"YouTube: {t.link_youtube}")
                        if t.link_stream: links.append(f"StreamYard: {t.link_stream}")
                        if hasattr(t, 'links_adicionais') and t.links_adicionais:
                            for l in t.links_adicionais: links.append(f"{l.get('label', 'Link')}: {l.get('url', '')}")
                        
                        data_row = [
                            format_date_br(t.data),
                            t.horario_inicio,
                            t.horario_fim,
                            t.evento,
                            t.responsavel,
                            t.local,
                            t.tipo_transmissao,
                            t.modalidade,
                            get_status_info(t.status)["label"],
                            t.publico,
                            t.tempo_total,
                            t.operador,
                            "\n".join(links),
                            t.observacoes
                        ]
                        
                        for c_idx, value in enumerate(data_row, 1):
                            cell = ws.cell(row=r_idx, column=c_idx, value=value)
                            
                            # Formatação da coluna de Status (Índice 9)
                            if c_idx == 9:
                                s_info = get_status_info(t.status)
                                hex_color = status_colors_hex.get(s_info["color"], "FFFFFF")
                                cell.fill = PatternFill(start_color=hex_color, end_color=hex_color, fill_type="solid")
                                cell.alignment = Alignment(horizontal="center", vertical="center")
                                cell.font = Font(bold=True)
                            else:
                                cell.alignment = Alignment(vertical="center", wrap_text=(c_idx in [4, 13, 14]))

                    # Ajuste automático de largura
                    for col in ws.columns:
                        max_length = 0; column = col[0].column_letter
                        for cell in col:
                            try:
                                if cell.value:
                                    # Para células com quebra de linha, pegamos a maior linha
                                    lines = str(cell.value).split('\n')
                                    length = max(len(line) for line in lines)
                                    if length > max_length: max_length = length
                            except: pass
                        ws.column_dimensions[column].width = min(max_length + 3, 60)

                    wb.save(path)
                await asyncio.to_thread(_build)
                self.show_popup("Excel salvo com sucesso!", path)
            except Exception as ex: print(f"Erro ao exportar Excel: {ex}")
        self.page.run_task(_ex)

    def exportar_links(self, e):
        r = tk.Tk(); r.withdraw(); r.attributes("-topmost", True); r.focus_force(); path = filedialog.asksaveasfilename(defaultextension=".docx", filetypes=[("Word", "*.docx")], initialfile="links.docx"); r.destroy()
        if not path: return
        self.btn_exportar_links.disabled = True; self.btn_exportar_links.text = "Gerando..."; self.update()
        lista = self.get_lista_filtrada()
        async def _ex():
            try:
                def _process():
                    doc = Document(); title = doc.add_heading('Links das transmissões', 0); title.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    for t in lista:
                        p_evento = doc.add_paragraph(); run_evento = p_evento.add_run(t.evento); run_evento.bold = True; run_evento.font.size = Pt(14)
                        p_data = doc.add_paragraph(); p_data.add_run(f"{format_date_br(t.data)} - {t.horario_inicio} às {t.horario_fim}")
                        if t.link_youtube: doc.add_paragraph(f"YouTube: {t.link_youtube}")
                        if t.link_stream: doc.add_paragraph(f"StreamYard: {t.link_stream}")
                        if hasattr(t, 'links_adicionais') and t.links_adicionais:
                            for link_obj in t.links_adicionais:
                                label = link_obj.get("label", "Link"); url = link_obj.get("url", ""); 
                                if url: doc.add_paragraph(f"{label}: {url}")
                        doc.add_paragraph("-" * 15)
                    doc.save(path)
                await asyncio.to_thread(_process)
                self.show_popup("Relatório de Links salvo!", path)
            except Exception as ex: print(f"Erro docx: {ex}")
            finally: self.btn_exportar_links.disabled = False; self.btn_exportar_links.text = "Links"; self.page.update()
        self.page.run_task(_ex)

    def show_popup(self, text, path):
        def on_open_click(e):
            self.abrir_pasta(path)
            dlg.open = False
            self.page.update()
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Sucesso!"),
            content=ft.Text(f"{text}\nDeseja abrir a pasta onde o arquivo foi salvo?"),
            actions=[
                ft.TextButton("Não", on_click=lambda _: self.fechar_dlg(dlg)),
                ft.ElevatedButton("Abrir Pasta", icon=ft.Icons.FOLDER_OPEN, bgcolor=ft.Colors.GREEN_700, on_click=on_open_click)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    def confirmar_exclusao(self, t):
        dlg = ft.AlertDialog(title=ft.Text("Confirmar Exclusão"), content=ft.Text(f"Deseja excluir '{t.evento}'?"), actions=[ft.TextButton("Cancelar", on_click=lambda _: self.fechar_dlg(dlg)), ft.ElevatedButton("Excluir", bgcolor=ft.Colors.RED_700, on_click=lambda _: self.deletar_e_fechar(t, dlg))])
        self.page.overlay.append(dlg); dlg.open = True; self.page.update()
    def fechar_dlg(self, dlg): dlg.open = False; self.page.update()
    def deletar_e_fechar(self, t, dlg): self.controller.deletar(t.id); dlg.open = False; self.reset_and_update()
    def reset_and_update(self): self.pagina_atual = 0; self.init_ui()
    def atualizar(self): self.init_ui()
    def mudar_pagina(self, delta): self.pagina_atual += delta; self.init_ui()
