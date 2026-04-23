import flet as ft
from datetime import datetime
from utils.helpers import normalize_date, format_date_br, check_status_match, get_status_info
from utils.dialog_helper import mostrar_detalhes_transmissao, abrir_menu_contexto

class HistoricoView(ft.Column):
    def __init__(self, controller, on_edit):
        super().__init__(expand=True, spacing=20, scroll=ft.ScrollMode.AUTO)
        self.controller = controller
        self.on_edit = on_edit
        self.init_ui()

    def init_ui(self):
        from utils.helpers import get_status_options
        self.sort_column_index = 0
        self.sort_ascending = False

        self.txt_busca = ft.TextField(label="Pesquisar no Histórico", prefix_icon=ft.Icons.SEARCH, on_change=lambda _: self.filtrar(), expand=True, height=45, text_size=13)
        self.dd_status = ft.Dropdown(label="Status", options=[ft.dropdown.Option("Todos")] + [ft.dropdown.Option(o) for o in get_status_options()], value="Todos", on_select=lambda _: self.filtrar(), width=180, height=45, text_size=12)
        self.dd_tipo = ft.Dropdown(label="Tipo", options=[ft.dropdown.Option(o) for o in ["Todos", "YouTube", "StreamYard", "Zoom", "OBS"]], value="Todos", on_select=lambda _: self.filtrar(), width=150, height=45, text_size=12)
        self.dd_modalidade = ft.Dropdown(label="Modalidade", options=[ft.dropdown.Option(o) for o in ["Todos", "Online", "Presencial", "Híbrido"]], value="Todos", on_select=lambda _: self.filtrar(), width=150, height=45, text_size=12)
        
        self.tabela = ft.DataTable(
            sort_column_index=self.sort_column_index,
            sort_ascending=self.sort_ascending,
            columns=[
                ft.DataColumn(ft.Text("Data"), on_sort=self.on_sort_click),
                ft.DataColumn(ft.Text("Horário"), on_sort=self.on_sort_click),
                ft.DataColumn(ft.Text("Evento"), on_sort=self.on_sort_click),
                ft.DataColumn(ft.Text("Responsável"), on_sort=self.on_sort_click),
                ft.DataColumn(ft.Text("Tipo"), on_sort=self.on_sort_click),
                ft.DataColumn(ft.Text("Modalidade"), on_sort=self.on_sort_click),
                ft.DataColumn(ft.Text("Local"), on_sort=self.on_sort_click),
                ft.DataColumn(ft.Text("Operador"), on_sort=self.on_sort_click),
                ft.DataColumn(ft.Text("Status"), on_sort=self.on_sort_click),
                ft.DataColumn(ft.Text("Ações")),
            ],
            column_spacing=20,
            rows=[],
            heading_row_color=ft.Colors.with_opacity(0.1, ft.Colors.BLUE_400),
            border_radius=10,
        )

        self.controls = [
            ft.Row([ft.Text("📜 Histórico de Transmissões", size=30, weight=ft.FontWeight.BOLD), ft.Container(expand=True)], alignment=ft.MainAxisAlignment.START),
            ft.Row([self.txt_busca, self.dd_status, self.dd_tipo, self.dd_modalidade], spacing=10),
            ft.Container(content=ft.Row([self.tabela], scroll=ft.ScrollMode.AUTO), padding=10, bgcolor=ft.Colors.WHITE10, border_radius=15, expand=True)
        ]
        self.filtrar()

    def on_sort_click(self, e):
        self.sort_column_index = e.column_index
        self.sort_ascending = not self.sort_ascending # Toggle ascending/descending
        self.tabela.sort_column_index = self.sort_column_index
        self.tabela.sort_ascending = self.sort_ascending
        self.filtrar()

    def filtrar(self):
        termo = self.txt_busca.value.lower() if self.txt_busca.value else ""
        status = self.dd_status.value
        tipo = self.dd_tipo.value
        modalidade = self.dd_modalidade.value
        
        self.tabela.rows = []
        eventos = []
        for t in self.controller.transmissoes:
            if termo:
                # Localiza em todos os campos relevantes
                campos = [
                    t.evento,
                    t.responsavel,
                    format_date_br(t.data),
                    f"{t.horario_inicio} às {t.horario_fim}",
                    t.tipo_transmissao,
                    t.modalidade,
                    t.local,
                    t.status,
                    getattr(t, 'operador', '')
                ]
                if not any(termo in str(c).lower() for c in campos if c):
                    continue

            if not check_status_match(t.status, status): continue
            if tipo != "Todos" and t.tipo_transmissao != tipo: continue
            if modalidade != "Todos" and t.modalidade != modalidade: continue
            eventos.append(t)

        def get_sort_key(t):
            if self.sort_column_index == 0: return (normalize_date(t.data), t.horario_inicio)
            if self.sort_column_index == 1: return t.horario_inicio
            if self.sort_column_index == 2: return t.evento.lower()
            if self.sort_column_index == 3: return t.responsavel.lower()
            if self.sort_column_index == 4: return t.tipo_transmissao.lower() if t.tipo_transmissao else ""
            if self.sort_column_index == 5: return t.modalidade.lower() if t.modalidade else ""
            if self.sort_column_index == 6: return t.local.lower() if t.local else ""
            if self.sort_column_index == 7: return t.operador.lower() if hasattr(t, 'operador') and t.operador else ""
            if self.sort_column_index == 8: return t.status.lower()
            return (normalize_date(t.data), t.horario_inicio)

        eventos.sort(key=get_sort_key, reverse=not self.sort_ascending)
        
        for t in eventos:
            status_info = get_status_info(t.status)
            self.tabela.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(format_date_br(t.data), size=12)),
                        ft.DataCell(ft.Text(f"{t.horario_inicio} às {t.horario_fim}", size=12, weight=ft.FontWeight.BOLD, no_wrap=True)),
                        ft.DataCell(
                            ft.Container(
                                content=ft.GestureDetector(
                                    content=ft.Text(t.evento, size=13, weight=ft.FontWeight.W_500, color=ft.Colors.BLUE_200),
                                    on_tap=lambda _, item=t: mostrar_detalhes_transmissao(self.page, item, self.controller, self.atualizar),
                                    on_secondary_tap=lambda e, item=t: abrir_menu_contexto(self.page, item, self.controller, self.on_edit, self.confirmar_exclusao, self.atualizar),
                                ),
                                width=300, 
                                padding=ft.padding.symmetric(vertical=5)
                            )
                        ),
                        ft.DataCell(ft.Text(t.responsavel, size=12)),
                        ft.DataCell(ft.Text(t.tipo_transmissao or "-", size=12)),
                        ft.DataCell(ft.Text(t.modalidade or "-", size=12)),
                        ft.DataCell(ft.Text(t.local or "-", size=11, color=ft.Colors.WHITE38)),
                        ft.DataCell(ft.Text(t.operador or "-", size=12)),
                        ft.DataCell(ft.Container(content=ft.Text(status_info["label"], size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK), bgcolor=status_info["color"], padding=ft.padding.symmetric(horizontal=10, vertical=4), border_radius=8)),
                        ft.DataCell(ft.Row([
                            ft.IconButton(ft.Icons.INFO_OUTLINE, icon_size=18, icon_color=ft.Colors.CYAN_200, on_click=lambda _, item=t: mostrar_detalhes_transmissao(self.page, item, self.controller, self.atualizar)),
                            ft.IconButton(ft.Icons.EDIT, icon_size=18, icon_color=ft.Colors.BLUE_200, on_click=lambda _, item=t: self.on_edit(item)),
                            ft.IconButton(ft.Icons.DELETE, icon_size=18, icon_color=ft.Colors.RED_200, on_click=lambda _, item=t: self.confirmar_exclusao(item)),
                        ], spacing=0)),
                    ]
                )
            )
        try:
            if self.page: self.tabela.update()
        except: pass

    def atualizar(self): self.filtrar()

    def confirmar_exclusao(self, t):
        dlg = ft.AlertDialog(title=ft.Text("Confirmar Exclusão"), content=ft.Text(f"Deseja excluir '{t.evento}'?"), actions=[ft.TextButton("Cancelar", on_click=lambda _: self.fechar_dlg(dlg)), ft.ElevatedButton("Excluir", bgcolor=ft.Colors.RED_700, on_click=lambda _: self.deletar_e_fechar(t, dlg))])
        self.page.overlay.append(dlg); dlg.open = True; self.page.update()
    
    def fechar_dlg(self, dlg): dlg.open = False; self.page.update()
    def deletar_e_fechar(self, t, dlg): self.controller.deletar(t.id); dlg.open = False; self.filtrar()
