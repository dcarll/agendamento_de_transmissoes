import flet as ft
from models.transmissao_model import Transmissao
from utils.helpers import get_status_info, format_date_br, get_status_options

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
        mostrar_detalhes_transmissao(page, t)

    # Opções principais
    opcoes_principais = [
        ft.TextButton(
            content=ft.Row([ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.CYAN_200), ft.Text("Ver Detalhes (Clique)", color=ft.Colors.WHITE)], spacing=10),
            on_click=acao_detalhes,
            style=ft.ButtonStyle(padding=15, shape=ft.RoundedRectangleBorder(radius=10))
        ),
        ft.TextButton(
            content=ft.Row([ft.Icon(ft.Icons.EDIT_OUTLINED, color=ft.Colors.BLUE_200), ft.Text("Editar Transmissão (Clique Duplo)", color=ft.Colors.WHITE)], spacing=10),
            on_click=acao_editar,
            style=ft.ButtonStyle(padding=15, shape=ft.RoundedRectangleBorder(radius=10))
        ),
        ft.TextButton(
            content=ft.Row([ft.Icon(ft.Icons.DELETE_FOREVER_OUTLINED, color=ft.Colors.RED_400), ft.Text("Excluir Transmissão", color=ft.Colors.WHITE)], spacing=10),
            on_click=acao_excluir,
            style=ft.ButtonStyle(padding=15, shape=ft.RoundedRectangleBorder(radius=10))
        ),
    ]

    # Submenu de Status
    botoes_status = []
    for status in get_status_options():
        info = get_status_info(status)
        botoes_status.append(
            ft.TextButton(
                content=ft.Row([
                    ft.Icon(info["icon"], color=info["color"], size=18),
                    ft.Text(status, color=ft.Colors.WHITE70, size=13),
                ], spacing=10),
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
        actions=[
            ft.TextButton("Fechar", on_click=lambda e: fechar_dialogo(e, dlg))
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        shape=ft.RoundedRectangleBorder(radius=20),
        bgcolor=ft.Colors.GREY_900,
    )

    def fechar_dialogo(e, d):
        d.open = False
        page.update()

    page.overlay.append(dlg)
    dlg.open = True
    page.update()

def mostrar_detalhes_transmissao(page: ft.Page, t: Transmissao):
    status_info = get_status_info(t.status)
    color_status = status_info["color"]

    def create_detail_row(label, value, icon, is_link=False):
        if not value:
            value = "---"
        
        content = ft.Row([
            ft.Icon(icon, size=20, color=ft.Colors.WHITE38),
            ft.Column([
                ft.Text(label, size=11, color=ft.Colors.WHITE38, weight=ft.FontWeight.W_300),
                ft.TextField(
                    value=value,
                    read_only=True,
                    border=ft.InputBorder.NONE,
                    text_size=15,
                    color=ft.Colors.BLUE_200 if is_link else ft.Colors.WHITE,
                    dense=True,
                    cursor_color=ft.Colors.CYAN_400,
                    selection_color=ft.Colors.CYAN_900,
                    can_reveal_password=False,
                    content_padding=0,
                )
            ], spacing=0, expand=True)
        ], spacing=15, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        return ft.Container(
            content=content,
            padding=ft.padding.symmetric(horizontal=15, vertical=8),
            bgcolor=ft.Colors.WHITE10,
            border_radius=10,
        )

    # Header do Dialog
    header = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.INFO_OUTLINE, color=color_status, size=30),
                ft.Column([
                    ft.Text("Detalhes da Transmissão", size=14, color=ft.Colors.WHITE70),
                    ft.Text(t.evento, size=22, weight=ft.FontWeight.BOLD, overflow=ft.TextOverflow.ELLIPSIS),
                ], spacing=-5, expand=True),
                ft.Container(
                    content=ft.Text(status_info["label"], size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
                    bgcolor=color_status,
                    padding=ft.padding.symmetric(horizontal=12, vertical=5),
                    border_radius=8,
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(height=1, color=ft.Colors.WHITE10)
        ], spacing=15),
        padding=ft.padding.only(bottom=10)
    )

    # Grid de detalhes
    details_grid = ft.Column([
        ft.Row([
            ft.Column([create_detail_row("Data", format_date_br(t.data), ft.Icons.CALENDAR_TODAY)], expand=1),
            ft.Column([create_detail_row("Horário", f"{t.horario_inicio} - {t.horario_fim}", ft.Icons.ACCESS_TIME)], expand=1),
        ], spacing=10),
        
        ft.Row([
            ft.Column([create_detail_row("Responsável", t.responsavel, ft.Icons.PERSON)], expand=1),
            ft.Column([create_detail_row("Local", t.local, ft.Icons.LOCATION_ON)], expand=1),
        ], spacing=10),

        ft.Row([
            ft.Column([create_detail_row("Tipo", t.tipo_transmissao, ft.Icons.LIVE_TV)], expand=1),
            ft.Column([create_detail_row("Modalidade", t.modalidade, ft.Icons.CHAIR)], expand=1),
        ], spacing=10),

        ft.Row([
            ft.Column([create_detail_row("Operador", t.operador, ft.Icons.ENGINEERING)], expand=1),
            ft.Column([create_detail_row("Público", str(t.publico), ft.Icons.PEOPLE)], expand=1),
        ], spacing=10),

        create_detail_row("Link Stream", t.link_stream, ft.Icons.LINK, is_link=True),
        create_detail_row("Link YouTube", t.link_youtube, ft.Icons.PLAY_CIRCLE_FILL, is_link=True),
        
        ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.NOTES, size=20, color=ft.Colors.WHITE38),
                    ft.Text("Observações", size=11, color=ft.Colors.WHITE38),
                ], spacing=15),
                ft.TextField(
                    value=t.observacoes if t.observacoes else "Sem observações adicionais.",
                    read_only=True,
                    multiline=True,
                    border=ft.InputBorder.NONE,
                    text_size=14,
                    color=ft.Colors.WHITE70,
                    selection_color=ft.Colors.CYAN_900,
                    content_padding=ft.padding.only(left=35)
                )
            ], spacing=5),
            padding=ft.padding.symmetric(horizontal=15, vertical=10),
            bgcolor=ft.Colors.WHITE10,
            border_radius=10,
        )
    ], spacing=10, scroll=ft.ScrollMode.ADAPTIVE)

    dlg = ft.AlertDialog(
        content=ft.Container(
            content=ft.Column([
                header,
                ft.Container(content=details_grid, expand=True)
            ], spacing=10),
            width=600,
            height=650,
            padding=10
        ),
        actions=[
            ft.TextButton("Fechar", on_click=lambda e: fechar_dialogo(e, dlg))
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        shape=ft.RoundedRectangleBorder(radius=20),
        bgcolor=ft.Colors.GREY_900,
    )

    def fechar_dialogo(e, d):
        d.open = False
        page.update()

    page.overlay.append(dlg)
    dlg.open = True
    page.update()
