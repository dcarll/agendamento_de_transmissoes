from datetime import datetime
import flet as ft
import asyncio
from models.transmissao_model import Transmissao
from utils.helpers import get_status_info, format_date_br, get_status_options, mascarar_hora, normalize_date
from utils.capa_helper import abrir_gerador_capa

def abrir_menu_contexto(page: ft.Page, t: Transmissao, controller, on_edit, on_delete, on_update):
    def mudar_status(novo_status):
        t.status = novo_status
        controller.atualizar(t)
        dlg.open = False
        page.update()
        if on_update:
            on_update()

    def acao_editar(e):
        dlg.open = False
        page.update()
        if on_edit:
            on_edit(t)

    def acao_excluir(e):
        dlg.open = False
        page.update()
        if on_delete:
            on_delete(t)

    def acao_detalhes(e):
        dlg.open = False
        page.update()
        mostrar_detalhes_transmissao(page, t, controller, on_update)

    # Opções principais
    opcoes_principais = [
        ft.TextButton(
            content=ft.Row([ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.CYAN_200), ft.Text("Ver Detalhes", color=ft.Colors.WHITE)], spacing=10),
            on_click=acao_detalhes,
            style=ft.ButtonStyle(padding=15, shape=ft.RoundedRectangleBorder(radius=10))
        ),
        ft.TextButton(
            content=ft.Row([ft.Icon(ft.Icons.EDIT_OUTLINED, color=ft.Colors.BLUE_200), ft.Text("Editar Transmissão", color=ft.Colors.WHITE)], spacing=10),
            on_click=acao_editar,
            style=ft.ButtonStyle(padding=15, shape=ft.RoundedRectangleBorder(radius=10))
        ),
        ft.TextButton(
            content=ft.Row([ft.Icon(ft.Icons.DELETE_FOREVER_OUTLINED, color=ft.Colors.RED_400), ft.Text("Excluir Transmissão", color=ft.Colors.WHITE)], spacing=10),
            on_click=acao_excluir,
            style=ft.ButtonStyle(padding=15, shape=ft.RoundedRectangleBorder(radius=10))
        ),
    ]

    botoes_status = []
    for status in get_status_options():
        info = get_status_info(status)
        botoes_status.append(
            ft.TextButton(
                content=ft.Row([ft.Icon(info["icon"], color=info["color"], size=18), ft.Text(status, color=ft.Colors.WHITE70, size=13)], spacing=10),
                on_click=lambda e, s=status: mudar_status(s),
                style=ft.ButtonStyle(padding=10, shape=ft.RoundedRectangleBorder(radius=8))
            )
        )

    dlg = ft.AlertDialog(
        title=ft.Row([ft.Icon(ft.Icons.MENU), ft.Text("Ações")]),
        content=ft.Container(
            content=ft.Column([
                ft.Column(opcoes_principais, spacing=2),
                ft.Divider(height=20, color=ft.Colors.WHITE10),
                ft.Text("Mudar Status para:", size=12, color=ft.Colors.WHITE38, italic=True),
                ft.Column(botoes_status, spacing=1),
            ], tight=True, scroll=ft.ScrollMode.ADAPTIVE),
            width=300
        ),
        actions=[ft.TextButton("Fechar", on_click=lambda e: fechar_dialogo(e, dlg))],
        actions_alignment=ft.MainAxisAlignment.END,
        shape=ft.RoundedRectangleBorder(radius=20),
        bgcolor=ft.Colors.GREY_900,
    )

    def fechar_dialogo(e, d):
        d.open = False; page.update()

    page.overlay.append(dlg); dlg.open = True; page.update()

