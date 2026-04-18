import flet as ft
from controllers.transmissao_controller import TransmissaoController
from datetime import datetime, timedelta
from utils.helpers import normalize_date, format_date_br, formatar_data_completa_semana, parse_date, formatar_data_semana
from utils.dialog_helper import mostrar_detalhes_transmissao, abrir_menu_contexto

class CalendarioView(ft.Column):
    def __init__(self, controller: TransmissaoController, on_edit):
        super().__init__(expand=True, spacing=25, scroll=ft.ScrollMode.ADAPTIVE)
        self.controller = controller
        self.on_edit = on_edit
        self.pagina_atual = 0
        self.itens_por_página = 20
        self.view_mode = "list" # grid ou list
        
        # Componentes Fixos
        self.txt_busca = ft.TextField(
            hint_text="Pesquisar...",
            prefix_icon=ft.Icons.SEARCH,
            on_change=lambda _: self.reset_and_update(),
            width=250, height=45, text_size=13,
            content_padding=ft.padding.only(left=10, right=10),
            border_radius=10, bgcolor=ft.Colors.WHITE10
        )
        self.txt_count = ft.Text("0 eventos encontrados", color=ft.Colors.WHITE70)
        self.grid_container = ft.Column(expand=True)
        
        # Filtros (Persistentes)
        from utils.helpers import get_status_options
        self.dd_status = ft.Dropdown(
            label="Filtrar por Status",
            options=[ft.dropdown.Option("Todos")] + [ft.dropdown.Option(o) for o in get_status_options()],
            value="Todos", on_select=lambda _: self.reset_and_update(), width=200
        )
        self.dd_periodo = ft.Dropdown(
            label="Período",
            options=[ft.dropdown.Option(o) for o in ["Todos", "Dia", "Semana", "Mês", "Semestre", "Ano", "Personalizado"]],
            value="Todos", on_select=lambda _: self.on_periodo_change(), width=150
        )
        self.dd_tipo = ft.Dropdown(
            label="Tipo",
            options=[ft.dropdown.Option(o) for o in ["Todos", "StreamYard", "OBS", "YouTube", "Zoom", "Outro"]],
            value="Todos", on_select=lambda _: self.reset_and_update(), width=130
        )
        self.dd_modalidade = ft.Dropdown(
            label="Modalidade",
            options=[ft.dropdown.Option(o) for o in ["Todos", "Presencial", "Online", "Híbrido"]],
            value="Todos", on_select=lambda _: self.reset_and_update(), width=140
        )
        self.dd_ordenar = ft.Dropdown(
            label="Ordenar por",
            options=[
                ft.dropdown.Option("data_evento", "Data do Evento"),
                ft.dropdown.Option("nome", "Nome"),
                ft.dropdown.Option("data_criacao", "Data de Criação"),
            ],
            value="data_evento", on_select=lambda _: self.reset_and_update(), width=200
        )

        # Controles de Período Personalizado
        self.txt_inicio = ft.TextField(label="Início", value="--/--/----", read_only=True, on_click=lambda _: self.abrir_calendario("inicio"), width=120, text_size=12)
        self.txt_fim = ft.TextField(label="Fim", value="--/--/----", read_only=True, on_click=lambda _: self.abrir_calendario("fim"), width=120, text_size=12)
        self.data_inicio_selecionada = None
        self.data_fim_selecionada = None

        # Botão de Troca de Visualização
        self.btn_view_toggle = ft.IconButton(
            icon=ft.Icons.GRID_VIEW,
            tooltip="Exibir em Grade",
            on_click=lambda _: self.toggle_view_mode()
        )

        # Botão Exportar Excel
        self.btn_exportar_excel = ft.ElevatedButton(
            "Exportar Excel",
            icon=ft.Icons.FILE_DOWNLOAD,
            on_click=self.exportar_excel,
            style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.GREEN_700),
            height=40,
        )

        self.row_personalizado = ft.Row([
            self.txt_inicio, ft.Text("Até:", weight=ft.FontWeight.BOLD), self.txt_fim,
            ft.IconButton(ft.Icons.CHECK_CIRCLE, icon_color=ft.Colors.GREEN, on_click=lambda _: self.reset_and_update())
        ], visible=False, spacing=10)

        # MONTAGEM FIXA DA TELA
        self.controls = [
            ft.Row([
                ft.Column([
                    ft.Text("Calendário de Transmissões", size=28, weight=ft.FontWeight.BOLD),
                    self.txt_count,
                ]),
                ft.Column([
                    ft.Row([
                        self.txt_busca, 
                        ft.Column([
                            self.dd_periodo,
                            self.row_personalizado
                        ], spacing=5), 
                        self.dd_status, self.dd_tipo, self.dd_modalidade, self.dd_ordenar,
                        self.btn_view_toggle, self.btn_exportar_excel
                    ], spacing=10, wrap=True),
                ], horizontal_alignment=ft.CrossAxisAlignment.START, expand=True)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Divider(height=10, color=ft.Colors.WHITE10),
            self.grid_container
        ]
        self.init_ui()

    def init_ui(self):
        hoje_dt = datetime.now()
        hoje_str = hoje_dt.strftime("%Y-%m-%d")
        status_filtro = self.dd_status.value
        periodo_filtro = self.dd_periodo.value
        tipo_filtro = self.dd_tipo.value
        modalidade_filtro = self.dd_modalidade.value
        ordem = self.dd_ordenar.value
        
        # Container para o grid dinâmico (não perde foco na busca)
        if not hasattr(self, 'grid_container'):
            self.grid_container = ft.Column(expand=True)

        # 1. Filtra as transmissões
        lista_filtrada = []
        termo = self.txt_busca.value.lower() if self.txt_busca.value else ""
        
        for t in self.controller.transmissoes:
            dt_t = normalize_date(t.data)
            
            # Filtro de Busca (Texto)
            if termo:
                if (termo not in t.evento.lower() and 
                    termo not in t.responsavel.lower() and 
                    termo not in (t.local or "").lower()):
                    continue

            # REGRAS DE EXIBIÇÃO:
            from utils.helpers import get_status_info, check_status_match
            
            # Exibir por padrão a partir da data atual
            dt_t = normalize_date(t.data)
            if periodo_filtro == "Todos":
                # Se o filtro de status for "Finalizado" ou "Cancelado" OU houver um termo de busca, permitimos ver itens passados
                # Caso contrário, mantemos apenas eventos futuros (padrão do calendário)
                if not termo and status_filtro not in ["Finalizado (Fase 5)", "Cancelado"] and dt_t < hoje_str: 
                    continue
            
            if not check_status_match(t.status, status_filtro): continue
            if tipo_filtro != "Todos" and t.tipo_transmissao != tipo_filtro: continue
            if modalidade_filtro != "Todos" and t.modalidade != modalidade_filtro: continue
                
            if periodo_filtro == "Personalizado":
                if self.data_inicio_selecionada and self.data_fim_selecionada:
                    t_datetime = parse_date(t.data)
                    if t_datetime:
                        t_date = t_datetime.date()
                        if not (self.data_inicio_selecionada.date() <= t_date <= self.data_fim_selecionada.date()):
                            continue
                else:
                    if dt_t < hoje_str: continue
            elif periodo_filtro != "Todos":
                t_datetime = parse_date(t.data)
                if not t_datetime: continue
                
                # Definições de Período mais intuitivas
                if periodo_filtro == "Dia":
                    if dt_t != hoje_str: continue
                elif periodo_filtro == "Semana":
                    # Pega o início da semana (segunda) e fim (domingo)
                    segunda = hoje_dt - timedelta(days=hoje_dt.weekday())
                    domingo = segunda + timedelta(days=6)
                    if not (segunda.date() <= t_datetime.date() <= domingo.date()): continue
                elif periodo_filtro == "Mês":
                    if t_datetime.month != hoje_dt.month or t_datetime.year != hoje_dt.year: continue
                elif periodo_filtro == "Semestre":
                    semestre_atual = 1 if hoje_dt.month <= 6 else 2
                    t_semestre = 1 if t_datetime.month <= 6 else 2
                    if semestre_atual != t_semestre or t_datetime.year != hoje_dt.year: continue
                elif periodo_filtro == "Ano":
                    if t_datetime.year != hoje_dt.year: continue
            
            lista_filtrada.append(t)
        
        # 2. Ordenação
        if ordem == "nome":
            lista_filtrada.sort(key=lambda x: x.evento.lower())
        elif ordem == "data_criacao":
            # Assume que os itens que não tem data_criacao ainda (antigos) ficam por último
            lista_filtrada.sort(key=lambda x: getattr(x, 'data_criacao', ''), reverse=True)
        else: # data_evento (padrão)
            lista_filtrada.sort(key=lambda x: (normalize_date(x.data), x.horario_inicio))
        total_paginas = (len(lista_filtrada) + self.itens_por_página - 1) // self.itens_por_página
        
        # 3. Paginação (Slicing)
        inicio = self.pagina_atual * self.itens_por_página
        fim = inicio + self.itens_por_página
        itens_pagina = lista_filtrada[inicio:fim]

        self.txt_count.value = f"{len(lista_filtrada)} eventos encontrados"
        self.popular_grid(itens_pagina, total_paginas)

    def popular_grid(self, itens_pagina, total_paginas):
        grid_controls = []
        if not itens_pagina:
            grid_controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.EVENT_BUSY, size=50, color=ft.Colors.WHITE24),
                        ft.Text("Nenhuma transmissão encontrada.", size=16, color=ft.Colors.WHITE38),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.Alignment.CENTER, padding=50
                )
            )
        else:
            if self.view_mode == "grid":
                # Layout em Grade (Ajustado para 5 por linha)
                grid = ft.GridView(
                    expand=True,
                    max_extent=400, # Cards maiores
                    runs_count=5,   # Máximo de 5 cards por linha
                    spacing=20,
                    run_spacing=20,
                    child_aspect_ratio=0.85,
                )
                for t in itens_pagina:
                    grid.controls.append(self.create_event_card(t))
                grid_controls.append(grid)
            else:
                # Layout em Lista
                lista = ft.Column(spacing=10, expand=True, scroll=ft.ScrollMode.AUTO)
                for t in itens_pagina:
                    lista.controls.append(self.create_event_row(t))
                grid_controls.append(lista)

        # Paginação
        paginacao = ft.Row([
            ft.IconButton(ft.Icons.ARROW_BACK_IOS_NEW, on_click=lambda _: self.mudar_pagina(-1), disabled=self.pagina_atual == 0),
            ft.Text(f"Página {self.pagina_atual + 1} de {max(1, total_paginas)}", size=16, weight=ft.FontWeight.BOLD),
            ft.IconButton(ft.Icons.ARROW_FORWARD_IOS, on_click=lambda _: self.mudar_pagina(1), disabled=self.pagina_atual >= total_paginas - 1),
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=20)
        
        grid_controls.append(ft.Container(height=20))
        grid_controls.append(paginacao)
        
        self.grid_container.controls = grid_controls
        try:
            if self.page and self.grid_container.page:
                self.grid_container.update()
                self.txt_count.update()
        except:
            pass

    def get_status_color(self, status):
        from utils.helpers import get_status_info
        return get_status_info(status)["color"]

    def create_event_row(self, t):
        from utils.helpers import get_status_info
        status_info = get_status_info(t.status)
        color_status = status_info["color"]
        
        # Gradiente sutil baseado na cor do status
        gradient = ft.LinearGradient(
            begin=ft.Alignment(-1, 0), # center_left
            end=ft.Alignment(1, 0),    # center_right
            colors=[ft.Colors.with_opacity(0.15, color_status), ft.Colors.with_opacity(0.05, ft.Colors.BLACK)]
        )
        
        return ft.GestureDetector(
            mouse_cursor=ft.MouseCursor.CLICK,
            on_tap=lambda _, item=t: mostrar_detalhes_transmissao(self.page, item),
            on_double_tap=lambda _, item=t: self.on_edit(item),
            on_secondary_tap=lambda _, item=t: abrir_menu_contexto(self.page, item, self.controller, self.on_edit, self.confirmar_exclusao, self.atualizar),
            on_hover=self.set_hover,
            content=ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Text(formatar_data_semana(t.data), weight=ft.FontWeight.BOLD, size=14, color=ft.Colors.BLACK),
                        bgcolor=color_status, padding=10, border_radius=10, width=120, alignment=ft.Alignment.CENTER
                    ),
                    ft.Text(f"{t.horario_inicio}\n   às \n{t.horario_fim}", weight=ft.FontWeight.BOLD, size=14, width=130),
                    ft.Column([
                        ft.Text(t.evento, size=18, weight=ft.FontWeight.BOLD),
                        ft.Text(f"{t.responsavel} | {t.local}", size=14, color=ft.Colors.WHITE70),
                    ], expand=True, spacing=2),
                    # Coluna de Status com Melhor Contraste
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Container(
                                    bgcolor=color_status, 
                                    width=12, 
                                    height=12, 
                                    border_radius=6,
                                    border=ft.border.all(1, ft.Colors.BLACK) # Contorno na bolinha
                                ),
                                ft.Text(
                                    status_info["label"], 
                                    size=14, 
                                    # Cor contrastante: se o status for muito claro, usa branco ou preto
                                    color=color_status, 
                                    weight=ft.FontWeight.BOLD,
                                ),
                            ], spacing=8),
                            ft.Text(
                                status_info["phase"].upper() if status_info["phase"] else "", 
                                size=10, 
                                italic=False, 
                                weight=ft.FontWeight.W_300,
                                color=ft.Colors.WHITE60
                            )
                        ], spacing=2),
                        width=160
                    ),
                    ft.Text(t.tipo_transmissao, size=11, color=ft.Colors.WHITE38, width=80),
                    ft.Row([
                        ft.IconButton(ft.Icons.INFO_OUTLINE, icon_size=20, icon_color=ft.Colors.CYAN_200, on_click=lambda _, item=t: mostrar_detalhes_transmissao(self.page, item), tooltip="Ver Detalhes"),
                        ft.IconButton(ft.Icons.EDIT_NOTE, icon_size=20, icon_color=ft.Colors.BLUE_200, on_click=lambda _: self.on_edit(t), tooltip="Editar"),
                        ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_size=20, icon_color=ft.Colors.RED_300, on_click=lambda _, item=t: self.confirmar_exclusao(item), tooltip="Excluir")
                    ], spacing=0)
                ], spacing=20),
                gradient=gradient,
                padding=15,
                border_radius=12,
                border=ft.border.all(1, ft.Colors.with_opacity(0.1, color_status)),
                animate=ft.Animation(300, ft.AnimationCurve.DECELERATE),
                tooltip="Clique: Ver Detalhes / Clique Duplo: Editar / Direito: Menu",
            )
        )

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

    def reset_and_update(self):
        self.pagina_atual = 0
        self.init_ui()
        try:
            if self.page and self.grid_container.page:
                self.grid_container.update()
                self.txt_count.update()
        except:
            pass

    def atualizar(self):
        self.init_ui()

    def mudar_pagina(self, delta):
        self.pagina_atual += delta
        self.init_ui()
        try:
            if self.page:
                self.update()
        except:
            pass

    def toggle_view_mode(self):
        if self.view_mode == "grid":
            self.view_mode = "list"
            self.btn_view_toggle.icon = ft.Icons.GRID_VIEW
            self.btn_view_toggle.tooltip = "Exibir em Grade"
        else:
            self.view_mode = "grid"
            self.btn_view_toggle.icon = ft.Icons.VIEW_LIST
            self.btn_view_toggle.tooltip = "Exibir em Lista"
        
        try:
            if self.btn_view_toggle.page:
                self.btn_view_toggle.update()
            self.init_ui()
            if self.page:
                self.update()
        except:
            pass

    def on_periodo_change(self):
        is_p = self.dd_periodo.value == "Personalizado"
        self.row_personalizado.visible = is_p
        if not is_p:
            self.data_inicio_selecionada = None
            self.data_fim_selecionada = None
            self.txt_inicio.value = "--/--/----"
            self.txt_fim.value = "--/--/----"
        else:
            # Mostra imediatamente o seletor de data para o início
            self.abrir_calendario("inicio")
            
        self.row_personalizado.update()
        self.reset_and_update()

    def abrir_calendario(self, tipo):
        # Valor inicial: data já selecionada ou hoje
        data_inicial = None
        if tipo == "inicio" and self.data_inicio_selecionada:
            data_inicial = self.data_inicio_selecionada
        elif tipo == "fim" and self.data_fim_selecionada:
            data_inicial = self.data_fim_selecionada
        else:
            data_inicial = datetime.now()

        def on_change(e):
            val = e.control.value # O Flet preenche isso no DatePicker
            if val:
                if tipo == "inicio":
                    self.data_inicio_selecionada = val
                    self.txt_inicio.value = val.strftime('%d/%m/%Y')
                    self.txt_inicio.update()
                else:
                    self.data_fim_selecionada = val
                    self.txt_fim.value = val.strftime('%d/%m/%Y')
                    self.txt_fim.update()
                
                # Se as duas datas já foram escolhidas, aplica o filtro automaticamente
                if self.data_inicio_selecionada and not self.data_fim_selecionada:
                    # Se escolheu o início, já abre o fim automaticamente para ser rápido
                    self.abrir_calendario("fim")
                elif self.data_inicio_selecionada and self.data_fim_selecionada:
                    self.reset_and_update()

        dp = ft.DatePicker(
            on_change=on_change,
            value=data_inicial,
            first_date=datetime(2020, 1, 1),
            last_date=datetime(2030, 12, 31),
            confirm_text="Confirmar",
            cancel_text="Cancelar",
            help_text="Selecione a data",
        )
        self.page.overlay.append(dp)
        self.page.update()
        dp.open = True
        self.page.update()

    def create_event_card(self, t):
        from utils.helpers import get_status_info
        status_info = get_status_info(t.status)
        color_status = status_info["color"]
        
        # Gradiente sutil baseado na cor do status
        gradient = ft.LinearGradient(
            begin=ft.Alignment(-1, -1), # top_left
            end=ft.Alignment(1, 1),     # bottom_right
            colors=[ft.Colors.with_opacity(0.2, color_status), ft.Colors.with_opacity(0.05, ft.Colors.BLACK)]
        )
        
        return ft.GestureDetector(
            mouse_cursor=ft.MouseCursor.CLICK,
            on_tap=lambda _, item=t: mostrar_detalhes_transmissao(self.page, item),
            on_double_tap=lambda _, item=t: self.on_edit(item),
            on_secondary_tap=lambda _, item=t: abrir_menu_contexto(self.page, item, self.controller, self.on_edit, self.confirmar_exclusao, self.atualizar),
            on_hover=self.set_hover,
            content=ft.Container(
                content=ft.Column([
                    # Cabeçalho do Card
                    ft.Row([
                        ft.Container(
                            content=ft.Text(formatar_data_completa_semana(t.data), weight=ft.FontWeight.BOLD, size=13, color=ft.Colors.BLACK),
                            bgcolor=color_status,
                            padding=ft.padding.symmetric(horizontal=10, vertical=5),
                            border_radius=7
                        ),
                        ft.Text(f"{t.horario_inicio} às {t.horario_fim}", weight=ft.FontWeight.BOLD, size=14),
                        ft.Container(expand=True),
                        ft.PopupMenuButton(
                            icon=ft.Icons.MORE_VERT,
                            icon_size=24,
                            items=[
                                ft.PopupMenuItem(
                                    content=ft.Row([ft.Icon(ft.Icons.INFO_OUTLINE, size=24), ft.Text("Detalhes", size=16)]),
                                    on_click=lambda _, item=t: mostrar_detalhes_transmissao(self.page, item)
                                ),
                                ft.PopupMenuItem(
                                    content=ft.Row([ft.Icon(ft.Icons.EDIT, size=24), ft.Text("Editar", size=16)]),
                                    on_click=lambda _: self.on_edit(t)
                                ),
                                ft.PopupMenuItem(
                                    content=ft.Row([ft.Icon(ft.Icons.DELETE, size=24), ft.Text("Excluir", size=16)]),
                                    on_click=lambda _, item=t: self.confirmar_exclusao(item)
                                ),
                            ],
                        )
                    ], spacing=10),
                    
                    ft.Text(t.evento, size=22, weight=ft.FontWeight.BOLD, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                    
                    ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.PERSON_OUTLINE, size=18, color=ft.Colors.WHITE38),
                            ft.Text(t.responsavel, size=16, color=ft.Colors.WHITE70, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        ], spacing=8),
                        ft.Row([
                            ft.Icon(ft.Icons.LOCATION_ON_OUTLINED, size=18, color=ft.Colors.WHITE38),
                            ft.Text(t.local, size=16, color=ft.Colors.WHITE38, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        ], spacing=8),
                    ], spacing=5, expand=True),
                    
                    ft.Divider(height=10, color=ft.Colors.with_opacity(0.1, color_status)),
                    
                    ft.Row([
                        ft.Container(bgcolor=color_status, width=12, height=12, border_radius=6),
                        ft.Text(status_info["label"], size=15, weight=ft.FontWeight.W_600, color=color_status),
                        ft.Container(expand=True),
                        ft.Text(t.tipo_transmissao, size=13, color=ft.Colors.WHITE38)
                    ], spacing=8)
                ], spacing=12),
                gradient=gradient,
                padding=20,
                border_radius=15,
                border=ft.border.all(1, ft.Colors.with_opacity(0.2, color_status)),
                animate=ft.Animation(300, ft.AnimationCurve.DECELERATE),
                tooltip=f"{t.evento}\nClique para detalhes",
            )
        )

    def confirmar_exclusao(self, t):
        dlg = None
        
        def fechar_dialogo(e):
            dlg.open = False
            self.page.update()

        def deletar_item(e):
            self.controller.deletar(t.id)
            dlg.open = False
            self.page.update()
            self.reset_and_update()

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
        import os

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)

        path = filedialog.asksaveasfilename(
            title="Salvar Calendário como...",
            defaultextension=".xlsx",
            initialfile="calendario_transmissoes.xlsx",
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
            ws.title = "Calendário de Transmissões"

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

            # Aplica os mesmos filtros da tela
            from utils.helpers import get_status_info, check_status_match, format_date_br
            hoje_dt = datetime.now()
            hoje_str = hoje_dt.strftime("%Y-%m-%d")
            status_filtro = self.dd_status.value
            periodo_filtro = self.dd_periodo.value
            tipo_filtro = self.dd_tipo.value
            modalidade_filtro = self.dd_modalidade.value
            ordem = self.dd_ordenar.value
            termo = self.txt_busca.value.lower() if self.txt_busca.value else ""

            lista_filtrada = []
            for t in self.controller.transmissoes:
                dt_t = normalize_date(t.data)
                if termo:
                    if (termo not in t.evento.lower() and
                        termo not in t.responsavel.lower() and
                        termo not in (t.local or "").lower()):
                        continue
                if not check_status_match(t.status, status_filtro): continue
                if tipo_filtro != "Todos" and t.tipo_transmissao != tipo_filtro: continue
                if modalidade_filtro != "Todos" and t.modalidade != modalidade_filtro: continue

                if periodo_filtro == "Personalizado":
                    if self.data_inicio_selecionada and self.data_fim_selecionada:
                        t_datetime = parse_date(t.data)
                        if t_datetime:
                            t_date = t_datetime.date()
                            if not (self.data_inicio_selecionada.date() <= t_date <= self.data_fim_selecionada.date()):
                                continue
                    else:
                        if dt_t < hoje_str: continue
                elif periodo_filtro != "Todos":
                    t_datetime = parse_date(t.data)
                    if not t_datetime: continue
                    if periodo_filtro == "Dia":
                        if dt_t != hoje_str: continue
                    elif periodo_filtro == "Semana":
                        segunda = hoje_dt - timedelta(days=hoje_dt.weekday())
                        domingo = segunda + timedelta(days=6)
                        if not (segunda.date() <= t_datetime.date() <= domingo.date()): continue
                    elif periodo_filtro == "Mês":
                        if t_datetime.month != hoje_dt.month or t_datetime.year != hoje_dt.year: continue
                    elif periodo_filtro == "Semestre":
                        semestre_atual = 1 if hoje_dt.month <= 6 else 2
                        t_semestre = 1 if t_datetime.month <= 6 else 2
                        if semestre_atual != t_semestre or t_datetime.year != hoje_dt.year: continue
                    elif periodo_filtro == "Ano":
                        if t_datetime.year != hoje_dt.year: continue

                lista_filtrada.append(t)

            # Ordenar
            if ordem == "nome":
                lista_filtrada.sort(key=lambda x: x.evento.lower())
            elif ordem == "data_criacao":
                lista_filtrada.sort(key=lambda x: getattr(x, 'data_criacao', ''), reverse=True)
            else:
                lista_filtrada.sort(key=lambda x: (normalize_date(x.data), x.horario_inicio))

            row_num = 2
            for t in lista_filtrada:
                status_info = get_status_info(t.status)
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
                ft.Text(f"✅ Calendário salvo como {os.path.basename(caminho)}"),
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
