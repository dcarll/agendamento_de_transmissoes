import flet as ft
from controllers.transmissao_controller import TransmissaoController
from datetime import datetime
from utils.helpers import normalize_date, formatar_data_semana, formatar_data_completa_semana, parse_date, get_status_info
from utils.dialog_helper import mostrar_detalhes_transmissao, abrir_menu_contexto
import asyncio

class DashboardView(ft.Column):
    def __init__(self, controller: TransmissaoController, on_edit):
        super().__init__(expand=True, spacing=30, scroll=ft.ScrollMode.AUTO)
        self.controller = controller
        self.on_edit = on_edit
        self.filtro_especial = None
        self.pagina_atual = 0
        self.itens_por_pagina = 12
        
        self.relogio = ft.Text("", size=30, weight=ft.FontWeight.BOLD, color=ft.Colors.CYAN_200)
        self.data_extenso = ft.Text("", size=12, color=ft.Colors.WHITE70)
        self.txt_busca = ft.TextField(hint_text="Pesquisar...", prefix_icon=ft.Icons.SEARCH, on_change=lambda _: self.reset_pagination(), expand=True, height=45, text_size=13, bgcolor=ft.Colors.WHITE10, border_radius=10, border=ft.InputBorder.NONE)
        
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
        header = ft.Row([ft.Column([ft.Text("TRANSMISSÕES DTI/LAB!", size=32, weight=ft.FontWeight.BOLD), ft.Text("Sistema de Transmissões DTI/LABORATÓRIOS", size=14, color=ft.Colors.WHITE38)], spacing=0), ft.Container(expand=True), ft.Container(content=ft.Column([self.relogio, self.data_extenso], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0), padding=ft.padding.symmetric(horizontal=30, vertical=10), bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.CYAN_900), border_radius=15, border=ft.border.all(1, ft.Colors.with_opacity(0.2, ft.Colors.CYAN_200))), ft.Container(expand=True), ft.Row([self.txt_busca, ft.IconButton(ft.Icons.REFRESH, on_click=lambda _: self.atualizar_dados())], spacing=10)], vertical_alignment=ft.CrossAxisAlignment.CENTER)
        status_section = ft.Container(content=self.row_status, padding=ft.padding.symmetric(vertical=10), alignment=ft.Alignment(0, 0))
        main_layout = ft.Row([ft.Column([ft.Row([ft.Icon(ft.Icons.EVENT_NOTE, color=ft.Colors.ORANGE_400), ft.Text("Próximos Eventos", size=22, weight=ft.FontWeight.BOLD)]), self.lista_eventos, self.paginacao_row], expand=7, spacing=20), ft.Column([ft.Row([ft.Icon(ft.Icons.BAR_CHART, color=ft.Colors.BLUE_400), ft.Text("Resumo Público", size=20, weight=ft.FontWeight.BOLD)]), ft.Container(content=self.resumo_publico, padding=20, bgcolor=ft.Colors.WHITE10, border_radius=15), ft.Row([ft.Container(content=self.resumo_mensal, padding=15, bgcolor=ft.Colors.WHITE10, border_radius=15, expand=1), ft.Container(content=self.resumo_semestral, padding=15, bgcolor=ft.Colors.WHITE10, border_radius=15, expand=1)], spacing=15), ft.Row([ft.Icon(ft.Icons.CALENDAR_MONTH, color=ft.Colors.ORANGE_400), ft.Text("Resumo Anual", size=18, weight=ft.FontWeight.BOLD)]), ft.Container(content=self.resumo_anual, padding=20, bgcolor=ft.Colors.WHITE10, border_radius=15)], expand=3, spacing=15)], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START, spacing=30)
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
        if termo: eventos = [t for t in eventos if termo in t.evento.lower() or termo in t.responsavel.lower()]
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
        return ft.GestureDetector(
            content=ft.Container(
                content=ft.Row([
                    ft.Container(content=ft.Text(formatar_data_semana(t.data), weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.BLACK), bgcolor=s_info["color"], padding=ft.padding.symmetric(horizontal=10, vertical=5), border_radius=8, width=105, alignment=ft.Alignment(0, 0)),
                    ft.Column([ft.Text(t.evento, size=16, weight=ft.FontWeight.BOLD), ft.Text(f"{t.horario_inicio} às {t.horario_fim} - {t.responsavel} | {t.local}", size=12, color=ft.Colors.WHITE70)], expand=True, spacing=2),
                    ft.Container(content=ft.Row([ft.Container(bgcolor=s_info["color"], width=8, height=8, border_radius=4), ft.Text(s_info["label"], size=11, color=s_info["color"], weight=ft.FontWeight.BOLD)], spacing=5), width=140),
                    ft.Row([ft.IconButton(ft.Icons.INFO_OUTLINE, icon_size=18, icon_color=ft.Colors.CYAN_200, on_click=lambda _: mostrar_detalhes_transmissao(self.page, t, self.controller, self.atualizar_dados)), ft.IconButton(ft.Icons.EDIT_NOTE, icon_size=18, icon_color=ft.Colors.BLUE_200, on_click=lambda _: self.on_edit(t)), ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_size=18, icon_color=ft.Colors.RED_300, on_click=lambda _: self.confirmar_exclusao(t))], spacing=0)
                ], spacing=15),
                padding=12, border_radius=12, bgcolor=ft.Colors.WHITE10, border=ft.border.all(1, ft.Colors.with_opacity(0.05, ft.Colors.WHITE))
            ),
            on_tap=lambda _: mostrar_detalhes_transmissao(self.page, t, self.controller, self.atualizar_dados),
            on_secondary_tap=lambda e: abrir_menu_contexto(self.page, t, self.controller, self.on_edit, self.confirmar_exclusao, self.atualizar_dados),
        )

    def confirmar_exclusao(self, t):
        dlg = ft.AlertDialog(title=ft.Text("Confirmar Exclusão"), content=ft.Text(f"Deseja excluir '{t.evento}'?"), actions=[ft.TextButton("Cancelar", on_click=lambda _: self.fechar_dlg(dlg)), ft.ElevatedButton("Excluir", bgcolor=ft.Colors.RED_700, on_click=lambda _: self.deletar_e_fechar(t, dlg))])
        self.page.overlay.append(dlg); dlg.open = True; self.page.update()
    def fechar_dlg(self, dlg): dlg.open = False; self.page.update()
    def deletar_e_fechar(self, t, dlg): self.controller.deletar(t.id); dlg.open = False; self.atualizar_dados()
