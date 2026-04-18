import flet as ft
from controllers.transmissao_controller import TransmissaoController
from models.transmissao_model import Transmissao
from utils.helpers import normalize_date, format_date_br, get_status_info
from utils.dialog_helper import mostrar_detalhes_transmissao, abrir_menu_contexto
import os
from datetime import datetime

class HistoricoView(ft.Column):
    def __init__(self, controller: TransmissaoController, on_edit):
        super().__init__(expand=True, spacing=20, scroll=ft.ScrollMode.ADAPTIVE)
        self.controller = controller
        self.on_edit = on_edit
        self.init_ui()

    def init_ui(self):
        # Filtros
        self.txt_busca = ft.TextField(
            hint_text="Pesquisar evento, responsável ou local...",
            prefix_icon=ft.Icons.SEARCH,
            on_change=lambda _: self.filtrar(),
            expand=True,
            height=45,
            text_size=14,
            content_padding=ft.padding.only(left=10, right=10),
            border_radius=10,
            bgcolor=ft.Colors.WHITE10
        )
        
        opcoes_filtro = ["YouTube", "StreamYard+Youtube", "OBS+YOUTUBE", "ZOOM+YOUTUBE", "OBS+YOUTUBE+STREAMYARD", "GRAVAÇÃO", "StreamYard", "Zoom", "Outro"]
        self.dd_tipo_filtro = ft.Dropdown(
            label="Tipo de Transmissão",
            options=[ft.dropdown.Option("Todos")] + [ft.dropdown.Option(o) for o in opcoes_filtro],
            value="Todos",
            on_select=lambda _: self.filtrar(),
            width=250
        )

        self.btn_exportar = ft.ElevatedButton(
            "Exportar CSV", 
            icon=ft.Icons.DOWNLOAD,
            on_click=self.exportar_csv,
            style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.GREEN_700)
        )

        self.btn_exportar_excel = ft.ElevatedButton(
            "Exportar Excel",
            icon=ft.Icons.FILE_DOWNLOAD,
            on_click=self.exportar_excel,
            style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.TEAL_700)
        )

        self.lista_historico = ft.Column(expand=True, spacing=10)

        self.btn_hist_modificacoes = ft.ElevatedButton(
            "Histórico de Modificações", 
            icon=ft.Icons.HISTORY,
            on_click=self.abrir_historico_modificacoes,
            style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.BLUE_GREY_700)
        )

        self.controls = [
            ft.Row([
                ft.Text("Histórico de Transmissões", size=28, weight=ft.FontWeight.BOLD),
                ft.Row([self.btn_hist_modificacoes, self.btn_exportar_excel, self.btn_exportar], spacing=10)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            
            ft.Row([self.txt_busca, self.dd_tipo_filtro], spacing=20),
            
            ft.Container(
                content=ft.Column([
                    # Header da "Tabela" Customizada
                    ft.Container(
                        content=ft.Row([
                            ft.Text("Data", width=100, weight=ft.FontWeight.BOLD),
                            ft.Text("Evento", expand=True, weight=ft.FontWeight.BOLD),
                            ft.Text("Responsável", width=150, weight=ft.FontWeight.BOLD),
                            ft.Text("Tipo", width=120, weight=ft.FontWeight.BOLD),
                            ft.Text("Status", width=160, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                            ft.Text("Ações", width=100, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                        ], spacing=15),
                        padding=ft.padding.symmetric(horizontal=15, vertical=10),
                        bgcolor=ft.Colors.WHITE10,
                        border_radius=10,
                    ),
                    self.lista_historico
                ], spacing=10),
                expand=True
            )
        ]
        self.filtrar()

    def filtrar(self):
        termo = self.txt_busca.value.lower() if self.txt_busca.value else ""
        tipo_filtro = self.dd_tipo_filtro.value
        self.lista_historico.controls.clear()
        hoje = datetime.now().strftime("%Y-%m-%d")
        
        # Ordenar por data decrescente (mais recentes primeiro)
        sorted_list = sorted(self.controller.transmissoes, key=lambda x: normalize_date(x.data), reverse=True)
        
        for t in sorted_list:
            data_norm = normalize_date(t.data)
            
            # Filtro: Histórico não mostra transmissões agendadas futuras (fase 1, 2, 3, 4)
            status_info = get_status_info(t.status)
            is_upcoming = status_info["phase"] in ["fase 1", "fase 2", "fase 3", "fase 4"]
            
            if is_upcoming and data_norm >= hoje:
                continue

            if termo and termo not in t.evento.lower() and termo not in t.responsavel.lower() and termo not in (t.local or "").lower():
                continue
            if tipo_filtro != "Todos" and t.tipo_transmissao != tipo_filtro:
                continue
                
            color_status = status_info["color"]
            
            self.lista_historico.controls.append(
                ft.GestureDetector(
                    mouse_cursor=ft.MouseCursor.CLICK,
                    on_tap=lambda _, item=t: mostrar_detalhes_transmissao(self.page, item),
                    on_double_tap=lambda _, item=t: self.on_edit(item),
                    on_secondary_tap=lambda _, item=t: abrir_menu_contexto(self.page, item, self.controller, self.on_edit, self.confirmar_exclusao, self.filtrar),
                    on_hover=self.set_hover,
                    content=ft.Container(
                        content=ft.Row([
                            ft.Text(format_date_br(t.data), width=100, size=14),
                            ft.Text(t.evento, expand=True, size=14, weight=ft.FontWeight.W_500, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                            ft.Text(t.responsavel, width=150, size=14),
                            ft.Text(t.tipo_transmissao, width=120, size=14, color=ft.Colors.WHITE38),
                            ft.Container(
                                content=ft.Column([
                                    ft.Container(
                                        content=ft.Text(
                                            status_info["label"], 
                                            size=12, 
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.BLACK
                                        ),
                                        bgcolor=color_status,
                                        padding=ft.padding.symmetric(horizontal=10, vertical=4),
                                        border_radius=8,
                                    ),
                                    ft.Text(status_info["phase"].upper() if status_info["phase"] else "", size=9, weight=ft.FontWeight.W_300, color=ft.Colors.WHITE38)
                                ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                width=160
                            ),
                            ft.Row([
                                ft.IconButton(ft.Icons.INFO_OUTLINE, icon_color=ft.Colors.CYAN_200, icon_size=18, on_click=lambda _, item=t: mostrar_detalhes_transmissao(self.page, item), tooltip="Ver Detalhes"),
                                ft.IconButton(ft.Icons.EDIT, icon_color=ft.Colors.BLUE_200, icon_size=18, on_click=lambda _, item=t: self.on_edit(item), tooltip="Editar"),
                                ft.IconButton(ft.Icons.DELETE, icon_color=ft.Colors.RED_200, icon_size=18, on_click=lambda _, item=t: self.confirmar_exclusao(item), tooltip="Excluir"),
                            ], width=100, alignment=ft.MainAxisAlignment.CENTER)
                        ], spacing=15),
                        padding=ft.padding.symmetric(horizontal=15, vertical=10),
                        bgcolor=ft.Colors.WHITE10,
                        border_radius=10,
                        animate=ft.Animation(300, ft.AnimationCurve.DECELERATE),
                        tooltip="Clique: Ver Detalhes / Clique Duplo: Editar / Direito: Menu",
                    )
                )
            )
        try:
            if self.page:
                self.lista_historico.update()
        except:
            pass

    def set_hover(self, e):
        target = e.control.content if hasattr(e.control, "content") and isinstance(e.control, ft.GestureDetector) else e.control
        is_hover = e.data == "true"
        
        target.scale = 1.015 if is_hover else 1.0
        
        if is_hover:
            if not hasattr(target, "_orig_shadow"):
                target._orig_shadow = target.shadow
            if not hasattr(target, "_orig_border"):
                target._orig_border = target.border
                
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

    def atualizar(self):
        self.filtrar()

    def confirmar_exclusao(self, t):
        dlg = None
        
        def fechar_dialogo(e):
            dlg.open = False
            self.page.update()

        def deletar_item(e):
            self.controller.deletar(t.id)
            dlg.open = False
            self.page.update()
            self.filtrar()

        dlg = ft.AlertDialog(
            title=ft.Text("Confirmar Exclusão"),
            content=ft.Text(f"Deseja realmente excluir a transmissão '{t.evento}'?"),
            actions=[
                ft.TextButton("Cancelar", on_click=fechar_dialogo),
                ft.ElevatedButton("Excluir", bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE, on_click=deletar_item),
            ]
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    def exportar_csv(self, e):
        import tkinter as tk
        from tkinter import filedialog
        
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        
        path = filedialog.asksaveasfilename(
            title="Salvar Histórico como...",
            defaultextension=".csv",
            initialfile="historico_transmissoes.csv",
            filetypes=[("Arquivos CSV", "*.csv")]
        )
        
        root.destroy()

        if not path:
            return
            
        caminho = path
        if not caminho.endswith(".csv"):
            caminho += ".csv"
            
        sucesso = self.controller.exportar_csv(caminho)
        import os
        if sucesso:
            def abrir_pasta(ev):
                os.startfile(os.path.dirname(caminho))

            snack = ft.SnackBar(
                ft.Text(f"✅ Exportado com sucesso para {os.path.basename(caminho)}"),
                action="Abrir Pasta",
                on_action=abrir_pasta,
                bgcolor=ft.Colors.GREEN_700,
                duration=5000
            )
        else:
            snack = ft.SnackBar(
                ft.Text("❌ Erro ao exportar ou lista vazia."), 
                bgcolor=ft.Colors.RED_700
            )
            
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()

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
            title="Salvar Histórico como...",
            defaultextension=".xlsx",
            initialfile="historico_transmissoes.xlsx",
            filetypes=[("Arquivos Excel", "*.xlsx")]
        )

        root.destroy()

        if not path:
            return

        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

            wb = Workbook()
            ws = wb.active
            ws.title = "Histórico de Transmissões"

            # Estilos
            header_font = Font(bold=True, color="FFFFFF", size=12)
            header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
            border = Border(
                left=Side(style='thin'), right=Side(style='thin'),
                top=Side(style='thin'), bottom=Side(style='thin')
            )
            center = Alignment(horizontal='center', vertical='center')

            headers = ["Data", "Evento", "Responsável", "Tipo", "Modalidade", "Status",
                       "Início", "Fim", "Duração", "Público", "Local", "Operador", "Observações"]
            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col, value=header)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = center
                cell.border = border

            # Usa a mesma lista filtrada que aparece na tabela
            hoje = datetime.now().strftime("%Y-%m-%d")
            sorted_list = sorted(self.controller.transmissoes, key=lambda x: normalize_date(x.data), reverse=True)
            row_num = 2
            for t in sorted_list:
                data_norm = normalize_date(t.data)
                from utils.helpers import get_status_info
                status_info = get_status_info(t.status)
                is_upcoming = status_info["phase"] in ["fase 1", "fase 2", "fase 3", "fase 4"]
                if is_upcoming and data_norm >= hoje:
                    continue

                termo = self.txt_busca.value.lower()
                if termo and termo not in t.evento.lower() and termo not in t.responsavel.lower() and termo not in (t.local or "").lower():
                    continue
                tipo_filtro = self.dd_tipo_filtro.value
                if tipo_filtro != "Todos" and t.tipo_transmissao != tipo_filtro:
                    continue

                values = [
                    format_date_br(t.data), t.evento, t.responsavel,
                    t.tipo_transmissao, t.modalidade, status_info["label"],
                    t.horario_inicio, t.horario_fim, t.tempo_total,
                    t.publico, t.local, t.operador, t.observacoes
                ]
                for col, value in enumerate(values, 1):
                    cell = ws.cell(row=row_num, column=col, value=value)
                    cell.border = border
                    if col in (7, 8, 9, 10):
                        cell.alignment = center
                row_num += 1

            # Ajustar largura
            widths = [14, 30, 20, 20, 12, 18, 10, 10, 12, 10, 20, 15, 30]
            for i, w in enumerate(widths):
                ws.column_dimensions[chr(65 + i)].width = w

            caminho = path
            if not caminho.endswith(".xlsx"):
                caminho += ".xlsx"
            wb.save(caminho)

            def abrir_pasta(ev):
                os.startfile(os.path.dirname(caminho))

            snack = ft.SnackBar(
                ft.Text(f"✅ Histórico salvo como {os.path.basename(caminho)}"),
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

    def abrir_historico_modificacoes(self, e):
        logs = self.controller.db.obter_historico_modificacoes()
        
        tabela_logs = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("DATA/HORA")),
                ft.DataColumn(ft.Text("USUÁRIO")),
                ft.DataColumn(ft.Text("AÇÃO")),
                ft.DataColumn(ft.Text("DETALHES")),
            ],
            rows=[],
            expand=True,
            column_spacing=20
        )

        for log in logs:
            cor_acao = ft.Colors.WHITE
            if log["acao"] == "INSERÇÃO":
                cor_acao = ft.Colors.GREEN_400
            elif log["acao"] == "ALTERAÇÃO":
                cor_acao = ft.Colors.BLUE_400
            elif log["acao"] == "EXCLUSÃO":
                cor_acao = ft.Colors.RED_400
                
            tabela_logs.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(log["data_hora"], size=13)),
                        ft.DataCell(ft.Text(log["usuario"], size=13)),
                        ft.DataCell(ft.Text(log["acao"], color=cor_acao, weight=ft.FontWeight.BOLD, size=13)),
                        ft.DataCell(ft.Text(log["detalhes"], size=13)),
                    ]
                )
            )

        def exportar_txt(e):
            caminho = "data/historico_modificacoes.txt"
            linhas = ["DATA/HORA | USUARIO | ACAO | DETALHES", "-"*80]
            for log in logs:
                linhas.append(f"{log['data_hora']} | {log['usuario']} | {log['acao']} | {log['detalhes']}")
            
            try:
                import os
                if not os.path.exists("data"):
                    os.makedirs("data", exist_ok=True)
                with open(caminho, 'w', encoding='utf-8') as f:
                    f.write("\n".join(linhas))
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Salvo com sucesso em: {caminho}"), bgcolor=ft.Colors.GREEN_700)
                self.page.snack_bar.open = True
            except Exception as ex:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao exportar: {ex}"), bgcolor=ft.Colors.RED_700)
                self.page.snack_bar.open = True
            self.page.update()

        dlg_modal = None
        def fechar(e):
            dlg_modal.open = False
            self.page.update()

        dlg_modal = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.HISTORY, color=ft.Colors.BLUE_200),
                ft.Text("Histórico de Modificações"),
                ft.Container(expand=True),
                ft.ElevatedButton("EXPORTAR HISTÓRICO (.TXT)", icon=ft.Icons.DOWNLOAD, on_click=exportar_txt, bgcolor=ft.Colors.INDIGO_700, color=ft.Colors.WHITE)
            ]),
            content=ft.Container(
                content=ft.Column([tabela_logs], scroll=ft.ScrollMode.ADAPTIVE),
                width=1000,
                height=600,
                border_radius=10,
                bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE)
            ),
            actions=[
                ft.ElevatedButton("FECHAR", icon=ft.Icons.CLOSE, on_click=fechar, bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE)
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.overlay.append(dlg_modal)
        dlg_modal.open = True
        self.page.update()
