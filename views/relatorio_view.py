import flet as ft
from datetime import datetime
from utils.helpers import parse_date, converter_tempo_para_segundos, formatar_segundos_para_tempo
import asyncio
import os
import tkinter as tk
from tkinter import filedialog

# Imports pesados no topo
try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill
except ImportError:
    pass

class RelatorioView(ft.Column):
    def __init__(self, controller, on_back=None):
        super().__init__(expand=True, spacing=20, scroll=ft.ScrollMode.AUTO)
        self.controller = controller
        self.on_back = on_back
        self.filtro_periodo = "Semestral"
        self.filtro_ano = None
        self.filtro_tipo = "Todos"
        
        self.tabela = ft.DataTable(
            columns=[], rows=[], border=ft.border.all(1, ft.Colors.WHITE10), border_radius=10,
            heading_row_color=ft.Colors.with_opacity(0.15, ft.Colors.BLUE_400), heading_row_height=50,
            data_row_min_height=45, data_row_max_height=55, column_spacing=30, horizontal_margin=15,
        )
        self.init_ui()

    def init_ui(self):
        self.dd_periodo = ft.Dropdown(label="Agrupamento", options=[ft.dropdown.Option("Semestral"), ft.dropdown.Option("Anual"), ft.dropdown.Option("Mensal")], value=self.filtro_periodo, on_select=self.on_filtro_change, border=ft.InputBorder.NONE, width=180)
        anos = self.get_anos_disponiveis()
        self.dd_ano = ft.Dropdown(label="Ano", options=[ft.dropdown.Option("Todos")] + [ft.dropdown.Option(str(a)) for a in anos], value="Todos", on_select=self.on_filtro_change, border=ft.InputBorder.NONE, width=140)
        tipos = self.get_tipos_disponiveis()
        self.dd_tipo = ft.Dropdown(label="Tipo de Transmissão", options=[ft.dropdown.Option("Todos")] + [ft.dropdown.Option(t) for t in tipos], value="Todos", on_select=self.on_filtro_change, border=ft.InputBorder.NONE, width=200)
        self.total_row = ft.Container(content=ft.Row([], spacing=30), bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.GREEN_400), border_radius=10, padding=15)
        
        self.btn_exportar = ft.ElevatedButton("Exportar Excel", icon=ft.Icons.FILE_DOWNLOAD, style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE), on_click=self.exportar_excel, height=45)

        self.controls = [
            ft.Row([ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: self.on_back() if self.on_back else None), ft.Text("📊 Relatórios", size=30, weight=ft.FontWeight.BOLD)], alignment=ft.MainAxisAlignment.START, spacing=10),
            ft.Divider(height=10, color=ft.Colors.WHITE10),
            ft.Container(content=ft.Row([self.wrap_filter(self.dd_periodo), self.wrap_filter(self.dd_ano), self.wrap_filter(self.dd_tipo), ft.Container(expand=True), self.btn_exportar], spacing=15, alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER), padding=ft.padding.symmetric(vertical=5)),
            ft.Container(content=self.tabela, border_radius=15, bgcolor=ft.Colors.with_opacity(0.03, ft.Colors.WHITE), padding=10),
            self.total_row,
        ]
        self.popular_tabela()

    def wrap_filter(self, control):
        return ft.Container(content=control, border_radius=12, border=ft.border.all(1, ft.Colors.with_opacity(0.2, ft.Colors.WHITE)), padding=ft.padding.only(left=10, right=10))

    def get_anos_disponiveis(self):
        anos = set(); [anos.add(parse_date(t.data).year) for t in self.controller.transmissoes if parse_date(t.data)]
        return sorted(anos)

    def get_tipos_disponiveis(self):
        tipos = set(); [tipos.add(t.tipo_transmissao) for t in self.controller.transmissoes if t.tipo_transmissao]
        return sorted(tipos)

    def on_filtro_change(self, e):
        self.filtro_periodo = self.dd_periodo.value; self.filtro_ano = None if self.dd_ano.value == "Todos" else int(self.dd_ano.value); self.filtro_tipo = self.dd_tipo.value; self.popular_tabela(); self.update()

    def get_transmissoes_filtradas(self):
        filtradas = []
        for t in self.controller.transmissoes:
            dt = parse_date(t.data)
            if not dt or (self.filtro_ano and dt.year != self.filtro_ano) or (self.filtro_tipo != "Todos" and t.tipo_transmissao != self.filtro_tipo): continue
            filtradas.append(t)
        return filtradas

    def agrupar_dados(self):
        transmissoes = self.get_transmissoes_filtradas(); grupos = {}
        for t in transmissoes:
            dt = parse_date(t.data)
            if not dt: continue
            if self.filtro_periodo == "Semestral": key = f"{'1º' if dt.month <= 6 else '2º'}/{dt.year}"; sk = (dt.year, 0 if dt.month <= 6 else 1)
            elif self.filtro_periodo == "Anual": key = str(dt.year); sk = (dt.year, 0)
            else: meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]; key = f"{meses[dt.month - 1]}/{dt.year}"; sk = (dt.year, dt.month)
            if key not in grupos: grupos[key] = {"sort_key": sk, "transmissoes": 0, "publico": 0, "segundos": 0, "tipos": {}}
            grupos[key]["transmissoes"] += 1; grupos[key]["publico"] += t.publico; grupos[key]["segundos"] += converter_tempo_para_segundos(t.tempo_total)
            tipo = t.tipo_transmissao or "Outro"; grupos[key]["tipos"][tipo] = grupos[key]["tipos"].get(tipo, 0) + 1
        return sorted(grupos.items(), key=lambda x: x[1]["sort_key"])

    def popular_tabela(self):
        dados = self.agrupar_dados(); self.tabela.columns = [ft.DataColumn(ft.Text("Período")), ft.DataColumn(ft.Text("Público"), numeric=True), ft.DataColumn(ft.Text("Transmissões"), numeric=True), ft.DataColumn(ft.Text("Tipos")), ft.DataColumn(ft.Text("Horas"))]
        self.tabela.rows = []; tp, tt, ts, tts = 0, 0, 0, {}
        for periodo, info in dados:
            tp += info["publico"]; tt += info["transmissoes"]; ts += info["segundos"]
            for t, c in info["tipos"].items(): tts[t] = tts.get(t, 0) + c
            tipos_str = ", ".join([f"{t}: {c}" for t, c in sorted(info["tipos"].items())])
            self.tabela.rows.append(ft.DataRow(cells=[ft.DataCell(ft.Text(periodo)), ft.DataCell(ft.Text(str(info["publico"]))), ft.DataCell(ft.Text(str(info["transmissoes"]))), ft.DataCell(ft.Text(tipos_str, size=12)), ft.DataCell(ft.Text(formatar_segundos_para_tempo(info["segundos"])))]))
        total_tipos_str = ", ".join([f"{t}: {c}" for t, c in sorted(tts.items())])
        self.total_row.content = ft.Row([ft.Container(content=ft.Row([ft.Icon(ft.Icons.SUMMARIZE, color=ft.Colors.GREEN_400), ft.Text("TOTAL")]), width=130), ft.Container(content=ft.Column([ft.Text("Público"), ft.Text(f"{tp:,}".replace(",", "."), size=18)]), width=120), ft.Container(content=ft.Column([ft.Text("Transmissões"), ft.Text(str(tt), size=18)]), width=120), ft.Container(content=ft.Column([ft.Text("Tipos"), ft.Text(total_tipos_str, size=12)]), expand=True), ft.Container(content=ft.Column([ft.Text("Horas Totais"), ft.Text(formatar_segundos_para_tempo(ts), size=18, color=ft.Colors.CYAN_400)]), width=130)], spacing=30)

    def abrir_pasta(self, caminho):
        try:
            pasta = os.path.dirname(caminho)
            if os.name == 'nt': os.startfile(pasta)
            else: import subprocess; subprocess.run(['open' if os.uname().sysname == 'Darwin' else 'xdg-open', pasta])
        except: pass

    def exportar_excel(self, e):
        def _get_path():
            root = tk.Tk(); root.withdraw(); root.attributes("-topmost", True); root.focus_force()
            path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")], initialfile="relatorio.xlsx")
            root.destroy(); return path
        caminho = _get_path()
        if not caminho: return
        
        self.btn_exportar.disabled = True; self.btn_exportar.text = "Exportando..."; self.update()
        
        async def _exec():
            try:
                def _build():
                    wb = Workbook(); ws = wb.active; ws.title = "Relatório"
                    headers = ["Período", "Público", "Transmissões", "Tipos", "Horas"]
                    for col, h in enumerate(headers, 1):
                        cell = ws.cell(1, col, h); cell.font = Font(bold=True, color="FFFFFF"); cell.fill = PatternFill("solid", start_color="1F4E79")
                    dados = self.agrupar_dados()
                    for row, (periodo, info) in enumerate(dados, 2):
                        ws.cell(row, 1, periodo); ws.cell(row, 2, info["publico"]); ws.cell(row, 3, info["transmissoes"])
                        ws.cell(row, 4, ", ".join([f"{t}: {c}" for t, c in info["tipos"].items()])); ws.cell(row, 5, formatar_segundos_para_tempo(info["segundos"]))
                    wb.save(caminho)
                
                await asyncio.to_thread(_build)
                self.show_popup("Relatório exportado!", caminho)
            except Exception as ex:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Erro: {ex}"), bgcolor=ft.Colors.RED_700); self.page.snack_bar.open = True
            finally:
                self.btn_exportar.disabled = False; self.btn_exportar.text = "Exportar Excel"; self.page.update()
        self.page.run_task(_exec)

    def show_popup(self, text, path):
        def on_open_click(e):
            self.abrir_pasta(path); dlg.open = False; self.page.update()
        dlg = ft.AlertDialog(
            title=ft.Text("Arquivo Salvo"),
            content=ft.Text(f"{text}\nDeseja abrir a pasta agora?"),
            actions=[
                ft.TextButton("Não", on_click=lambda _: self.fechar_dlg(dlg)),
                ft.ElevatedButton("Abrir Pasta", icon=ft.Icons.FOLDER_OPEN, bgcolor=ft.Colors.GREEN_700, on_click=on_open_click)
            ]
        )
        self.page.overlay.append(dlg); dlg.open = True; self.page.update()

    def fechar_dlg(self, dlg): dlg.open = False; self.page.update()
