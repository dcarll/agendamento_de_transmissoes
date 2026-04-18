import flet as ft
from controllers.transmissao_controller import TransmissaoController
from views.dashboard_view import DashboardView
from views.calendario_view import CalendarioView
from views.historico_view import HistoricoView
from views.formulario_view import FormularioView
from views.relatorio_view import RelatorioView

class TransmissionApp:
    def __init__(self, page: ft.Page):
        self.page = page
        # Inicializa o controller com callback para notificar outros usuários/instâncias
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
        self.page.theme = ft.Theme(color_scheme_seed=ft.Colors.BLUE_700)

    def init_components(self):
        # Sidebar (Navigation Rail)
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
                ft.NavigationRailDestination(
                    icon=ft.Icons.DASHBOARD_OUTLINED,
                    selected_icon=ft.Icons.DASHBOARD,
                    label="Início",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.CALENDAR_MONTH_OUTLINED,
                    selected_icon=ft.Icons.CALENDAR_MONTH,
                    label="Calendário",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.HISTORY_OUTLINED,
                    selected_icon=ft.Icons.HISTORY,
                    label="Histórico",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.ADD_CIRCLE_OUTLINE,
                    selected_icon=ft.Icons.ADD_CIRCLE,
                    label="Novo",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.ASSESSMENT_OUTLINED,
                    selected_icon=ft.Icons.ASSESSMENT,
                    label="Relatório",
                ),
            ],
            on_change=lambda e: self.navegar(e.control.selected_index)
        )

        # Content Area
        self.content_area = ft.Container(
            expand=True,
            padding=30,
            animate=ft.Animation(500, ft.AnimationCurve.DECELERATE)
        )

        self.layout = ft.Row(
            [
                self.rail,
                ft.VerticalDivider(width=1, color="white10"),
                self.content_area,
            ],
            expand=True,
            spacing=0,
        )

    def navegar(self, index):
        self.rail.selected_index = index
        # Força o recarregamento dos dados antes de renderizar a view
        self.controller.transmissoes = self.controller.carregar()
        
        if index == 0:
            self.content_area.content = DashboardView(self.controller, on_edit=self.abrir_edicao)
        elif index == 1:
            self.content_area.content = CalendarioView(self.controller, on_edit=self.abrir_edicao)
        elif index == 2:
            self.content_area.content = HistoricoView(self.controller, on_edit=self.abrir_edicao)
        elif index == 3:
            self.content_area.content = FormularioView(self.controller, on_back=lambda: self.navegar(0))
        elif index == 4:
            self.content_area.content = RelatorioView(self.controller, on_back=lambda: self.navegar(0))
            
        self.page.update()

    def setup_sync(self):
        # Subscreve para mensagens em tempo real (PubSub entre sessões no mesmo servidor)
        self.page.pubsub.subscribe(self.on_broadcast)
        # Inicia o monitoramento periódico para instâncias em computadores diferentes
        self.page.run_task(self.auto_refresh_task)

    async def auto_refresh_task(self):
        import asyncio
        import json
        last_data_hash = ""
        while True:
            await asyncio.sleep(2.0) # Verifica a cada 2 segundos
            try:
                if self.rail.selected_index not in (3, 4) and not isinstance(self.content_area.content, FormularioView):
                    nuevas_transmissoes = self.controller.carregar()
                    
                    # Gera um hash simples ou string comparável do estado atual
                    # (Apenas para checar se algo mudou antes de rebuildar toda a UI)
                    current_data_hash = str(len(nuevas_transmissoes)) + str(max([t.id for t in nuevas_transmissoes] if nuevas_transmissoes else [0]))
                    
                    # Adicionalmente, podemos checar se algum status mudou
                    if nuevas_transmissoes:
                        status_summary = "".join([t.status[:1] for t in nuevas_transmissoes])
                        current_data_hash += status_summary

                    if current_data_hash != last_data_hash:
                        last_data_hash = current_data_hash
                        self.controller.transmissoes = nuevas_transmissoes
                        
                        if hasattr(self.content_area.content, "atualizar"):
                            self.content_area.content.atualizar()
                        else:
                            self.navegar(self.rail.selected_index)
            except:
                pass

    def notificar_mudanca(self):
        """Notifica todas as sessões conectadas ao mesmo servidor Flet."""
        try:
            self.page.pubsub.send_all("update_required")
        except:
            pass

    def on_broadcast(self, message):
        if message == "update_required":
            self.recarregar_interface()

    def recarregar_interface(self):
        try:
            # Se o usuário está na tela de "Novo" (índice 3) ou Editando (que usa FormularioView), 
            # não recarregamos para evitar que ele perca o que está digitando.
            if self.rail.selected_index in (3, 4) or isinstance(self.content_area.content, FormularioView):
                # Apenas atualizamos os dados no fundo, mas não resetamos a view
                self.controller.transmissoes = self.controller.carregar()
                return
            
            # Recarrega a view atual com os novos dados
            self.navegar(self.rail.selected_index)
        except Exception as e:
            print(f"Erro ao recarregar interface: {e}")

    def abrir_edicao(self, transmissao):
        # Captura o estado atual da view para restauração posterior
        view = self.content_area.content
        state = {
            "index": self.rail.selected_index,
            "pagina": getattr(view, "pagina_atual", 0),
            "busca": getattr(view.txt_busca, "value", "") if hasattr(view, "txt_busca") else "",
        }
        
        # Estado específico do Calendário
        if isinstance(view, CalendarioView):
            state.update({
                "status": view.dd_status.value,
                "periodo": view.dd_periodo.value,
                "tipo": view.dd_tipo.value,
                "modalidade": view.dd_modalidade.value,
                "ordenar": view.dd_ordenar.value,
                "view_mode": view.view_mode,
                "data_inicio": view.data_inicio_selecionada,
                "data_fim": view.data_fim_selecionada,
            })

        self.content_area.content = FormularioView(
            self.controller, 
            on_back=lambda: self.voltar_da_edicao(state), 
            transmissao_edit=transmissao
        )
        self.page.update()

    def voltar_da_edicao(self, state):
        # Retorna para a aba anterior
        self.navegar(state["index"])
        view = self.content_area.content
        
        # Restaura busca e página
        if hasattr(view, "txt_busca"):
            view.txt_busca.value = state["busca"]
        if hasattr(view, "pagina_atual"):
            view.pagina_atual = state["pagina"]
            
        # Restaura filtros específicos do Calendário
        if isinstance(view, CalendarioView):
            view.dd_status.value = state.get("status", "Todos")
            view.dd_periodo.value = state.get("periodo", "Todos")
            view.dd_tipo.value = state.get("tipo", "Todos")
            view.dd_modalidade.value = state.get("modalidade", "Todos")
            view.dd_ordenar.value = state.get("ordenar", "data_evento")
            view.view_mode = state.get("view_mode", "list")
            view.data_inicio_selecionada = state.get("data_inicio")
            view.data_fim_selecionada = state.get("data_fim")
            
            # Atualiza textos de data se necessário
            if view.data_inicio_selecionada:
                view.txt_inicio.value = view.data_inicio_selecionada.strftime('%d/%m/%Y')
            if view.data_fim_selecionada:
                view.txt_fim.value = view.data_fim_selecionada.strftime('%d/%m/%Y')
            
            if view.dd_periodo.value == "Personalizado":
                view.row_personalizado.visible = True

        # Re-inicializa a UI com os dados restaurados
        if hasattr(view, "init_ui"):
            view.init_ui()
            
        self.page.update()
