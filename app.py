import flet as ft
import os
import asyncio
from controllers.transmissao_controller import TransmissaoController
from views.dashboard_view import DashboardView
from views.calendario_view import CalendarioView
from views.historico_view import HistoricoView
from views.formulario_view import FormularioView
from views.relatorio_view import RelatorioView

class TransmissionApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.controller = TransmissaoController(on_change=self.notificar_mudanca)
        
        self.setup_page()
        self.init_components()
        self.page.add(self.layout)
        self.setup_sync()
        self.navegar(0)

    def setup_page(self):
        self.page.title = "Sistema de Transmissões DTI/LAB"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.padding = 0
        self.page.spacing = 0
        self.page.bgcolor = ft.Colors.BLACK
        self.page.window.min_width = 1000
        self.page.window.min_height = 700
        self.page.window.icon = "transmissoes.ico"
        self.page.icon = "transmissoes.ico"
        self.page.window.maximized = True
        self.page.theme = ft.Theme(color_scheme_seed=ft.Colors.BLUE_700)

    def init_components(self):
        # Sidebar Customizada com Design Premium
        self.nav_items_container = ft.Column(spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
        self.nav_destinations = [
            {"icon": ft.Icons.GRID_VIEW_ROUNDED, "label": "Início", "index": 0},
            {"icon": ft.Icons.CALENDAR_MONTH_ROUNDED, "label": "Calendário", "index": 1},
            {"icon": ft.Icons.HISTORY_ROUNDED, "label": "Histórico", "index": 2},
            {"icon": ft.Icons.ADD_BOX_ROUNDED, "label": "Novo", "index": 3},
            {"icon": ft.Icons.BAR_CHART_ROUNDED, "label": "Relatório", "index": 4},
        ]

        # Armazena os controles de item para atualização de estado
        self.nav_controls = []
        self._selected_index = 0

        def create_nav_item(dest):
            index = dest["index"]
            is_selected = index == self._selected_index
            
            # Indicador lateral (barra vertical)
            indicator = ft.Container(
                width=4,
                height=25,
                bgcolor=ft.Colors.CYAN_400 if is_selected else ft.Colors.TRANSPARENT,
                border_radius=2,
                animate=ft.Animation(300, ft.AnimationCurve.DECELERATE)
            )

            icon_color = ft.Colors.CYAN_400 if is_selected else ft.Colors.WHITE38
            text_color = ft.Colors.WHITE if is_selected else ft.Colors.WHITE38
            
            item = ft.Container(
                content=ft.Column([
                    ft.Icon(dest["icon"], color=icon_color, size=28, animate_size=ft.Animation(300, ft.AnimationCurve.DECELERATE)),
                    ft.Text(dest["label"], color=text_color, size=11, weight=ft.FontWeight.BOLD if is_selected else ft.FontWeight.W_400)
                ], spacing=5, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.padding.symmetric(vertical=15, horizontal=10),
                border_radius=15,
                width=80,
                # Efeito de glassmorphism no selecionado
                bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.CYAN_400) if is_selected else ft.Colors.TRANSPARENT,
                on_click=lambda _: self.navegar(index),
                on_hover=lambda e: self.on_nav_hover(e, index),
                animate=ft.Animation(300, ft.AnimationCurve.DECELERATE),
                data=index # Para identificar no hover
            )

            # Wrapper para incluir o indicador
            return ft.Stack([
                item,
                ft.Container(content=indicator, alignment=ft.Alignment(-1, 0), padding=ft.padding.only(left=2))
            ], width=80)

        # Atualiza os itens
        self.nav_items_container.controls = [create_nav_item(d) for d in self.nav_destinations]

        # Container principal da Sidebar
        self.sidebar = ft.Container(
            content=ft.Column([
                # Logo Section
                ft.Container(
                    content=ft.Stack([
                        ft.Container(
                            width=60, height=60,
                            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.CYAN_400),
                            border_radius=20,
                            rotate=ft.Rotate(0.2),
                        ),
                        ft.Container(
                            content=ft.Icon(ft.Icons.PODCASTS, size=35, color=ft.Colors.CYAN_400),
                            width=60, height=60,
                            alignment=ft.Alignment(0, 0)
                        )
                    ]),
                    padding=ft.padding.only(top=30, bottom=50),
                    alignment=ft.Alignment(0, 0)
                ),
                # Menu Items
                self.nav_items_container,
            ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            width=100,
            bgcolor="#0F1115", # Dark Background elegante
            border=ft.border.only(right=ft.BorderSide(1, ft.Colors.WHITE10)),
        )

        self.content_area = ft.Container(
            expand=True,
            padding=30,
            bgcolor="#13161B", # Background um pouco mais claro para a área de conteúdo
            animate=ft.Animation(400, ft.AnimationCurve.DECELERATE)
        )

        self.layout = ft.Row(
            [self.sidebar, self.content_area],
            expand=True, spacing=0,
        )

    # Propriedade para compatibilidade
    @property
    def rail(self):
        # Retorna um objeto que "finge" ser o rail para manter compatibilidade com o resto do código
        class RailProxy:
            def __init__(self, parent):
                self.parent = parent
            @property
            def selected_index(self):
                return self.parent._selected_index
            @selected_index.setter
            def selected_index(self, value):
                self.parent._selected_index = value
                self.parent.refresh_sidebar()
        return RailProxy(self)

    def on_nav_hover(self, e, index):
        if e.data == "true":
            if index != self._selected_index:
                e.control.bgcolor = ft.Colors.with_opacity(0.05, ft.Colors.WHITE)
        else:
            if index != self._selected_index:
                e.control.bgcolor = ft.Colors.TRANSPARENT
        e.control.update()

    def refresh_sidebar(self):
        # Recria os itens para refletir a seleção
        def create_nav_item(dest):
            index = dest["index"]
            is_selected = index == self._selected_index
            
            indicator = ft.Container(
                width=4,
                height=25,
                bgcolor=ft.Colors.CYAN_400 if is_selected else ft.Colors.TRANSPARENT,
                border_radius=2,
                animate=ft.Animation(300, ft.AnimationCurve.DECELERATE)
            )

            icon_color = ft.Colors.CYAN_400 if is_selected else ft.Colors.WHITE38
            text_color = ft.Colors.WHITE if is_selected else ft.Colors.WHITE38
            
            item = ft.Container(
                content=ft.Column([
                    ft.Icon(dest["icon"], color=icon_color, size=28, animate_size=ft.Animation(300, ft.AnimationCurve.DECELERATE)),
                    ft.Text(dest["label"], color=text_color, size=11, weight=ft.FontWeight.BOLD if is_selected else ft.FontWeight.W_400)
                ], spacing=5, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.padding.symmetric(vertical=15, horizontal=10),
                border_radius=15,
                width=80,
                bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.CYAN_400) if is_selected else ft.Colors.TRANSPARENT,
                on_click=lambda _: self.navegar(index),
                on_hover=lambda e: self.on_nav_hover(e, index),
                animate=ft.Animation(300, ft.AnimationCurve.DECELERATE),
                data=index
            )

            return ft.Stack([
                item,
                ft.Container(content=indicator, alignment=ft.Alignment(-1, 0), padding=ft.padding.only(left=2))
            ], width=80)

        self.nav_items_container.controls = [create_nav_item(d) for d in self.nav_destinations]
        self.sidebar.update()

    def _criar_view(self, index):
        """Cria a view para o índice dado. Usa dados já em memória."""
        if index == 0:
            return DashboardView(self.controller, on_edit=self.abrir_edicao, on_navigate=self.navegar)
        elif index == 1:
            return CalendarioView(self.controller, on_edit=self.abrir_edicao)
        elif index == 2:
            return HistoricoView(self.controller, on_edit=self.abrir_edicao)
        elif index == 3:
            return FormularioView(self.controller, on_back=lambda: self.navegar(0))
        elif index == 4:
            return RelatorioView(self.controller, on_back=lambda: self.navegar(0))

    def navegar(self, index):
        self.rail.selected_index = index
        
        # 1. Mostra um spinner de carregamento imediatamente
        # Isso libera a thread principal para o relógio continuar rodando
        self.content_area.content = ft.Container(
            content=ft.Column([
                ft.ProgressRing(width=40, height=40, stroke_width=3, color=ft.Colors.BLUE_400),
                ft.Text("Carregando...", size=14, color=ft.Colors.WHITE38),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
            expand=True,
            alignment=ft.Alignment(0, 0)
        )
        self.page.update()

        # 2. Constrói a view em background
        async def build_view():
            try:
                # O Flet permite criar widgets em threads separadas (são apenas objetos Python)
                new_view = await asyncio.to_thread(self._criar_view, index)
                self.content_area.content = new_view
                self.page.update()
            except Exception as e:
                print(f"Erro ao construir view: {e}")

        self.page.run_task(build_view)

    def setup_sync(self):
        self.page.pubsub.subscribe(self.on_broadcast)
        self.page.run_task(self.auto_refresh_task)

    async def auto_refresh_task(self):
        """Verifica mudanças no arquivo JSON a cada 5s em background (não bloqueia UI)."""
        import asyncio
        last_mtime = 0
        while True:
            await asyncio.sleep(5.0)
            try:
                filepath = self.controller.FILEPATH
                current_mtime = await asyncio.to_thread(os.path.getmtime, filepath)
                if current_mtime != last_mtime and last_mtime != 0:
                    last_mtime = current_mtime
                    # Outro usuário salvou - relê do disco em background
                    dados = await asyncio.to_thread(self.controller.db._carregar_arquivo)
                    self.controller.db._dados = dados
                    self.controller.transmissoes = self.controller.carregar()
                    if hasattr(self.content_area.content, "atualizar"):
                        self.content_area.content.atualizar()
                else:
                    last_mtime = current_mtime
            except:
                pass

    def notificar_mudanca(self):
        try:
            self.page.pubsub.send_all("update_required")
        except:
            pass

    def on_broadcast(self, message):
        if message == "update_required":
            self.recarregar_interface()

    def recarregar_interface(self):
        try:
            if self.rail.selected_index in (3, 4) or isinstance(self.content_area.content, FormularioView):
                return
            if hasattr(self.content_area.content, "atualizar"):
                self.content_area.content.atualizar()
                self.page.update()
            else:
                self.navegar(self.rail.selected_index)
        except Exception as e:
            print(f"Erro ao recarregar interface: {e}")

    def abrir_edicao(self, transmissao):
        self.content_area.content = FormularioView(
            self.controller,
            on_back=lambda: self.navegar(0),
            transmissao_edit=transmissao
        )
        self.page.update()
