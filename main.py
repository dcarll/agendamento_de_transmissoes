import flet as ft
from app import TransmissionApp

def main(page: ft.Page):
    # Inicializa a aplicação
    TransmissionApp(page)

if __name__ == "__main__":
    # Inicia diretamente no modo desktop
    ft.run(main, assets_dir="assets")
