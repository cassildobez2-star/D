import requests
import os

def baixar_imagem(url, pasta="downloads"):
    if not os.path.exists(pasta):
        os.makedirs(pasta)

    nome_arquivo = url.split("/")[-1]
    caminho = os.path.join(pasta, nome_arquivo)

    r = requests.get(url)
    with open(caminho, "wb") as f:
        f.write(r.content)

    return caminho