def mostrar_detalhes_transmissao(page: ft.Page, t: Transmissao, controller=None, on_update=None):
    status_info = get_status_info(t.status)
    color_status = status_info["color"]
    fields = {}

    def on_field_change(e):
        btn_salvar.visible = True; page.update()

    def create_dropdown_row(label, value, options_list, icon):
        # Garante que o valor atual esteja nas opções, se não, adiciona (ou lida como "Outro")
        options = [ft.dropdown.Option(s) for s in options_list]
        if value and value not in options_list:
            options.append(ft.dropdown.Option(value))
        
        dd = ft.Dropdown(
            value=value, 
            options=options, 
            border=ft.InputBorder.NONE, 
            text_size=15, 
            color=ft.Colors.WHITE, 
            dense=True, 
            on_select=on_field_change, 
            content_padding=0,
            expand=True
        )
        fields[label] = dd
        return ft.Container(
            content=ft.Row([
                ft.Icon(icon, size=20, color=ft.Colors.WHITE38), 
                ft.Column([
                    ft.Text(label, size=11, color=ft.Colors.WHITE38, weight=ft.FontWeight.W_300), 
                    dd
                ], spacing=0, expand=True)
            ], spacing=15), 
            padding=ft.padding.symmetric(horizontal=15, vertical=8), 
            bgcolor=ft.Colors.WHITE10, 
            border_radius=10
        )

    def create_date_row(label, value, icon):
        def abrir_calendario(e):
            def on_change_date(e):
                val = e.control.value
                if val:
                    field.value = val.strftime("%d/%m/%Y")
                    on_field_change(e)
                    page.update()
            
            from utils.helpers import parse_date
            dt_inicial = parse_date(field.value) or datetime.now()
            
            dp = ft.DatePicker(
                on_change=on_change_date,
                value=dt_inicial,
                confirm_text="Confirmar",
                cancel_text="Cancelar",
                help_text="Selecione a data"
            )
            page.overlay.append(dp)
            page.update()
            dp.open = True
            page.update()

        val = value if value else ""
        field = ft.TextField(
            value=val, 
            read_only=True, 
            on_click=abrir_calendario, 
            border=ft.InputBorder.NONE, 
            text_size=15, 
            color=ft.Colors.WHITE, 
            dense=True, 
            content_padding=0
        )
        fields[label] = field
        return ft.Container(
            content=ft.Row([
                ft.Icon(icon, size=20, color=ft.Colors.WHITE38), 
                ft.Column([
                    ft.Text(label, size=11, color=ft.Colors.WHITE38, weight=ft.FontWeight.W_300), 
                    field
                ], spacing=0, expand=True)
            ], spacing=15), 
            padding=ft.padding.symmetric(horizontal=15, vertical=8), 
            bgcolor=ft.Colors.WHITE10, 
            border_radius=10
        )

    def create_detail_row(label, value, icon, is_link=False):
        val = value if value else ""
        
        def on_change(e):
            if label in ["Início", "Fim", "Início Real", "Fim Real"]:
                mascarar_hora(e)
            on_field_change(e)

        field = ft.TextField(
            value=val, 
            read_only=False, 
            border=ft.InputBorder.NONE, 
            text_size=14 if is_link else 15, 
            color=ft.Colors.BLUE_300 if is_link else ft.Colors.WHITE, 
            dense=True, 
            content_padding=ft.padding.only(top=8, bottom=8) if is_link else 0, 
            on_change=on_change,
            multiline=is_link,
            max_lines=3 if is_link else 1,
        )
        fields[label] = field
        
        row_controls = [
            ft.Icon(icon, size=20, color=ft.Colors.WHITE38), 
            ft.Column([
                ft.Text(label, size=11, color=ft.Colors.WHITE38, weight=ft.FontWeight.W_300), 
                field
            ], spacing=0, expand=True, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
        ]

        # Adiciona botões de ação para links
        if is_link:
            def copy_link(e):
                import subprocess
                val = field.value
                if val:
                    try:
                        # Usa clip.exe nativo do Windows para copiar
                        process = subprocess.Popen(['clip'], stdin=subprocess.PIPE)
                        process.communicate(val.encode('utf-8'))
                        page.snack_bar = ft.SnackBar(
                            ft.Text("✓ Link copiado!"), 
                            bgcolor=ft.Colors.GREEN_700
                        )
                    except Exception as ex:
                        page.snack_bar = ft.SnackBar(
                            ft.Text(f"Erro ao copiar: {ex}"), 
                            bgcolor=ft.Colors.RED_700
                        )
                else:
                    page.snack_bar = ft.SnackBar(
                        ft.Text("Campo vazio!"), 
                        bgcolor=ft.Colors.ORANGE_700
                    )
                page.snack_bar.open = True
                page.update()

            def open_link(e):
                import webbrowser
                url = field.value
                if url:
                    if not url.startswith(("http://", "https://", "mailto:", "tel:")):
                        url = "https://" + url
                    webbrowser.open(url)

            row_controls.append(
                ft.Row([
                    ft.IconButton(
                        icon=ft.Icons.COPY_ALL_ROUNDED, 
                        icon_size=22, 
                        icon_color=ft.Colors.BLUE_400, 
                        tooltip="Copiar Link", 
                        on_click=copy_link,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.OPEN_IN_NEW_ROUNDED, 
                        icon_size=22, 
                        icon_color=ft.Colors.GREEN_400, 
                        tooltip="Abrir no Navegador", 
                        on_click=open_link,
                    ),
                ], spacing=0)
            )

        return ft.Container(
            content=ft.Row(row_controls, spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER), 
            padding=ft.padding.symmetric(horizontal=15, vertical=5 if is_link else 8), 
            bgcolor=ft.Colors.WHITE10, 
            border_radius=10,
            animate=ft.Animation(300, ft.AnimationCurve.DECELERATE)
        )

    header = ft.Container(
        content=ft.Column([
            ft.Row([ft.Row([ft.Icon(ft.Icons.INFO_OUTLINE, color=color_status, size=24), ft.Text("Detalhes da Transmissão", size=14, color=ft.Colors.WHITE70)], spacing=10), ft.Container(content=ft.Text(status_info["label"], size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK), bgcolor=color_status, padding=ft.padding.symmetric(horizontal=12, vertical=5), border_radius=8)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.TextField(value=t.evento, text_size=24, text_style=ft.TextStyle(weight=ft.FontWeight.BOLD), text_align=ft.TextAlign.CENTER, border=ft.InputBorder.NONE, multiline=True, on_change=on_field_change, content_padding=0, expand=True),
            ft.Divider(height=1, color=ft.Colors.WHITE10)
        ], spacing=10), padding=ft.padding.only(bottom=10)
    )

    # Seção de Links Adicionais
    col_links_extras = ft.Column(spacing=10)
    def render_links_extras():
        col_links_extras.controls = []
        if hasattr(t, 'links_adicionais') and t.links_adicionais:
            for i, link in enumerate(t.links_adicionais):
                label = link.get("label", "Link")
                url = link.get("url", "")
                col_links_extras.controls.append(create_detail_row(f"Extra_{i}_{label}", url, ft.Icons.LINK, is_link=True))
    render_links_extras()

    details_grid = ft.Column([
        ft.Row([
            ft.Column([create_date_row("Data", format_date_br(t.data), ft.Icons.CALENDAR_TODAY)], expand=1),
            ft.Column([create_detail_row("Início", t.horario_inicio, ft.Icons.ACCESS_TIME)], expand=1),
            ft.Column([create_detail_row("Fim", t.horario_fim, ft.Icons.ACCESS_TIME_FILLED)], expand=1),
        ], spacing=10),
        ft.Row([ft.Column([create_detail_row("Responsável", t.responsavel, ft.Icons.PERSON)], expand=1), ft.Column([create_detail_row("Local", t.local, ft.Icons.LOCATION_ON)], expand=1)], spacing=10),
        ft.Row([
            ft.Column([create_dropdown_row("Tipo", t.tipo_transmissao, ["StreamYard+Youtube", "OBS+YOUTUBE", "ZOOM+YOUTUBE", "OBS+YOUTUBE+STREAMYARD", "GRAVAÇÃO", "YouTube", "StreamYard", "Zoom"], ft.Icons.LIVE_TV)], expand=1), 
            ft.Column([create_dropdown_row("Modalidade", t.modalidade, ["Presencial", "Online", "Híbrido"], ft.Icons.CHAIR)], expand=1)
        ], spacing=10),
        ft.Row([ft.Column([create_detail_row("Operador", t.operador, ft.Icons.ENGINEERING)], expand=1), ft.Column([create_detail_row("Público", str(t.publico), ft.Icons.PEOPLE)], expand=1)], spacing=10),
        
        create_dropdown_row("Status", t.status, get_status_options(), ft.Icons.STARS),
        create_detail_row("Link Stream", t.link_stream, ft.Icons.LINK, is_link=True),
        create_detail_row("Link YouTube", t.link_youtube, ft.Icons.PLAY_CIRCLE_FILL, is_link=True),
        col_links_extras, # Onde entram os links extras
        ft.Container(
            content=ft.Column([
                ft.Row([ft.Icon(ft.Icons.NOTES, size=20, color=ft.Colors.WHITE38), ft.Text("Observações", size=11, color=ft.Colors.WHITE38)], spacing=15), 
                fields.setdefault("Observações", ft.TextField(value=t.observacoes, read_only=False, multiline=True, border=ft.InputBorder.NONE, text_size=14, color=ft.Colors.WHITE70, content_padding=ft.padding.only(left=35), on_change=on_field_change))
            ], spacing=5), 
            padding=ft.padding.symmetric(horizontal=15, vertical=10), bgcolor=ft.Colors.WHITE10, border_radius=10
        ),
        
        # Seção de Horários Reais (Execução)
        ft.Row([
            ft.Icon(ft.Icons.PLAY_CIRCLE_FILL, color=ft.Colors.GREEN_400, size=18),
            ft.Text("Execução Real (Preencher após a transmissão)", size=11, color=ft.Colors.GREEN_400, weight=ft.FontWeight.W_500)
        ], spacing=10, margin=ft.margin.only(top=5)),
        ft.Row([
            ft.Column([create_detail_row("Início Real", t.horario_inicio_real, ft.Icons.PLAY_ARROW_ROUNDED)], expand=1),
            ft.Column([create_detail_row("Fim Real", t.horario_fim_real, ft.Icons.STOP_ROUNDED)], expand=1)
        ], spacing=10),
    ], spacing=10, scroll=ft.ScrollMode.ADAPTIVE)

    def salvar_alteracoes(e):
        from utils.helpers import normalize_date, validar_hora
        t.evento = header.content.controls[1].value
        t.data = normalize_date(fields["Data"].value)
        t.horario_inicio = fields["Início"].value
        t.horario_fim = fields["Fim"].value
        t.responsavel = fields["Responsável"].value; t.local = fields["Local"].value; t.tipo_transmissao = fields["Tipo"].value
        t.modalidade = fields["Modalidade"].value; t.operador = fields["Operador"].value; t.status = fields["Status"].value
        t.horario_inicio_real = fields["Início Real"].value; t.horario_fim_real = fields["Fim Real"].value
        t.link_stream = fields["Link Stream"].value; t.link_youtube = fields["Link YouTube"].value
        t.observacoes = fields["Observações"].value
        try: t.publico = int(fields["Público"].value)
        except: t.publico = 0
        
        # Salvar links extras de volta
        if hasattr(t, 'links_adicionais') and t.links_adicionais:
            for i, link in enumerate(t.links_adicionais):
                key = f"Extra_{i}_{link.get('label', 'Link')}"
                if key in fields: link["url"] = fields[key].value

        if controller:
            controller.atualizar(t)
            if on_update: on_update()
        btn_salvar.visible = False; page.snack_bar = ft.SnackBar(ft.Text("Alterações salvas!"), bgcolor=ft.Colors.GREEN_700); page.snack_bar.open = True; page.update()

    btn_salvar = ft.ElevatedButton("Salvar Alterações", icon=ft.Icons.SAVE, bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE, visible=False, on_click=salvar_alteracoes)
    
    btn_gerar_capa = ft.ElevatedButton(
        "Gerar Capa",
        icon=ft.Icons.IMAGE,
        bgcolor=ft.Colors.INDIGO_700,
        color=ft.Colors.WHITE,
        on_click=lambda _: abrir_gerador_capa(page, t.evento)
    )

    dlg = ft.AlertDialog(content=ft.Container(content=ft.Column([header, ft.Container(content=details_grid, expand=True)], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.STRETCH), width=800, height=750, padding=10), actions=[btn_gerar_capa, btn_salvar, ft.TextButton("Fechar", on_click=lambda e: fechar_dialogo(e, dlg))], actions_alignment=ft.MainAxisAlignment.END, shape=ft.RoundedRectangleBorder(radius=20), bgcolor=ft.Colors.GREY_900)
    def fechar_dialogo(e, d): d.open = False; page.update()
    page.overlay.append(dlg); dlg.open = True; page.update()
