import flet as ft
from controllers.transmissao_controller import TransmissaoController
from datetime import datetime
from utils.helpers import normalize_date, formatar_data_semana
from utils.dialog_helper import mostrar_detalhes_transmissao, abrir_menu_contexto
import asyncio

class DashboardView(ft.Column):
    def __init__(self, controller: TransmissaoController, on_edit):
        self.filtro_especial = None # Garante que existe antes de qualquer cálculo
        super().__init__(
            expand=True,
            spacing=25,
            scroll=ft.ScrollMode.ADAPTIVE
        )
        self.controller = controller
        self.on_edit = on_edit
        self.pagina_atual = 0
        self.itens_por_página = 10
        self.txt_busca = ft.TextField(
            hint_text="Pesquisar evento, responsável ou local...",
            prefix_icon=ft.Icons.SEARCH,
            on_change=lambda _: self.mudar_busca(),
            expand=True,
            height=45,
            text_size=14,
            content_padding=ft.padding.only(left=10, right=10),
            border_radius=10,
            bgcolor=ft.Colors.WHITE10
        )
        
        # Elementos do Relogio Neon
        self.lbl_relogio_hora = ft.Text("00:00:00", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.CYAN_400, font_family="Consolas")
        self.lbl_relogio_data = ft.Text("Carregando...", size=11, color=ft.Colors.CYAN_200, weight=ft.FontWeight.W_300)
        
        self.lista_container = ft.Column(spacing=15)
        self.cards_container = ft.Row(spacing=15, wrap=True)
        self.summary_container = ft.Column(expand=2, spacing=15)

        self.controls = [
            ft.Row(
                [
                    ft.Column([
                        ft.Text("TRANSMISSÕES DTI/LAB!", size=32, weight=ft.FontWeight.BOLD),
                        ft.Text("Sistema de Transmissões DTI/LABORATÓRIOS", size=16, color=ft.Colors.WHITE70),
                    ], expand=2),
                    
                    ft.Container(
                        content=ft.Column([
                            self.lbl_relogio_hora,
                            self.lbl_relogio_data
                        ], spacing=-5, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=ft.padding.symmetric(horizontal=30, vertical=10),
                        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.CYAN_900),
                        border_radius=15,
                        border=ft.border.all(1, ft.Colors.CYAN_700),
                        shadow=ft.BoxShadow(
                            blur_radius=20,
                            color=ft.Colors.with_opacity(0.2, ft.Colors.CYAN_400),
                            spread_radius=1
                        ),
                    ),
                    
                    ft.Row([self.txt_busca, ft.IconButton(ft.Icons.REFRESH, on_click=lambda _: self.atualizar())], spacing=10, expand=3),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            
            self.cards_container,
            
            ft.Row([
                ft.Column([
                    ft.Text("📅 Próximos Eventos", size=22, weight=ft.FontWeight.W_600),
                    self.lista_container
                ], expand=3, spacing=15),
                
                self.summary_container
            ], spacing=30, alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START)
        ]

        self.init_ui()

    def init_ui(self):
        stats = self.controller.get_stats()
        
        # Cards
        self.cards_container.controls = [
            self.create_stat_card("Aguardando", "fase 1", str(stats['ativas']), ft.Colors.RED_400, ft.Icons.SCHEDULE, lambda _: self.filtrar_status("Aguardando (Fase 1)")),
            self.create_stat_card("Em Reunião", "fase 2", str(stats['em_reuniao']), ft.Colors.AMBER_400, ft.Icons.GROUPS, lambda _: self.filtrar_status("Em Reunião (Fase 2)")),
            self.create_stat_card("Criação de Links", "fase 3", str(stats['criacao_links']), ft.Colors.TEAL_400, ft.Icons.LINK, lambda _: self.filtrar_status("Criação de Links (Fase 3)")),
            self.create_stat_card("Agendado", "fase 4", str(stats['agendado_f4']), ft.Colors.GREEN_400, ft.Icons.EVENT_AVAILABLE, lambda _: self.filtrar_status("Agendado (Fase 4)")),
            self.create_stat_card("Finalizadas", "fase 5", str(stats['concluidas']), ft.Colors.PURPLE_400, ft.Icons.CHECK_CIRCLE, lambda _: self.filtrar_status("Finalizado (Fase 5)")),
            self.create_stat_card("Canceladas", "", str(stats['cancelados']), ft.Colors.BROWN, ft.Icons.CANCEL, lambda _: self.filtrar_status("Cancelado")),
            self.create_stat_card("Total no Mês", "", str(stats['total_mensal']), ft.Colors.BLUE_400, ft.Icons.CALENDAR_TODAY, lambda _: self.filtrar_mes()),
            self.create_stat_card("Horas de Live", "", stats['horas_totais'], ft.Colors.CYAN_400, ft.Icons.ALARM, None),
        ]
        
        # Summary
        self.summary_container.controls = self.create_summary_column_controls(stats)
        
        self.popular_lista()

        try:
            if self.page:
                self.cards_container.update()
                self.summary_container.update()
                self.lista_container.update()
        except:
            pass

    def popular_lista(self):
        self.lista_container.controls = [self.create_quick_calendar_list()]
        

    def filtrar_status(self, status):
        self.filtro_especial = None
        # Define o termo de busca como o status para filtrar a lista
        self.txt_busca.value = status
        self.txt_busca.update()
        self.mudar_busca()

    def filtrar_mes(self):
        self.filtro_especial = "mes"
        self.txt_busca.value = ""
        self.txt_busca.update()
        self.mudar_busca()

    def create_stat_card(self, title, phase, value, color, icon, on_click=None):
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row([
                        ft.Icon(icon, color=color, size=24),
                        ft.Column([
                            ft.Text(title, size=16, color=ft.Colors.WHITE70, weight=ft.FontWeight.W_500),
                            ft.Text(phase, size=12, color=ft.Colors.WHITE38, italic=True) if phase else ft.Container()
                        ], spacing=-5),
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Text(value, size=28, weight=ft.FontWeight.BOLD, no_wrap=True, text_align=ft.TextAlign.CENTER),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            width=185,
            height=130,
            bgcolor="surface-variant",
            border_radius=20,
            padding=15,
            on_click=on_click,
            on_hover=self.set_hover,
            ink=True,
            animate=ft.Animation(300, ft.AnimationCurve.DECELERATE),
        )

    def create_quick_calendar_list(self):
        # Pega as próximas transmissões agendadas
        hoje = datetime.now()
        hoje_str = hoje.strftime("%Y-%m-%d")
        termo = self.txt_busca.value.lower() if self.txt_busca.value else ""
        
        # Filtro Base
        if self.filtro_especial == "mes":
            # Filtra tudo do mês atual
            lista_base = []
            from utils.helpers import parse_date
            for t in self.controller.transmissoes:
                dt = parse_date(t.data)
                if dt and dt.month == hoje.month and dt.year == hoje.year:
                    lista_base.append(t)
        elif not termo:
            # Padrão: Próximas e Em Andamento
            from utils.helpers import get_status_info 
            lista_base = [
                t for t in self.controller.transmissoes 
                if normalize_date(t.data) >= hoje_str or get_status_info(t.status)["phase"] == "fase 1"
            ]
        else:
            # Busca por texto e/ou status
            from utils.helpers import check_status_match
            lista_base = [
                t for t in self.controller.transmissoes 
                if termo in t.evento.lower() or 
                   termo in t.responsavel.lower() or 
                   termo in (t.local or "").lower() or
                   check_status_match(t.status, self.txt_busca.value)
            ]
            
        # Ordena: Por data e horário de início
        from utils.helpers import get_status_info
        lista_base.sort(key=lambda x: (normalize_date(x.data), x.horario_inicio))
        
        total_paginas = (len(lista_base) + self.itens_por_página - 1) // self.itens_por_página
        
        if not lista_base:
            return ft.Container(
                content=ft.Text("Nenhum evento encontrado.", color=ft.Colors.WHITE38),
                padding=20,
                bgcolor=ft.Colors.WHITE10,
                border_radius=15
            )

        # Slice da página atual
        inicio = self.pagina_atual * self.itens_por_página
        fim = inicio + self.itens_por_página
        itens_pagina = lista_base[inicio:fim]

        def get_status_color(status):
            return get_status_info(status)["color"]

        items = []
        for t in itens_pagina:
            color_status = get_status_color(t.status)
            gradient = ft.LinearGradient(
                begin=ft.Alignment(-1, 0),
                end=ft.Alignment(1, 0),
                colors=[ft.Colors.with_opacity(0.15, color_status), ft.Colors.with_opacity(0.05, ft.Colors.BLACK)]
            )
            
            items.append(
                ft.GestureDetector(
                    mouse_cursor=ft.MouseCursor.CLICK,
                    on_tap=lambda _, item=t: mostrar_detalhes_transmissao(self.page, item),
                    on_double_tap=lambda _, item=t: self.on_edit(item),
                    on_secondary_tap=lambda _, item=t: abrir_menu_contexto(self.page, item, self.controller, self.on_edit, self.confirmar_exclusao, self.atualizar),
                    on_hover=self.set_hover,
                    content=ft.Container(
                        content=ft.Row([
                            ft.Container(
                                content=ft.Text(formatar_data_semana(t.data), weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK, size=13),
                                bgcolor=color_status,
                                padding=8,
                                border_radius=10,
                                width=110,
                                alignment=ft.Alignment.CENTER
                            ),
                            ft.Column([
                                ft.Text(t.evento, weight=ft.FontWeight.BOLD, size=18),
                                ft.Text(f"{t.horario_inicio} às {t.horario_fim} - {t.responsavel}", size=14, color=ft.Colors.WHITE70),
                            ], spacing=2, expand=True),
                            ft.Row([
                                ft.IconButton(
                                    ft.Icons.INFO_OUTLINED,
                                    icon_size=18,
                                    icon_color=ft.Colors.CYAN_200,
                                    on_click=lambda _, item=t: mostrar_detalhes_transmissao(self.page, item),
                                    tooltip="Ver Detalhes"
                                ),
                                ft.IconButton(
                                    ft.Icons.EDIT_OUTLINED,
                                    icon_size=18,
                                    icon_color=ft.Colors.WHITE38,
                                    on_click=lambda _, item=t: self.on_edit(item),
                                    tooltip="Editar"
                                ),
                            ], spacing=0),
                            ft.Container(
                                content=ft.Text(t.tipo_transmissao, size=10, weight=ft.FontWeight.BOLD),
                                bgcolor=ft.Colors.BLUE_700,
                                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                border_radius=10
                            )
                        ], spacing=15),
                        padding=12,
                        gradient=gradient,
                        border_radius=15,
                        border=ft.border.all(1, ft.Colors.with_opacity(0.1, color_status)),
                        animate=ft.Animation(300, ft.AnimationCurve.DECELERATE),
                        tooltip="Clique: Ver Detalhes / Clique Duplo: Editar / Direito: Menu",
                    )
                )
            )
        
        # Paginação UI
        paginacao_buttons = ft.Row([
            ft.IconButton(
                ft.Icons.ARROW_BACK_IOS_NEW, 
                on_click=lambda _: self.mudar_pagina(-1),
                disabled=self.pagina_atual == 0,
                icon_size=16
            ),
            ft.Text(f"Página {self.pagina_atual + 1} de {max(1, total_paginas)}", size=14, color=ft.Colors.WHITE70),
            ft.IconButton(
                ft.Icons.ARROW_FORWARD_IOS, 
                on_click=lambda _: self.mudar_pagina(1),
                disabled=self.pagina_atual >= total_paginas - 1,
                icon_size=16
            ),
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=20)
        
        return ft.Column(controls=items + [paginacao_buttons], spacing=10)

    def mudar_busca(self):
        self.filtro_especial = None
        self.pagina_atual = 0
        self.popular_listas_ajax()

    def popular_listas_ajax(self):
        if hasattr(self, 'lista_container'):
            self.lista_container.controls = [self.create_quick_calendar_list()]
            self.lista_container.update()

    def mudar_pagina(self, delta):
        self.pagina_atual += delta
        self.popular_listas_ajax()

    def atualizar_visual(self):
        self.init_ui()

    def create_summary_card(self, title, total, hours, publico, color_icon):
        return ft.Container(
            content=ft.Column([
                ft.Text(title, size=16, weight=ft.FontWeight.BOLD),
                ft.Row([
                    ft.Icon(ft.Icons.CALENDAR_MONTH, color=ft.Colors.ORANGE_400, size=20),
                    ft.Column([
                        ft.Text("Transmissões", size=10, color=ft.Colors.WHITE70),
                        ft.Text(f"{total}", size=14, weight=ft.FontWeight.BOLD),
                    ], spacing=-2),
                ], spacing=10),
                ft.Row([
                    ft.Icon(ft.Icons.TIMER, color=ft.Colors.GREEN_400, size=20),
                    ft.Column([
                        ft.Text("Horas em Live", size=10, color=ft.Colors.WHITE70),
                        ft.Text(f"{hours}", size=14, weight=ft.FontWeight.BOLD),
                    ], spacing=-2),
                ], spacing=10),
                ft.Row([
                    ft.Icon(ft.Icons.GROUPS, color=ft.Colors.PURPLE_400, size=20),
                    ft.Column([
                        ft.Text("Público", size=10, color=ft.Colors.WHITE70),
                        ft.Text(f"{publico}", size=14, weight=ft.FontWeight.BOLD),
                    ], spacing=-2),
                ], spacing=10),
            ], spacing=10),
            bgcolor=ft.Colors.WHITE10,
            padding=15,
            border_radius=15,
            expand=True,
            on_hover=self.set_hover,
            animate=ft.Animation(300, ft.AnimationCurve.DECELERATE),
        )

    def create_summary_column_controls(self, stats):
        return [
            ft.Text("📊 Resumo Público", size=22, weight=ft.FontWeight.W_600),
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.PEOPLE, size=40, color=ft.Colors.BLUE_400),
                    ft.Text(f"{stats['publico_total']}", size=34, weight=ft.FontWeight.BOLD),
                    ft.Text("Público Total Acumulado", size=14, color=ft.Colors.WHITE70),
                    ft.ProgressBar(value=0.7, color=ft.Colors.BLUE_400, bgcolor=ft.Colors.BLUE_900),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                bgcolor=ft.Colors.BLUE_GREY_900,
                padding=25,
                border_radius=25,
                on_hover=self.set_hover,
                animate=ft.Animation(300, ft.AnimationCurve.DECELERATE),
            ),
            
            ft.Row([
                self.create_summary_card("Resumo Mensal", stats['total_mensal'], stats['horas_mensal'], stats['publico_mensal'], ft.Colors.BLUE_400),
                self.create_summary_card("Resumo Semestral", stats['total_semestre'], stats['horas_semestre'], stats['publico_semestre'], ft.Colors.ORANGE_400),
            ], spacing=10),

            ft.Text("📆 Resumo Anual", size=20, weight=ft.FontWeight.W_600),
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.AUTO_GRAPH, color=ft.Colors.CYAN_400),
                        ft.Column([
                            ft.Text("Transmissões no Ano", size=12, color=ft.Colors.WHITE70),
                            ft.Text(f"{stats['total_ano']}", size=18, weight=ft.FontWeight.BOLD),
                        ]),
                    ], spacing=15),
                    ft.Row([
                        ft.Icon(ft.Icons.HISTORY_TOGGLE_OFF, color=ft.Colors.INDIGO_400),
                        ft.Column([
                            ft.Text("Total Horas (Ano)", size=12, color=ft.Colors.WHITE70),
                            ft.Text(f"{stats['horas_ano']}", size=18, weight=ft.FontWeight.BOLD),
                        ]),
                    ], spacing=15),
                    ft.Row([
                        ft.Icon(ft.Icons.ANALYTICS, color=ft.Colors.PINK_400),
                        ft.Column([
                            ft.Text("Público Total (Ano)", size=12, color=ft.Colors.WHITE70),
                            ft.Text(f"{stats['publico_ano']}", size=18, weight=ft.FontWeight.BOLD),
                        ]),
                    ], spacing=15),
                ], spacing=15),
                bgcolor=ft.Colors.WHITE10,
                padding=20,
                border_radius=20,
                on_hover=self.set_hover,
                animate=ft.Animation(300, ft.AnimationCurve.DECELERATE),
            )
        ]

    def atualizar(self):
        self.controller.carregar()
        self.init_ui()

    def did_mount(self):
        self.running_clock = True
        self.page.run_task(self.update_clock_task)

    def will_unmount(self):
        self.running_clock = False

    async def update_clock_task(self):
        while self.running_clock:
            agora = datetime.now()
            # Formata hora: 14:30:05
            self.lbl_relogio_hora.value = agora.strftime("%H:%M:%S")
            # Formata data: Quinta, 09 de Abril
            meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
            dias = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
            
            dia_sem = dias[agora.weekday()]
            mes_nome = meses[agora.month - 1]
            
            self.lbl_relogio_data.value = f"{dia_sem}, {agora.day:02d} de {mes_nome}"
            
            try:
                self.lbl_relogio_hora.update()
                self.lbl_relogio_data.update()
            except:
                pass
            
            await asyncio.sleep(1)

    def set_hover(self, e):
        # Se for um Container, o efeito deve ser nele. Se for GestureDetector, no seu content.
        target = e.control if isinstance(e.control, ft.Container) else getattr(e.control, "content", e.control)
        
        if not target: return
        
        is_hover = e.data == "true"
        target.scale = 1.05 if is_hover else 1.0
        
        if is_hover:
            if not hasattr(target, "_orig_border"):
                target._orig_border = target.border
            
            target.border = ft.border.all(2, ft.Colors.CYAN_400)
            target.shadow = ft.BoxShadow(
                blur_radius=30,
                color=ft.Colors.with_opacity(0.4, ft.Colors.CYAN_700),
                spread_radius=1
            )
        else:
            if hasattr(target, "_orig_border"):
                target.border = target._orig_border
            target.shadow = None
            
        target.update()

    def confirmar_exclusao(self, t):
        dlg = None
        def fechar_dialogo(e):
            dlg.open = False
            self.page.update()

        def deletar_item(e):
            self.controller.deletar(t.id)
            dlg.open = False
            self.page.update()
            self.atualizar()

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
