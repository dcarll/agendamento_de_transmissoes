"""
Script para gerar o ícone do aplicativo (transmissoes.ico).
Usa apenas a biblioteca Pillow para criar um ícone com tema de transmissão/streaming.
Execute este script uma vez para gerar o arquivo .ico.
"""

from PIL import Image, ImageDraw, ImageFont
import math
import os

def criar_icone():
    sizes = [256]
    imgs = []
    
    for size in sizes:
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        cx, cy = size // 2, size // 2
        margin = int(size * 0.05)
        
        # ── Fundo circular com gradiente radial (azul escuro → azul elétrico) ──
        for r in range(cx - margin, 0, -1):
            ratio = r / (cx - margin)
            # Gradiente: centro claro → borda escura
            red   = int(25 + (41 - 25) * ratio)
            green = int(118 + (35 - 118) * ratio)
            blue  = int(255 + (126 - 255) * ratio)
            alpha = 255
            draw.ellipse(
                [cx - r, cy - r, cx + r, cy + r],
                fill=(red, green, blue, alpha)
            )
        
        # ── Torre/Antena central ──
        tower_color = (255, 255, 255, 240)
        tower_w = int(size * 0.06)
        tower_h = int(size * 0.35)
        tower_top = cy - int(size * 0.05)
        tower_bottom = tower_top + tower_h
        
        # Haste principal
        draw.rectangle(
            [cx - tower_w // 2, tower_top, cx + tower_w // 2, tower_bottom],
            fill=tower_color
        )
        
        # Base da antena (triângulo)
        base_w = int(size * 0.18)
        base_h = int(size * 0.10)
        draw.polygon(
            [
                (cx - base_w // 2, tower_bottom + base_h),
                (cx + base_w // 2, tower_bottom + base_h),
                (cx + tower_w // 2 + 2, tower_bottom),
                (cx - tower_w // 2 - 2, tower_bottom),
            ],
            fill=tower_color
        )
        
        # Ponta da antena (círculo)
        dot_r = int(size * 0.04)
        draw.ellipse(
            [cx - dot_r, tower_top - dot_r * 2, cx + dot_r, tower_top],
            fill=(100, 200, 255, 255)
        )
        
        # ── Ondas de sinal (arcos concêntricos) ──
        wave_color_left  = (100, 200, 255, 180)
        wave_color_right = (100, 200, 255, 180)
        
        wave_cx = cx
        wave_cy = tower_top - dot_r
        
        for i, radius in enumerate([int(size * 0.15), int(size * 0.25), int(size * 0.35)]):
            alpha = max(80, 180 - i * 50)
            thickness = max(2, int(size * 0.025))
            color = (100, 200, 255, alpha)
            
            # Arco esquerdo (onda saindo para a esquerda)
            bbox = [wave_cx - radius, wave_cy - radius, wave_cx + radius, wave_cy + radius]
            draw.arc(bbox, start=200, end=250, fill=color, width=thickness)
            
            # Arco direito (onda saindo para a direita)
            draw.arc(bbox, start=290, end=340, fill=color, width=thickness)
        
        # ── Ícone de calendário pequeno (canto inferior direito) ──
        cal_size = int(size * 0.28)
        cal_x = cx + int(size * 0.18)
        cal_y = cy + int(size * 0.18)
        
        # Fundo do calendário
        cal_bg = (30, 60, 120, 220)
        cal_border = (100, 200, 255, 255)
        
        # Retângulo do calendário
        draw.rounded_rectangle(
            [cal_x, cal_y, cal_x + cal_size, cal_y + cal_size],
            radius=int(size * 0.02),
            fill=cal_bg,
            outline=cal_border,
            width=max(1, int(size * 0.01))
        )
        
        # Barra superior do calendário
        bar_h = int(cal_size * 0.25)
        draw.rounded_rectangle(
            [cal_x, cal_y, cal_x + cal_size, cal_y + bar_h],
            radius=int(size * 0.02),
            fill=cal_border
        )
        
        # Pontos do calendário (grade de dias)
        dot_size = max(2, int(cal_size * 0.08))
        grid_margin = int(cal_size * 0.15)
        grid_area_w = cal_size - grid_margin * 2
        grid_area_h = cal_size - bar_h - grid_margin * 2
        
        for row in range(3):
            for col in range(3):
                dx = cal_x + grid_margin + int(col * grid_area_w / 2.5)
                dy = cal_y + bar_h + grid_margin + int(row * grid_area_h / 2.5)
                draw.ellipse(
                    [dx, dy, dx + dot_size, dy + dot_size],
                    fill=(200, 230, 255, 200)
                )
        
        # ── Ícone de play pequeno (canto inferior esquerdo) ──
        play_size = int(size * 0.16)
        play_cx = cx - int(size * 0.28)
        play_cy = cy + int(size * 0.28)
        
        # Círculo de fundo
        play_r = play_size // 2
        draw.ellipse(
            [play_cx - play_r, play_cy - play_r, play_cx + play_r, play_cy + play_r],
            fill=(30, 60, 120, 200),
            outline=(100, 200, 255, 255),
            width=max(1, int(size * 0.01))
        )
        
        # Triângulo de play
        tri_size = int(play_size * 0.35)
        tri_offset = int(tri_size * 0.15)  # Offset para centralizar visualmente
        draw.polygon(
            [
                (play_cx - tri_size // 2 + tri_offset, play_cy - tri_size),
                (play_cx - tri_size // 2 + tri_offset, play_cy + tri_size),
                (play_cx + tri_size + tri_offset, play_cy),
            ],
            fill=(100, 200, 255, 240)
        )
        
        imgs.append(img)
    
    # Gera múltiplos tamanhos a partir da imagem principal de 256px
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "transmissoes.ico")
    os.makedirs(os.path.dirname(icon_path), exist_ok=True)
    
    # Salva como .ico com múltiplos tamanhos
    base_img = imgs[0]
    icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    base_img.save(
        icon_path,
        format="ICO",
        sizes=icon_sizes
    )
    
    # Salva também como PNG para uso no Flet
    png_path = os.path.join(os.path.dirname(icon_path), "transmissoes.png")
    base_img.save(png_path, format="PNG")
    
    print("Icone gerado com sucesso!")
    print(f"   ICO: {icon_path}")
    print(f"   PNG: {png_path}")


if __name__ == "__main__":
    criar_icone()
