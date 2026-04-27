import flet as ft
from models.transmissao_model import Transmissao
from controllers.transmissao_controller import TransmissaoController
from utils.helpers import validar_hora, normalize_date, mascarar_hora
from datetime import datetime

class FormularioView(ft.Column):
    def __init__(self, controller: TransmissaoController, on_back, transmissao_edit: Transmissao = None, default_date=None):
        super().__init__(expand=True, scroll=ft.ScrollMode.ADAPTIVE, spacing=20)
        self.controller = controller
        self.on_back = on_back
        self.edit_mode = transmissao_edit is not None
        self.t_edit = transmissao_edit
        self.default_date = default_date
        self.init_ui()

    def wrap_field_gradient(self, control, expand=False):
        return ft.Container(
            content=control,
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, -1),
                end=ft.Alignment(1, 1),
                colors=[ft.Colors.with_opacity(0.12, ft.Colors.WHITE), ft.Colors.with_opacity(0.02, ft.Colors.WHITE)]
            ),
            border_radius=12,
            border=ft.border.all(1, ft.Colors.with_opacity(0.2, ft.Colors.WHITE)),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
                offset=ft.Offset(0, 0),
            ),
            padding=ft.padding.only(left=10, right=10),
            expand=expand,
            on_hover=self.set_hover,
            animate=ft.Animation(300, ft.AnimationCurve.DECELERATE),
        )

    def init_ui(self):
        # Campos
        self.txt_evento = ft.TextField(label="Nome do Evento*", value=self.t_edit.evento if self.edit_mode else "", border=ft.InputBorder.NONE, filled=False, text_size=16)
        self.txt_responsavel = ft.TextField(label="Responsável*", value=self.t_edit.responsavel if self.edit_mode else "", border=ft.InputBorder.NONE, filled=False, text_size=16)
        # Converte data para exibição DD/MM/AAAA
        if self.edit_mode:
            from utils.helpers import parse_date as _pd
            _dt = _pd(self.t_edit.data)
            data_display = _dt.strftime("%d/%m/%Y") if _dt else self.t_edit.data
        elif self.default_date:
            data_display = self.default_date.strftime("%d/%m/%Y")
        else:
            data_display = datetime.now().strftime("%d/%m/%Y")
        
        self.txt_data = ft.TextField(
            label="Data*", 
            value=data_display,
            read_only=True,
            on_click=self.abrir_calendario,
            border=ft.InputBorder.NONE,
            filled=False,
            text_size=16
        )
        self.txt_inicio = ft.TextField(
            label="Início (HH:MM)*", 
            value=self.t_edit.horario_inicio if self.edit_mode else "09:00", 
            hint_text="00:00",
            on_change=mascarar_hora,
            border=ft.InputBorder.NONE,
            filled=False,
            width=150,
            text_size=16
        )
        self.txt_fim = ft.TextField(
            label="Fim (HH:MM)*", 
            value=self.t_edit.horario_fim if self.edit_mode else "11:00", 
            hint_text="00:00",
            on_change=mascarar_hora,
            border=ft.InputBorder.NONE,
            filled=False,
            width=150,
            text_size=16
        )

        # Campos de Horário Real
        self.txt_inicio_real = ft.TextField(
            label="Início Real (HH:MM)", 
            value=self.t_edit.horario_inicio_real if self.edit_mode else "", 
            hint_text="00:00",
            on_change=mascarar_hora,
            border=ft.InputBorder.NONE,
            filled=False,
            width=180,
            text_size=16
        )
        self.txt_fim_real = ft.TextField(
            label="Término Real (HH:MM)", 
            value=self.t_edit.horario_fim_real if self.edit_mode else "", 
            hint_text="00:00",
            on_change=mascarar_hora,
            border=ft.InputBorder.NONE,
            filled=False,
            width=180,
            text_size=16
        )
        
        # Opções padrão para o dropdown
        opcoes_padrao = ["StreamYard+Youtube", "OBS+YOUTUBE", "ZOOM+YOUTUBE", "OBS+YOUTUBE+STREAMYARD", "GRAVAÇÃO", "YouTube", "StreamYard", "Zoom"]
        tipo_no_db = self.t_edit.tipo_transmissao if self.edit_mode else "YouTube"
        
        valor_inicial = tipo_no_db
        valor_custom = ""
        mostrar_custom = False
        
        # Se o valor vindo do DB não está na lista padrão...
        if tipo_no_db not in opcoes_padrao:
            valor_inicial = "Outro"
            mostrar_custom = True
            # Só coloca no campo custom se NÃO for a própria palavra "Outro" 
            # (para evitar que o campo mostre "Outro" quando o usuário ainda vai digitar)
            if tipo_no_db != "Outro":
                valor_custom = tipo_no_db

        def on_tipo_change(e):
            self.container_tipo_custom.visible = (e.control.value == "Outro")
            if e.control.value == "Outro" and not self.txt_tipo_custom.value:
                self.txt_tipo_custom.value = "" # Garante que comece vazio se for seleção manual de "Outro"
            self.update()

        self.dd_tipo = ft.Dropdown(
            label="Tipo de Transmissão*",
            options=[ft.dropdown.Option(o) for o in opcoes_padrao] + [ft.dropdown.Option("Outro")],
            value=valor_inicial,
            on_select=on_tipo_change,
            border=ft.InputBorder.NONE,
            filled=False,
            expand=True,
            text_size=16
        )

        self.txt_tipo_custom = ft.TextField(
            label="Qual o tipo?",
            value=valor_custom,
            border=ft.InputBorder.NONE,
            filled=False,
            expand=True,
            text_size=16,
            hint_text="Digite o nome do tipo..."
        )

        self.container_tipo_custom = ft.Container(
            content=self.txt_tipo_custom,
            expand=True,
            padding=10,
            bgcolor=ft.Colors.WHITE10,
            border_radius=15,
            border=ft.border.all(1, ft.Colors.WHITE24),
            visible=mostrar_custom
        )
        
        self.dd_modalidade = ft.Dropdown(
            label="Modalidade",
            options=[ft.dropdown.Option(o) for o in ["Presencial", "Online", "Híbrido"]],
            value=self.t_edit.modalidade if self.edit_mode else "Online",
            border=ft.InputBorder.NONE,
            filled=False,
            expand=True,
            text_size=16
        )
        
        self.txt_local = ft.TextField(label="Local", value=self.t_edit.local if self.edit_mode else "Auditório Central", border=ft.InputBorder.NONE, filled=False, text_size=16)
        self.txt_link_stream = ft.TextField(label="Link da Stream (Privado)", value=self.t_edit.link_stream if self.edit_mode else "", border=ft.InputBorder.NONE, filled=False, text_size=16)
        self.txt_link_youtube = ft.TextField(label="Link do YouTube (Público)", value=self.t_edit.link_youtube if self.edit_mode else "", border=ft.InputBorder.NONE, filled=False, text_size=16)
        
        from utils.helpers import get_status_options
        self.dd_status = ft.Dropdown(
            label="Status",
            options=[ft.dropdown.Option(o) for o in get_status_options()],
            value=self.t_edit.status if self.edit_mode else "Agendado (Fase 1)",
            border=ft.InputBorder.NONE,
            filled=False,
            expand=True,
            text_size=16
        )
        
        self.txt_publico = ft.TextField(label="Público Aproximado", value=str(self.t_edit.publico) if self.edit_mode else "0", keyboard_type=ft.KeyboardType.NUMBER, border=ft.InputBorder.NONE, filled=False, text_size=16)
        self.txt_operador = ft.TextField(label="Operador", value=self.t_edit.operador if self.edit_mode else "", border=ft.InputBorder.NONE, filled=False, text_size=16)
        self.txt_obs = ft.TextField(label="Observações", value=self.t_edit.observacoes if self.edit_mode else "", multiline=True, min_lines=3, border=ft.InputBorder.NONE, filled=False, text_size=16)
        
        # Controle de Links Adicionais
        self.col_links_adicionais = ft.Column(spacing=10)
        self.extra_links_fields = []
        
        if self.edit_mode and hasattr(self.t_edit, 'links_adicionais'):
            for item in self.t_edit.links_adicionais:
                # Verifica se é o novo formato (dict) ou legado (str)
                if isinstance(item, dict):
                    self.adicionar_link_field(item.get("label", ""), item.get("url", ""))
                else:
                    self.adicionar_link_field("", item)

        titulo = "Editar Transmissão" if self.edit_mode else "Nova Transmissão"
        
        self.controls = [
            ft.Row([
                ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: self.on_back()),
                ft.Text(titulo, size=32, weight=ft.FontWeight.BOLD),
            ], alignment=ft.MainAxisAlignment.START, spacing=10),
            
            ft.Divider(height=20),
            
            # Form Layout
            ft.Column([
                ft.Row([self.wrap_field_gradient(self.txt_evento, True), self.wrap_field_gradient(self.txt_responsavel, True)]),
                ft.Row([self.wrap_field_gradient(self.txt_data, True), self.wrap_field_gradient(self.txt_inicio), self.wrap_field_gradient(self.txt_fim)]),
                
                ft.Row([
                    self.wrap_field_gradient(self.dd_tipo, True),
                    self.wrap_field_gradient(self.dd_modalidade, True),
                    self.wrap_field_gradient(self.dd_status, True)
                ]),
                # Linha condicional para o tipo customizado
                ft.Row([self.container_tipo_custom], visible=True),
                self.wrap_field_gradient(self.txt_local),
                ft.Row([
                    self.wrap_field_gradient(self.txt_link_stream, True),
                    ft.Row([
                        self.wrap_field_gradient(self.txt_link_youtube, True),
                        ft.IconButton(
                            ft.Icons.ADD_LINK,
                            tooltip="Adicionar mais links",
                            icon_color=ft.Colors.BLUE_400,
                            on_click=lambda _: self.adicionar_link_field()
                        )
                    ], expand=True, spacing=5)
                ]),
                self.col_links_adicionais,
                ft.Row([self.wrap_field_gradient(self.txt_publico, True), self.wrap_field_gradient(self.txt_operador, True)]),
                self.wrap_field_gradient(self.txt_obs),
                # Seção de Horários Reais com destaque sutil
                ft.Row([
                    ft.Icon(ft.Icons.PLAY_CIRCLE_FILL, color=ft.Colors.GREEN_400, size=20),
                    ft.Text("Execução Real (Preencher após a transmissão)", size=12, color=ft.Colors.GREEN_400, weight=ft.FontWeight.W_500)
                ], spacing=10, margin=ft.margin.only(top=10)),
                ft.Row([
                    self.wrap_field_gradient(self.txt_inicio_real, True), 
                    self.wrap_field_gradient(self.txt_fim_real, True)
                ]),
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                ft.Row([
                    ft.ElevatedButton(
                        "Salvar Transmissão", 
                        icon=ft.Icons.SAVE, 
                        style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE),
                        on_click=self.salvar,
                        height=50,
                        expand=True
                    ),
                    ft.OutlinedButton(
                        "Cancelar", 
                        on_click=lambda _: self.on_back(),
                        height=50,
                        expand=True
                    )
                ], spacing=20)
            ], spacing=20)
        ]

    def adicionar_link_field(self, label_val="", url_val=""):
        idx = len(self.extra_links_fields) + 1
        label_final = label_val if label_val else f"Link Adicional {idx}"
        
        txt_label = ft.TextField(
            label="Nome do Link", 
            value=label_final, 
            border=ft.InputBorder.NONE, 
            filled=False, 
            text_size=16,
            width=200
        )
        txt_url = ft.TextField(
            label="URL", 
            value=url_val, 
            border=ft.InputBorder.NONE, 
            filled=False, 
            text_size=16,
            expand=True
        )
        
        self.extra_links_fields.append({"label": txt_label, "url": txt_url})
        
        row = ft.Row([
            self.wrap_field_gradient(txt_label),
            self.wrap_field_gradient(txt_url, True),
            ft.IconButton(
                ft.Icons.DELETE_OUTLINE,
                icon_color=ft.Colors.RED_400,
                on_click=lambda e: self.remover_link_field(row, txt_label, txt_url)
            )
        ], spacing=5)
        
        self.col_links_adicionais.controls.append(row)
        try:
            self.update()
        except:
            pass

    def remover_link_field(self, row, label_field, url_field):
        self.col_links_adicionais.controls.remove(row)
        # Remove do rastreamento de campos
        for i, item in enumerate(self.extra_links_fields):
            if item["label"] == label_field:
                self.extra_links_fields.pop(i)
                break
        self.update()

    def abrir_calendario(self, e):
        def on_change(e):
            val = e.control.value
            if val:
                self.txt_data.value = val.strftime("%d/%m/%Y")
                self.update()

        # Tenta pegar a data atual do campo para abrir o calendário nela
        data_atual = normalize_date(self.txt_data.value)
        from utils.helpers import parse_date
        dt_inicial = parse_date(data_atual) or datetime.now()

        dp = ft.DatePicker(
            on_change=on_change,
            value=dt_inicial,
            first_date=datetime(2020, 1, 1),
            last_date=datetime(2030, 12, 31),
            confirm_text="Confirmar",
            cancel_text="Cancelar",
            help_text="Selecione a data da transmissão"
        )
        self.page.overlay.append(dp)
        self.page.update()
        dp.open = True
        self.page.update()


    def to_minutes(self, hora_str):
        try:
            h, m = map(int, hora_str.split(':'))
            return h * 60 + m
        except:
            return 0

    def salvar(self, e):
        # Validações Básicas
        if not self.txt_evento.value or not self.txt_responsavel.value:
            self.show_error("Preencha os campos obrigatórios (*)!")
            return
        
        if not validar_hora(self.txt_inicio.value) or not validar_hora(self.txt_fim.value):
            self.show_error("Formato de hora inválido (HH:MM)!")
            return

        try:
            publico = int(self.txt_publico.value) if self.txt_publico.value else 0
        except:
            self.show_error("Público deve ser um número!")
            return

        # Converte DD/MM/YYYY de volta para YYYY-MM-DD para armazenamento
        data_salvar = self.txt_data.value
        try:
            dt_parsed = datetime.strptime(data_salvar, "%d/%m/%Y")
            data_salvar = dt_parsed.strftime("%Y-%m-%d")
        except:
            pass  # Se já estiver em outro formato, normalize_date cuida

        # Captura o valor do tipo: se for "Outro", pega o que está no txt_tipo_custom
        tipo = self.dd_tipo.value
        if tipo == "Outro":
            # Se for "Outro", o valor final é o que estiver na caixa de texto.
            # Se a caixa estiver vazia, salvamos como "Outro" mesmo.
            custom_val = self.txt_tipo_custom.value
            if custom_val and custom_val.strip() != "":
                tipo = custom_val
        
        # Fallback final se nada vier em tipo
        if not tipo or tipo.strip() == "":
            tipo = "YouTube" 

        dados = {
            "evento": self.txt_evento.value,
            "responsavel": self.txt_responsavel.value,
            "data": data_salvar,
            "horario_inicio": self.txt_inicio.value,
            "horario_fim": self.txt_fim.value,
            "horario_inicio_real": self.txt_inicio_real.value,
            "horario_fim_real": self.txt_fim_real.value,
            "tipo_transmissao": tipo,
            "modalidade": self.dd_modalidade.value,
            "status": self.dd_status.value,
            "local": self.txt_local.value,
            "link_stream": self.txt_link_stream.value,
            "link_youtube": self.txt_link_youtube.value,
            "publico": publico,
            "operador": self.txt_operador.value,
            "observacoes": self.txt_obs.value,
            "links_adicionais": [{"label": f["label"].value, "url": f["url"].value} for f in self.extra_links_fields if f["url"].value.strip()]
        }
        
        print(f"[DEBUG] Salvando tipo final: {tipo}")

        if self.edit_mode:
            conflito = self.verificar_conflito(dados)
            if conflito:
                self.confirmar_duplicado(dados, conflito)
            else:
                self.finalizar_salvamento(dados)
        else:
            conflito = self.verificar_conflito(dados)
            if conflito:
                self.confirmar_duplicado(dados, conflito)
            else:
                self.finalizar_salvamento(dados)

    def verificar_conflito(self, dados):
        # Se a própria transmissão que estamos salvando já é "Finalizada" ou "Cancelada", não checamos conflitos
        if dados["status"] and (dados["status"].startswith("Finalizado") or dados["status"] == "Cancelado"):
            return None
            
        data_nova = normalize_date(dados["data"])
        novo_ini = self.to_minutes(dados["horario_inicio"])
        # Se o fim não for informado ou for inválido, assume 1h depois (mas aqui temos validação antes)
        novo_fim = self.to_minutes(dados["horario_fim"])
        
        for t in self.controller.transmissoes:
            # Se for edição, ignora a si mesmo
            if self.edit_mode and t.id == self.t_edit.id:
                continue
                
            if normalize_date(t.data) == data_nova:
                # Ignora transmissões que já foram finalizadas ou canceladas
                if t.status and (t.status.startswith("Finalizado") or t.status == "Cancelado"):
                    continue
                    
                ex_ini = self.to_minutes(t.horario_inicio)
                ex_fim = self.to_minutes(t.horario_fim)
                
                # Verifica sobreposição de horários
                if novo_ini < ex_fim and novo_fim > ex_ini:
                    return t
        return None

    def confirmar_duplicado(self, dados, original):
        dlg = None
        
        def fechar(e):
            dlg.open = False
            self.page.update()

        def salvar_mesmo_assim(e):
            dlg.open = False
            self.page.update()
            self.finalizar_salvamento(dados)

        dlg = ft.AlertDialog(
            title=ft.Text("⚠️ Conflito Detectado"),
            content=ft.Text(
                f"Já existe uma transmissão agendada para este horário:\n\n"
                f"📌 Evento: {original.evento}\n"
                f"📅 Data: {original.data}\n"
                f"⏰ Início: {original.horario_inicio}\n\n"
                "Deseja cadastrar mesmo assim?"
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=fechar),
                ft.ElevatedButton("Sim, Cadastrar Mesmo Assim", bgcolor=ft.Colors.AMBER_700, on_click=salvar_mesmo_assim),
            ]
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    def finalizar_salvamento(self, dados):
        try:
            if self.edit_mode:
                dados["id"] = self.t_edit.id
                dados["tempo_total"] = self.t_edit.tempo_total
                dados["data_criacao"] = self.t_edit.data_criacao
                t = Transmissao.from_dict(dados)
                self.controller.atualizar(t)
            else:
                t = Transmissao(**dados)
                self.controller.adicionar(t)
                
            self.on_back()
        except Exception as ex:
            self.show_error(f"Erro ao salvar: {ex}")

    def show_error(self, msg):
        snack = ft.SnackBar(ft.Text(msg), bgcolor=ft.Colors.RED_700)
        if self.page:
            self.page.overlay.append(snack)
            snack.open = True
            self.page.update()

    def set_hover(self, e):
        is_hover = e.data == "true"
        
        e.control.scale = 1.01 if is_hover else 1.0
        
        if is_hover:
            if not hasattr(e.control, "_orig_shadow"):
                e.control._orig_shadow = e.control.shadow
            if not hasattr(e.control, "_orig_border"):
                e.control._orig_border = e.control.border
                
            e.control.shadow = ft.BoxShadow(
                blur_radius=15,
                color=ft.Colors.with_opacity(0.15, ft.Colors.CYAN_400),
                spread_radius=1
            )
            e.control.border = ft.border.all(1, ft.Colors.with_opacity(0.4, ft.Colors.WHITE))
        else:
            e.control.shadow = getattr(e.control, "_orig_shadow", None)
            e.control.border = getattr(e.control, "_orig_border", None)
            
        e.control.update()
