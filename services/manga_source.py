import requests
from bs4 import BeautifulSoup

def buscar_manga(nome):
    # Exemplo genérico (troque pela fonte que quiser)
    url = f"https://site-exemplo.com/search?q={nome}"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return None

    soup = BeautifulSoup(response.text, "lxml")

    resultados = []
    for item in soup.select(".manga-item a"):
        titulo = item.text.strip()
        link = item.get("href")
        resultados.append((titulo, link))

    return resultados[:5]
