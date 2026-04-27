import flet as ft
from controllers.transmissao_controller import TransmissaoController
from datetime import datetime
from utils.helpers import normalize_date, formatar_data_semana, formatar_data_completa_semana, parse_date, get_status_info, format_date_br
from utils.dialog_helper import mostrar_detalhes_transmissao, abrir_menu_contexto
import asyncio

class DashboardView(ft.Column):
    def __init__(self, controller: TransmissaoController, on_edit, on_navigate):
        super().__init__(expand=True, spacing=30, scroll=ft.ScrollMode.AUTO)
        self.controller = controller
        self.on_edit = on_edit
        self.on_navigate = on_navigate
        self.filtro_especial = None
        self.pagina_atual = 0
        self.itens_por_pagina = 12
        
        self.relogio = ft.Text("", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.CYAN_200)
        self.data_extenso = ft.Text("", size=11, color=ft.Colors.WHITE38)
        self.txt_busca = ft.TextField(
            hint_text="Pesquisar...", 
            prefix_icon=ft.Icons.SEARCH, 
            on_change=lambda _: self.reset_pagination(), 
            height=40, 
            text_size=13, 
            bgcolor=ft.Colors.TRANSPARENT, 
            border=ft.InputBorder.NONE,
            content_padding=ft.padding.symmetric(vertical=0, horizontal=0),
            cursor_color=ft.Colors.WHITE,
            selection_color=ft.Colors.with_opacity(0.3, ft.Colors.WHITE),
        )
        
        self.search_bar = ft.Container(
            content=self.txt_busca,
            width=280,
            height=40,
            border_radius=12,
            border=ft.border.all(1, ft.Colors.with_opacity(0.15, ft.Colors.WHITE)),
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, -1),
                end=ft.Alignment(1, 1),
                colors=[
                    ft.Colors.with_opacity(0.12, ft.Colors.WHITE),
                    ft.Colors.with_opacity(0.04, ft.Colors.WHITE),
                ],
            ),
            padding=ft.padding.symmetric(horizontal=12),
            animate=ft.Animation(300, ft.AnimationCurve.DECELERATE),
            on_hover=self.on_search_hover
        )
        
        self.row_status = ft.Row(spacing=30, scroll=ft.ScrollMode.AUTO, alignment=ft.MainAxisAlignment.CENTER)
        self.lista_eventos = ft.Column(spacing=10, expand=True)
        self.paginacao_row = ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=20)
        self.resumo_publico = ft.Column(); self.resumo_mensal = ft.Column(); self.resumo_semestral = ft.Column(); self.resumo_anual = ft.Column()
        self.init_ui()

    def did_mount(self): self.running = True; self.page.run_task(self.update_clock)
    def will_unmount(self): self.running = False
    async def update_clock(self):
        while self.running:
            agora = datetime.now(); self.relogio.value = agora.strftime("%H:%M:%S"); self.data_extenso.value = agora.strftime("%A, %d de %B")
            try: self.relogio.update(); self.data_extenso.update()
            except: break
            await asyncio.sleep(1)

    def init_ui(self):
        header = ft.Row([
            # Seção Esquerda: Título
            ft.Column([
                ft.Text("TRANSMISSÕES TI - LAB | FUNDASP", size=30, weight=ft.FontWeight.BOLD), 
                ft.Text("Sistema de agendamento e calendário de transmissões", size=13, color=ft.Colors.WHITE38)
            ], spacing=0, expand=True),
            
            # Seção Central: Barra de Pesquisa
            ft.Container(
                content=self.search_bar,
                expand=True,
                alignment=ft.Alignment(0, 0)
            ),
            
            # Seção Direita: Relógio
            ft.Container(
                content=ft.Container(
                    content=ft.Column([self.relogio, self.data_extenso], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0), 
                    padding=ft.padding.symmetric(horizontal=25, vertical=8), 
                    bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.CYAN_900), 
                    border_radius=15, 
                    border=ft.border.all(1, ft.Colors.with_opacity(0.2, ft.Colors.CYAN_200))
                ),
                expand=True,
                alignment=ft.Alignment(1, 0)
            )
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER)
        status_section = ft.Container(content=self.row_status, padding=ft.padding.symmetric(vertical=10), alignment=ft.Alignment(0, 0))
        main_layout = ft.Row([
            ft.Column([
                ft.Row([ft.Icon(ft.Icons.EVENT_NOTE, color=ft.Colors.ORANGE_400), ft.Text("Próximos Eventos", size=22, weight=ft.FontWeight.BOLD)]), 
                self.lista_eventos, 
                self.paginacao_row
            ], expand=7, spacing=20), 
            ft.Column([
                ft.Row([ft.Icon(ft.Icons.BAR_CHART, color=ft.Colors.BLUE_400), ft.Text("Resumo Público", size=20, weight=ft.FontWeight.BOLD)]), 
                ft.Container(
                    content=self.resumo_publico, 
                    padding=20, 
                    bgcolor=ft.Colors.WHITE10, 
                    border_radius=15,
                    on_click=lambda _: self.on_navigate(4),
                    on_hover=self.on_summary_hover,
                    tooltip="Ver detalhes no Relatório"
                ), 
                ft.Row([
                    ft.Container(
                        content=self.resumo_mensal, 
                        padding=15, 
                        bgcolor=ft.Colors.WHITE10, 
                        border_radius=15, 
                        expand=1,
                        on_click=lambda _: self.on_navigate(4),
                        on_hover=self.on_summary_hover,
                        tooltip="Ver detalhes no Relatório"
                    ), 
                    ft.Container(
                        content=self.resumo_semestral, 
                        padding=15, 
                        bgcolor=ft.Colors.WHITE10, 
                        border_radius=15, 
                        expand=1,
                        on_click=lambda _: self.on_navigate(4),
                        on_hover=self.on_summary_hover,
                        tooltip="Ver detalhes no Relatório"
                    )
                ], spacing=15), 
                ft.Row([ft.Icon(ft.Icons.CALENDAR_MONTH, color=ft.Colors.ORANGE_400), ft.Text("Resumo Anual", size=18, weight=ft.FontWeight.BOLD)]), 
                ft.Container(
                    content=self.resumo_anual, 
                    padding=20, 
                    bgcolor=ft.Colors.WHITE10, 
                    border_radius=15,
                    on_click=lambda _: self.on_navigate(4),
                    on_hover=self.on_summary_hover,
                    tooltip="Ver detalhes no Relatório"
                )
            ], expand=3, spacing=15)
        ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START, spacing=30)
        self.controls = [header, status_section, main_layout]; self.atualizar_dados()

    def build_stat_mini(self, title, phase_key, value, icon, color):
        is_selected = self.filtro_especial == phase_key
        return ft.Container(content=ft.Row([ft.Icon(icon, color=color, size=24), ft.Column([ft.Text(title, size=14, weight=ft.FontWeight.BOLD), ft.Text(phase_key, size=10, color=ft.Colors.WHITE38), ft.Text(str(value), size=24, weight=ft.FontWeight.BOLD)], spacing=-2)], spacing=10), padding=10, border_radius=10, bgcolor=ft.Colors.with_opacity(0.15, color) if is_selected else ft.Colors.TRANSPARENT, border=ft.border.all(1, color) if is_selected else None, on_click=lambda _: self.set_filtro_especial(phase_key))

    def set_filtro_especial(self, key): self.filtro_especial = key if self.filtro_especial != key else None; self.pagina_atual = 0; self.atualizar_dados()
    def reset_pagination(self): self.pagina_atual = 0; self.atualizar_dados()
    def mudar_pagina(self, delta): self.pagina_atual += delta; self.atualizar_dados()

    def atualizar_dados(self):
        stats = self.controller.get_estatisticas()
        self.row_status.controls = [self.build_stat_mini("Aguardando", "fase 1", stats["f1"], ft.Icons.ACCESS_TIME, ft.Colors.RED_400), self.build_stat_mini("Em Reunião", "fase 2", stats["f2"], ft.Icons.GROUPS, ft.Colors.AMBER_400), self.build_stat_mini("Criação de Link", "fase 3", stats["f3"], ft.Icons.LINK, ft.Colors.CYAN_400), self.build_stat_mini("Agendado", "fase 4", stats["f4"], ft.Icons.EVENT_AVAILABLE, ft.Colors.GREEN_400), self.build_stat_mini("Finalizadas", "fase 5", stats["f5"], ft.Icons.CHECK_CIRCLE, ft.Colors.PURPLE_400), self.build_stat_mini("Total no Mês", "mes", stats["total_mes"], ft.Icons.CALENDAR_VIEW_MONTH, ft.Colors.BLUE_400), self.build_stat_mini("Horas de Live", "horas", stats["horas_totais"], ft.Icons.TIMER, ft.Colors.CYAN_ACCENT_400)]
        self.resumo_publico.controls = [ft.Row([ft.Icon(ft.Icons.PEOPLE, size=40, color=ft.Colors.BLUE_400), ft.Container(expand=True), ft.Text(str(stats["publico_total"]), size=36, weight=ft.FontWeight.BOLD)], alignment=ft.MainAxisAlignment.CENTER), ft.Text("Público Total Acumulado", size=12, color=ft.Colors.WHITE38, text_align=ft.TextAlign.CENTER), ft.ProgressBar(value=0.7, color=ft.Colors.BLUE_400, bgcolor=ft.Colors.WHITE10, height=8)]
        def stats_box(title, trans, horas, pub): return ft.Column([ft.Text(title, weight=ft.FontWeight.BOLD, size=14), ft.Row([ft.Icon(ft.Icons.CALENDAR_MONTH, size=16, color=ft.Colors.ORANGE_400), ft.Text(f"Transmissões: {trans}", size=11)]), ft.Row([ft.Icon(ft.Icons.TIMER, size=16, color=ft.Colors.GREEN_400), ft.Text(f"Horas: {horas}", size=11)]), ft.Row([ft.Icon(ft.Icons.PEOPLE, size=16, color=ft.Colors.PURPLE_400), ft.Text(f"Público: {pub}", size=11)])], spacing=5)
        self.resumo_mensal.controls = [stats_box("Resumo Mensal", stats["total_mes"], stats["horas_mes"], stats["publico_mes"])]; self.resumo_semestral.controls = [stats_box("Resumo Semestral", stats["total_semestre"], stats["horas_semestre"], stats["publico_semestre"])]; self.resumo_anual.controls = [ft.Row([ft.Icon(ft.Icons.SHOW_CHART, color=ft.Colors.CYAN_400), ft.Column([ft.Text("Transmissões no Ano", size=10, color=ft.Colors.WHITE38), ft.Text(str(stats["total_ano"]), size=18, weight=ft.FontWeight.BOLD)])]), ft.Row([ft.Icon(ft.Icons.TIMER, color=ft.Colors.BLUE_400), ft.Column([ft.Text("Total Horas (Ano)", size=10, color=ft.Colors.WHITE38), ft.Text(stats["horas_ano"], size=18, weight=ft.FontWeight.BOLD)])]), ft.Row([ft.Icon(ft.Icons.PEOPLE, color=ft.Colors.PINK_400), ft.Column([ft.Text("Público Total (Ano)", size=10, color=ft.Colors.WHITE38), ft.Text(str(stats["publico_ano"]), size=18, weight=ft.FontWeight.BOLD)])])]
        
        termo = self.txt_busca.value.lower() if self.txt_busca.value else ""; hoje_str = datetime.now().strftime("%Y-%m-%d")
        if self.filtro_especial:
            if self.filtro_especial.startswith("fase"): eventos = [t for t in self.controller.transmissoes if get_status_info(t.status)["phase"] == self.filtro_especial]
            elif self.filtro_especial == "mes": agora = datetime.now(); eventos = [t for t in self.controller.transmissoes if parse_date(t.data).month == agora.month and parse_date(t.data).year == agora.year]
            else: eventos = self.controller.transmissoes
        else: eventos = [t for t in self.controller.transmissoes if normalize_date(t.data) >= hoje_str]
        if termo: 
            # Filtro por termo de busca
            eventos = [
                t for t in eventos 
                if termo in t.evento.lower() 
                or termo in t.responsavel.lower() 
                or termo in format_date_br(t.data)
            ]
        eventos.sort(key=lambda x: (normalize_date(x.data), x.horario_inicio))
        
        tp_total = (len(eventos) + self.itens_por_pagina - 1) // self.itens_por_pagina
        eventos_pag = eventos[self.pagina_atual*self.itens_por_pagina : (self.pagina_atual+1)*self.itens_por_pagina]
        self.lista_eventos.controls = []
        for t in eventos_pag:
            self.lista_eventos.controls.append(self.create_event_row(t))
        self.paginacao_row.visible = len(eventos) > 0
        self.paginacao_row.controls = [ft.IconButton(ft.Icons.ARROW_BACK_IOS_NEW, on_click=lambda _: self.mudar_pagina(-1), disabled=self.pagina_atual == 0), ft.Text(f"Página {self.pagina_atual + 1} de {max(1, tp_total)}", weight=ft.FontWeight.BOLD), ft.IconButton(ft.Icons.ARROW_FORWARD_IOS, on_click=lambda _: self.mudar_pagina(1), disabled=self.pagina_atual >= tp_total - 1)]
        try: self.update()
        except: pass

    def create_event_row(self, t):
        s_info = get_status_info(t.status)
        data_partes = formatar_data_semana(t.data).split(' - ')
        data_num = data_partes[0]
        dia_semana = data_partes[1] if len(data_partes) > 1 else ""
        
        return ft.GestureDetector(
            content=ft.Container(
                content=ft.Row([
                    # Data (Versão compacta para Dashboard)
                    ft.Container(
                        content=ft.Column([
                            ft.Text(data_num, weight=ft.FontWeight.BOLD, size=14, color=ft.Colors.BLACK),
                            ft.Text(dia_semana.upper(), size=8, color=ft.Colors.BLACK54, weight=ft.FontWeight.BOLD),
                        ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        bgcolor=s_info["color"],
                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                        border_radius=8,
                        width=85,
                        alignment=ft.Alignment(0, 0)
                    ),
                    # Info principal (Evento, Horário, Tipo, Modalidade)
                    ft.Column([
                        ft.Text(t.evento, size=15, weight=ft.FontWeight.BOLD, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Row([
                            ft.Text(f"{t.horario_inicio} às {t.horario_fim}", size=11, weight=ft.FontWeight.W_500, color=ft.Colors.CYAN_200),
                            ft.Text(" • ", color=ft.Colors.WHITE24),
                            ft.Text(t.modalidade or "N/A", size=11, color=ft.Colors.WHITE38),
                            ft.Text(" • ", color=ft.Colors.WHITE24),
                            ft.Text(t.tipo_transmissao or "-", size=11, color=ft.Colors.ORANGE_300, weight=ft.FontWeight.W_500),
                        ], spacing=5),
                    ], expand=True, spacing=2),
                    # Responsável e Local
                    ft.Column([
                        ft.Row([ft.Icon(ft.Icons.PERSON, size=12, color=ft.Colors.WHITE38), ft.Text(t.responsavel, size=11, color=ft.Colors.WHITE70, overflow=ft.TextOverflow.ELLIPSIS)], spacing=5),
                        ft.Row([ft.Icon(ft.Icons.LOCATION_ON, size=12, color=ft.Colors.WHITE38), ft.Text(t.local, size=10, color=ft.Colors.WHITE38, overflow=ft.TextOverflow.ELLIPSIS)], spacing=5),
                    ], spacing=2, width=180),
                    # Status
                    ft.Container(
                        content=ft.Row([
                            ft.Container(bgcolor=s_info["color"], width=6, height=6, border_radius=3),
                            ft.Text(s_info["label"], size=10, color=s_info["color"], weight=ft.FontWeight.BOLD)
                        ], spacing=5),
                        width=110
                    ),
                    # Ações rápidas
                    ft.Row([
                        ft.IconButton(ft.Icons.INFO_OUTLINE, icon_size=16, icon_color=ft.Colors.CYAN_200, tooltip="Detalhes", on_click=lambda _: mostrar_detalhes_transmissao(self.page, t, self.controller, self.atualizar_dados, on_edit=self.on_edit)),
                        ft.IconButton(ft.Icons.EDIT_NOTE, icon_size=18, icon_color=ft.Colors.BLUE_200, tooltip="Editar", on_click=lambda _: self.on_edit(t)),
                    ], spacing=0)
                ], spacing=15),
                padding=10, 
                border_radius=12, 
                bgcolor=ft.Colors.WHITE10, 
                border=ft.border.all(1, ft.Colors.with_opacity(0.05, ft.Colors.WHITE)),
                on_hover=lambda e: self.on_row_hover(e)
            ),
            on_tap=lambda _: mostrar_detalhes_transmissao(self.page, t, self.controller, self.atualizar_dados, on_edit=self.on_edit),
            on_secondary_tap=lambda e: abrir_menu_contexto(self.page, t, self.controller, self.on_edit, self.confirmar_exclusao, self.atualizar_dados),
        )

    def on_search_hover(self, e):
        e.control.border = ft.border.all(1, ft.Colors.with_opacity(0.4, ft.Colors.WHITE)) if e.data == "true" else ft.border.all(1, ft.Colors.with_opacity(0.15, ft.Colors.WHITE))
        e.control.update()

    def on_row_hover(self, e):
        e.control.bgcolor = ft.Colors.with_opacity(0.15, ft.Colors.WHITE) if e.data == "true" else ft.Colors.WHITE10
        e.control.update()

    def on_summary_hover(self, e):
        e.control.bgcolor = ft.Colors.with_opacity(0.18, ft.Colors.WHITE) if e.data == "true" else ft.Colors.WHITE10
        e.control.update()

    def confirmar_exclusao(self, t):
        dlg = ft.AlertDialog(title=ft.Text("Confirmar Exclusão"), content=ft.Text(f"Deseja excluir '{t.evento}'?"), actions=[ft.TextButton("Cancelar", on_click=lambda _: self.fechar_dlg(dlg)), ft.ElevatedButton("Excluir", bgcolor=ft.Colors.RED_700, on_click=lambda _: self.deletar_e_fechar(t, dlg))])
        self.page.overlay.append(dlg); dlg.open = True; self.page.update()
    def fechar_dlg(self, dlg): dlg.open = False; self.page.update()
    def deletar_e_fechar(self, t, dlg): self.controller.deletar(t.id); dlg.open = False; self.atualizar_dados()
