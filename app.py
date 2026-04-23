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
        self.rail = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=100,
            min_extended_width=200,
            bgcolor="surface-variant",
            leading=ft.Container(
                content=ft.Icon(ft.Icons.PODCASTS, size=40, color="blue400"),
                padding=ft.padding.symmetric(vertical=20)
            ),
            group_alignment=-0.9,
            destinations=[
                ft.NavigationRailDestination(icon=ft.Icons.DASHBOARD_OUTLINED, selected_icon=ft.Icons.DASHBOARD, label="Início"),
                ft.NavigationRailDestination(icon=ft.Icons.CALENDAR_MONTH_OUTLINED, selected_icon=ft.Icons.CALENDAR_MONTH, label="Calendário"),
                ft.NavigationRailDestination(icon=ft.Icons.HISTORY_OUTLINED, selected_icon=ft.Icons.HISTORY, label="Histórico"),
                ft.NavigationRailDestination(icon=ft.Icons.ADD_CIRCLE_OUTLINE, selected_icon=ft.Icons.ADD_CIRCLE, label="Novo"),
                ft.NavigationRailDestination(icon=ft.Icons.ASSESSMENT_OUTLINED, selected_icon=ft.Icons.ASSESSMENT, label="Relatório"),
            ],
            on_change=lambda e: self.navegar(e.control.selected_index)
        )

        self.content_area = ft.Container(
            expand=True,
            padding=30,
            animate=ft.Animation(300, ft.AnimationCurve.DECELERATE)
        )

        self.layout = ft.Row(
            [self.rail, ft.VerticalDivider(width=1, color="white10"), self.content_area],
            expand=True, spacing=0,
        )

    def _criar_view(self, index):
        """Cria a view para o índice dado. Usa dados já em memória."""
        if index == 0:
            return DashboardView(self.controller, on_edit=self.abrir_edicao)
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
