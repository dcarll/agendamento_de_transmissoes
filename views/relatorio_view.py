import flet as ft
from datetime import datetime
from utils.helpers import parse_date, converter_tempo_para_segundos, formatar_segundos_para_tempo


class RelatorioView(ft.Column):
    def __init__(self, controller, on_back=None):
        super().__init__(expand=True, spacing=20, scroll=ft.ScrollMode.AUTO)
        self.controller = controller
        self.on_back = on_back
        
        # Filtros
        self.filtro_periodo = "Semestral"  # Semestral, Anual, Mensal
        self.filtro_ano = None  # None = Todos
        self.filtro_tipo = "Todos"
        
        self.tabela = ft.DataTable(
            columns=[],
            rows=[],
            border=ft.border.all(1, ft.Colors.WHITE10),
            border_radius=10,
            heading_row_color=ft.Colors.with_opacity(0.15, ft.Colors.BLUE_400),
            heading_row_height=50,
            data_row_min_height=45,
            data_row_max_height=55,
            column_spacing=30,
            horizontal_margin=15,
        )
        
        self.init_ui()

    def init_ui(self):
        # Dropdown de Agrupamento
        self.dd_periodo = ft.Dropdown(
            label="Agrupamento",
            options=[
                ft.dropdown.Option("Semestral"),
                ft.dropdown.Option("Anual"),
                ft.dropdown.Option("Mensal"),
            ],
            value=self.filtro_periodo,
            on_select=self.on_filtro_change,
            border=ft.InputBorder.NONE,
            filled=False,
            text_size=14,
            width=180,
        )
        
        # Dropdown de Ano
        anos = self.get_anos_disponiveis()
        self.dd_ano = ft.Dropdown(
            label="Ano",
            options=[ft.dropdown.Option("Todos")] + [ft.dropdown.Option(str(a)) for a in anos],
            value="Todos",
            on_select=self.on_filtro_change,
            border=ft.InputBorder.NONE,
            filled=False,
            text_size=14,
            width=140,
        )
        
        # Dropdown de Tipo de Transmissão
        tipos = self.get_tipos_disponiveis()
        self.dd_tipo = ft.Dropdown(
            label="Tipo de Transmissão",
            options=[ft.dropdown.Option("Todos")] + [ft.dropdown.Option(t) for t in tipos],
            value="Todos",
            on_select=self.on_filtro_change,
            border=ft.InputBorder.NONE,
            filled=False,
            text_size=14,
            width=200,
        )

        # Linha de totais
        self.total_row = ft.Container(
            content=ft.Row([], spacing=30),
            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.GREEN_400),
            border_radius=10,
            padding=15,
            on_hover=self.set_hover,
            animate=ft.Animation(300, ft.AnimationCurve.DECELERATE),
        )

        self.controls = [
            ft.Row([
                ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: self.on_back() if self.on_back else None),
                ft.Text("📊 Relatórios", size=30, weight=ft.FontWeight.BOLD),
            ], alignment=ft.MainAxisAlignment.START, spacing=10),
            
            ft.Divider(height=10, color=ft.Colors.WHITE10),
            
            # Filtros
            ft.Container(
                content=ft.Row([
                    self.wrap_filter(self.dd_periodo),
                    self.wrap_filter(self.dd_ano),
                    self.wrap_filter(self.dd_tipo),
                    ft.Container(expand=True),
                    ft.ElevatedButton(
                        "Exportar Excel",
                        icon=ft.Icons.FILE_DOWNLOAD,
                        style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE),
                        on_click=self.exportar_excel,
                        height=45,
                    ),
                ], spacing=15, alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.padding.symmetric(vertical=5),
            ),

            # Tabela
            ft.Container(
                content=self.tabela,
                border_radius=15,
                bgcolor=ft.Colors.with_opacity(0.03, ft.Colors.WHITE),
                padding=10,
            ),
            
            # Linha de Totais
            self.total_row,
        ]
        
        self.popular_tabela()

    def wrap_filter(self, control):
        return ft.Container(
            content=control,
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, -1),
                end=ft.Alignment(1, 1),
                colors=[ft.Colors.with_opacity(0.12, ft.Colors.WHITE), ft.Colors.with_opacity(0.02, ft.Colors.WHITE)]
            ),
            border_radius=12,
            border=ft.border.all(1, ft.Colors.with_opacity(0.2, ft.Colors.WHITE)),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
                offset=ft.Offset(0, 0),
            ),
            padding=ft.padding.only(left=10, right=10),
            on_hover=self.set_hover,
            animate=ft.Animation(300, ft.AnimationCurve.DECELERATE),
        )

    def get_anos_disponiveis(self):
        anos = set()
        for t in self.controller.transmissoes:
            dt = parse_date(t.data)
            if dt:
                anos.add(dt.year)
        return sorted(anos)

    def get_tipos_disponiveis(self):
        tipos = set()
        for t in self.controller.transmissoes:
            if t.tipo_transmissao:
                tipos.add(t.tipo_transmissao)
        return sorted(tipos)

    def on_filtro_change(self, e):
        self.filtro_periodo = self.dd_periodo.value
        self.filtro_ano = None if self.dd_ano.value == "Todos" else int(self.dd_ano.value)
        self.filtro_tipo = self.dd_tipo.value
        self.popular_tabela()
        self.update()

    def get_transmissoes_filtradas(self):
        filtradas = []
        for t in self.controller.transmissoes:
            dt = parse_date(t.data)
            if not dt:
                continue
            if self.filtro_ano and dt.year != self.filtro_ano:
                continue
            if self.filtro_tipo != "Todos" and t.tipo_transmissao != self.filtro_tipo:
                continue
            filtradas.append(t)
        return filtradas

    def agrupar_dados(self):
        """Agrupa as transmissões por período e calcula as estatísticas."""
        transmissoes = self.get_transmissoes_filtradas()
        grupos = {}
        
        for t in transmissoes:
            dt = parse_date(t.data)
            if not dt or t.status == "Cancelado":
                continue
            
            if self.filtro_periodo == "Semestral":
                semestre = "1º" if dt.month <= 6 else "2º"
                key = f"{semestre}/{dt.year}"
                sort_key = (dt.year, 0 if dt.month <= 6 else 1)
            elif self.filtro_periodo == "Anual":
                key = str(dt.year)
                sort_key = (dt.year, 0)
            else:  # Mensal
                meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
                key = f"{meses[dt.month - 1]}/{dt.year}"
                sort_key = (dt.year, dt.month)
            
            if key not in grupos:
                grupos[key] = {
                    "sort_key": sort_key,
                    "transmissoes": 0,
                    "publico": 0,
                    "segundos": 0,
                    "tipos": {}
                }
            
            grupos[key]["transmissoes"] += 1
            grupos[key]["publico"] += t.publico
            grupos[key]["segundos"] += converter_tempo_para_segundos(t.tempo_total)
            
            tipo = t.tipo_transmissao or "Outro"
            grupos[key]["tipos"][tipo] = grupos[key]["tipos"].get(tipo, 0) + 1
        
        # Ordenar por sort_key
        dados_ordenados = sorted(grupos.items(), key=lambda x: x[1]["sort_key"])
        return dados_ordenados

    def popular_tabela(self):
        dados = self.agrupar_dados()
        
        # Definir colunas
        self.tabela.columns = [
            ft.DataColumn(ft.Text("Período", weight=ft.FontWeight.BOLD, size=14)),
            ft.DataColumn(ft.Text("Público", weight=ft.FontWeight.BOLD, size=14), numeric=True),
            ft.DataColumn(ft.Text("Transmissões", weight=ft.FontWeight.BOLD, size=14), numeric=True),
            ft.DataColumn(ft.Text("Tipos de Transmissão", weight=ft.FontWeight.BOLD, size=14)),
            ft.DataColumn(ft.Text("Horas", weight=ft.FontWeight.BOLD, size=14)),
        ]
        
        self.tabela.rows = []
        
        total_publico = 0
        total_transmissoes = 0
        total_segundos = 0
        total_tipos = {}
        
        for periodo, info in dados:
            total_publico += info["publico"]
            total_transmissoes += info["transmissoes"]
            total_segundos += info["segundos"]
            
            for tipo, count in info["tipos"].items():
                total_tipos[tipo] = total_tipos.get(tipo, 0) + count
            
            # Formatar tipos para exibição
            tipos_str = ", ".join([f"{t}: {c}" for t, c in sorted(info["tipos"].items())])
            
            horas_str = formatar_segundos_para_tempo(info["segundos"])

            self.tabela.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(periodo, size=14, weight=ft.FontWeight.W_600)),
                        ft.DataCell(ft.Text(str(info["publico"]), size=14)),
                        ft.DataCell(ft.Text(str(info["transmissoes"]), size=14, weight=ft.FontWeight.BOLD)),
                        ft.DataCell(ft.Text(tipos_str, size=12, color=ft.Colors.WHITE70)),
                        ft.DataCell(ft.Text(horas_str, size=14)),
                    ]
                )
            )
        
        # Linha de totais
        total_tipos_str = ", ".join([f"{t}: {c}" for t, c in sorted(total_tipos.items())])
        total_horas_str = formatar_segundos_para_tempo(total_segundos)
        
        self.total_row.content = ft.Row([
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.SUMMARIZE, color=ft.Colors.GREEN_400, size=22),
                    ft.Text("TOTAL", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_400),
                ], spacing=8),
                width=130,
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("Público", size=10, color=ft.Colors.WHITE38),
                    ft.Text(f"{total_publico:,}".replace(",", "."), size=18, weight=ft.FontWeight.BOLD),
                ], spacing=-2),
                width=120,
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("Transmissões", size=10, color=ft.Colors.WHITE38),
                    ft.Text(str(total_transmissoes), size=18, weight=ft.FontWeight.BOLD),
                ], spacing=-2),
                width=120,
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("Tipos", size=10, color=ft.Colors.WHITE38),
                    ft.Text(total_tipos_str, size=12, color=ft.Colors.WHITE70),
                ], spacing=-2),
                expand=True,
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("Horas Totais", size=10, color=ft.Colors.WHITE38),
                    ft.Text(total_horas_str, size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.CYAN_400),
                ], spacing=-2),
                width=130,
            ),
        ], spacing=30)

    def exportar_excel(self, e):
        try:
            import openpyxl
        except ImportError:
            snack = ft.SnackBar(
                ft.Text("❌ Biblioteca openpyxl não encontrada. Instale com: pip install openpyxl"),
                bgcolor=ft.Colors.RED_700
            )
            self.page.overlay.append(snack)
            snack.open = True
            self.page.update()
            return
            
        import tkinter as tk
        from tkinter import filedialog
        
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        
        path = filedialog.asksaveasfilename(
            title="Salvar Relatório como...",
            defaultextension=".xlsx",
            initialfile="relatorio_transmissoes.xlsx",
            filetypes=[("Arquivos Excel", "*.xlsx")]
        )
        
        root.destroy()

        if not path:
            return
            
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
            import os
            
            wb = Workbook()
            ws = wb.active
            ws.title = "Relatório de Transmissões"
            
            # Estilos
            header_font = Font(bold=True, color="FFFFFF", size=12)
            header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
            total_font = Font(bold=True, color="006B3F", size=12)
            total_fill = PatternFill(start_color="D5F5E3", end_color="D5F5E3", fill_type="solid")
            border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )
            center = Alignment(horizontal='center', vertical='center')
            
            # Headers
            headers = ["Período", "Público", "Transmissões", "Tipos de Transmissão", "Horas"]
            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col, value=header)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = center
                cell.border = border
            
            # Dados
            dados = self.agrupar_dados()
            total_publico = 0
            total_transmissoes = 0
            total_segundos = 0
            
            for row, (periodo, info) in enumerate(dados, 2):
                total_publico += info["publico"]
                total_transmissoes += info["transmissoes"]
                total_segundos += info["segundos"]
                
                tipos_str = ", ".join([f"{t}: {c}" for t, c in sorted(info["tipos"].items())])
                horas_str = formatar_segundos_para_tempo(info["segundos"])
                
                values = [periodo, info["publico"], info["transmissoes"], tipos_str, horas_str]
                for col, value in enumerate(values, 1):
                    cell = ws.cell(row=row, column=col, value=value)
                    cell.border = border
                    if col in (2, 3):
                        cell.alignment = center
            
            # Linha Total
            total_row = len(dados) + 2
            total_values = ["TOTAL", total_publico, total_transmissoes, "", formatar_segundos_para_tempo(total_segundos)]
            for col, value in enumerate(total_values, 1):
                cell = ws.cell(row=total_row, column=col, value=value)
                cell.font = total_font
                cell.fill = total_fill
                cell.border = border
                if col in (2, 3):
                    cell.alignment = center
            
            # Ajustar largura das colunas
            ws.column_dimensions['A'].width = 18
            ws.column_dimensions['B'].width = 14
            ws.column_dimensions['C'].width = 16
            ws.column_dimensions['D'].width = 35
            ws.column_dimensions['E'].width = 14
            
            # Salvar
            caminho = path
            if not caminho.endswith(".xlsx"):
                caminho += ".xlsx"
            wb.save(caminho)
            
            def abrir_pasta(ev):
                os.startfile(os.path.dirname(caminho))
            
            snack = ft.SnackBar(
                ft.Text(f"✅ Relatório salvo como {os.path.basename(caminho)}"),
                action="Abrir Pasta",
                on_action=abrir_pasta,
                bgcolor=ft.Colors.GREEN_700,
                duration=5000
            )
            self.page.overlay.append(snack)
            snack.open = True
            self.page.update()
            
        except Exception as ex:
            snack = ft.SnackBar(
                ft.Text(f"❌ Erro ao exportar: {ex}"),
                bgcolor=ft.Colors.RED_700
            )
            self.page.overlay.append(snack)
            snack.open = True
            self.page.update()

    def set_hover(self, e):
        target = e.control.content if hasattr(e.control, "content") and isinstance(e.control, ft.GestureDetector) else e.control
        is_hover = e.data == "true"
        
        target.scale = 1.015 if is_hover else 1.0
        
        if is_hover:
            if not hasattr(target, "_orig_shadow"):
                target._orig_shadow = target.shadow
            if not hasattr(target, "_orig_border"):
                target._orig_border = target.border
                
            # Brilho sutil (Ciano para combinar com o tema)
            target.shadow = ft.BoxShadow(
                blur_radius=20,
                color=ft.Colors.with_opacity(0.15, ft.Colors.CYAN_400),
                spread_radius=1
            )
            target.border = ft.border.all(1, ft.Colors.with_opacity(0.4, ft.Colors.WHITE))
        else:
            target.shadow = getattr(target, "_orig_shadow", None)
            target.border = getattr(target, "_orig_border", None)

        target.update()
