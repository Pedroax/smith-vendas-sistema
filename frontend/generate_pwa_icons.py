"""
Gera ícones PWA placeholder para o Smith 2.0
Execute: python generate_pwa_icons.py
"""
from PIL import Image, ImageDraw, ImageFont
import os

# Criar diretório de ícones
icons_dir = "public/icons"
os.makedirs(icons_dir, exist_ok=True)

# Tamanhos necessários para PWA
sizes = [72, 96, 128, 144, 152, 192, 384, 512]

# Cores do tema
bg_color = (59, 130, 246)  # Blue-500 (#3b82f6)
text_color = (255, 255, 255)  # White

def create_icon(size):
    """Cria um ícone com as iniciais S2"""
    # Criar imagem
    img = Image.new('RGB', (size, size), bg_color)
    draw = ImageDraw.Draw(img)

    # Adicionar borda arredondada (simulada com círculo)
    mask = Image.new('L', (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse([0, 0, size, size], fill=255)

    # Criar círculo de fundo
    output = Image.new('RGB', (size, size), (255, 255, 255, 0))
    output.paste(img, (0, 0))

    # Desenhar texto "S2"
    try:
        # Tentar usar fonte do sistema
        font_size = int(size * 0.4)
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.truetype("Arial.ttf", font_size)
    except:
        # Fallback para fonte padrão
        font = ImageFont.load_default()

    # Centralizar texto
    text = "S2"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = (size - text_width) // 2
    y = (size - text_height) // 2 - int(size * 0.05)

    draw.text((x, y), text, fill=text_color, font=font)

    return output

# Gerar todos os ícones
print("Gerando ícones PWA...")
for size in sizes:
    icon = create_icon(size)
    filename = f"{icons_dir}/icon-{size}x{size}.png"
    icon.save(filename, "PNG")
    print(f"[OK] Criado: {filename}")

print("\n[OK] Ícones PWA gerados com sucesso!")
print("\nPróximo passo:")
print("1. Substitua os ícones placeholder por seu logo real")
print("2. Use uma ferramenta como https://realfavicongenerator.net/ para criar ícones profissionais")
