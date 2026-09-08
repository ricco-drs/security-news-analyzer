import sys

import requests
from bs4 import BeautifulSoup
from datetime import datetime

# Muchos portales de noticias responden 403 si no reciben un User-Agent de
# navegador. Se envia una cabecera realista en cada peticion.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def analyze_url(url):
    response = requests.get(url, headers=HEADERS, timeout=10)
    response.raise_for_status()

    # requests no siempre detecta bien la codificacion desde las cabeceras;
    # apparent_encoding la infiere del contenido y evita que los acentos
    # salgan como "Ã³".
    response.encoding = response.apparent_encoding

    soup = BeautifulSoup(response.text, "html.parser")

    # soup.title.string devuelve None cuando el <title> contiene etiquetas
    # anidadas; get_text las aplana.
    if soup.title:
        title = soup.title.get_text(strip=True)
    else:
        title = "Sin titulo"

    text = soup.get_text(separator=" ", strip=True)
    words = text.split()

    return {
        "url": url,
        "title": title,
        "characters": len(text),
        "words": len(words),
        "analyzed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def main():
    # En la consola de Windows la salida por defecto no es UTF-8 y los
    # acentos se ven como "?". Se fuerza UTF-8 en stdout.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    print("=== Security News Analyzer ===")
    url = input("Ingrese una URL: ").strip()

    try:
        result = analyze_url(url)
    except Exception as error:
        print(f"\nNo se pudo analizar la URL: {error}")
        return

    print("\nResultado")
    print("-" * 40)
    print(f"Titulo: {result['title']}")
    print(f"Caracteres: {result['characters']}")
    print(f"Palabras: {result['words']}")
    print(f"Fecha: {result['analyzed_at']}")


if __name__ == "__main__":
    main()
