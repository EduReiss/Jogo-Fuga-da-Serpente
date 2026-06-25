"""
Fuja da Serpente
Trabalho de Algoritmos I 

O jogador anda pelo labirinto, pega uma chave (tem 3, só uma abre a
porta) e tenta fugir antes que a serpente alcance ele. A serpente
persegue usando A* com heurística de Manhattan.
"""

import pygame
import random
import heapq
import sys
import os



CELULA = 32
PAINEL = 90

VEL_SERPENTE = 210  # ms entre cada passo da serpente

DELAY_TECLA = 300
REPETICAO_TECLA = 120

COR_FUNDO = (18, 18, 24)
COR_TEXTO = (235, 235, 240)
COR_PAINEL = (28, 28, 36)
COR_SELECAO = (60, 180, 90)


# '#' = parede, espaço = caminho. Desenhei isso no papel antes e fui
# testando até garantir que dá pra chegar em qualquer ponto do mapa.
# tentei criar geração de mapa aleatoria mas getava mapa sem saida ou 
# prendia o jgoador ou a serpente
MAPA = [
    "###################",
    "#   #     #       #",
    "# # ##### # ### # #",
    "# # #   #   #   # #",
    "# # # # # # # ### #",
    "# #   #   # #   # #",
    "# ####### # ### # #",
    "#   #   # #   #   #",
    "# # ### # ####### #",
    "# #     #       # #",
    "# ############# # #",
    "#       #     # # #",
    "# # # # # ### # # #",
    "#     #     #     #",
    "###################",
]

N_LINHAS = len(MAPA)
N_COLS = len(MAPA[0])
LARGURA = N_COLS * CELULA
ALTURA = N_LINHAS * CELULA + PAINEL


def eh_parede(linha, col):
    if linha < 0 or linha >= N_LINHAS or col < 0 or col >= N_COLS:
        return True
    return MAPA[linha][col] == "#"


def celulas_livres():
    livres = []
    for l in range(N_LINHAS):
        for c in range(N_COLS):
            if MAPA[l][c] == " ":
                livres.append((l, c))
    return livres


# ===============================================================
# criação das entidades no começo da partida
# ===============================================================

def sorteia_livre(livres, usadas):
    opcoes = [p for p in livres if p not in usadas]
    return random.choice(opcoes)


def cria_chaves(livres, usadas):
    chaves = []
    for i in range(3):
        pos = sorteia_livre(livres, usadas)
        usadas.add(pos)
        chaves.append({"id": f"chave_{i+1}", "linha": pos[0], "coluna": pos[1]})

    correta = random.choice(chaves)["id"]
    return chaves, correta


def cria_porta(livres, usadas):
    pos = sorteia_livre(livres, usadas)
    usadas.add(pos)
    return {"linha": pos[0], "coluna": pos[1]}


def cria_serpente(livres, usadas):
    pos = sorteia_livre(livres, usadas)
    usadas.add(pos)
    return {"pos": pos}


def cria_jogador(livres):
    pos = random.choice(livres)
    return {"linha": pos[0], "coluna": pos[1], "chave": None, "dir": "baixo"}


# ===============================================================
# jogador
# ===============================================================

def mover_jogador(jogador, dl, dc):
    if dl == -1:
        jogador["dir"] = "cima"
    elif dl == 1:
        jogador["dir"] = "baixo"
    elif dc == -1:
        jogador["dir"] = "esquerda"
    elif dc == 1:
        jogador["dir"] = "direita"

    nl, nc = jogador["linha"] + dl, jogador["coluna"] + dc
    if not eh_parede(nl, nc):
        jogador["linha"], jogador["coluna"] = nl, nc


def coletar_chave(jogador, chaves):
    if jogador["chave"] is not None:
        return
    pos = (jogador["linha"], jogador["coluna"])
    for chave in chaves:
        if (chave["linha"], chave["coluna"]) == pos:
            jogador["chave"] = chave["id"]
            chaves.remove(chave)
            return


def tentar_abrir_porta(jogador, porta, chave_correta):
    pos = (jogador["linha"], jogador["coluna"])
    if pos != (porta["linha"], porta["coluna"]):
        return None
    if jogador["chave"] is None:
        return "sem_chave"
    if jogador["chave"] == chave_correta:
        return "vitoria"
    jogador["chave"] = None
    return "chave_errada"


# ===============================================================
# A* da serpente. Heurística de Manhattan
# Faz a serpente calcular a cada tick a menor distancia entre el e 
# o jogador e perseguir ele de uma forma inteligente
# ===============================================================

def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def vizinhos(pos):
    l, c = pos
    candidatos = [(l-1, c), (l+1, c), (l, c-1), (l, c+1)]
    return [p for p in candidatos if not eh_parede(*p)]


def astar(inicio, destino):
    fila = [(0, inicio)]
    custo = {inicio: 0}
    veio_de = {}
    visitado = set()

    while fila:
        _, atual = heapq.heappop(fila)
        if atual == destino:
            caminho = [atual]
            while atual in veio_de:
                atual = veio_de[atual]
                caminho.append(atual)
            caminho.reverse()
            return caminho[1:]

        if atual in visitado:
            continue
        visitado.add(atual)

        for viz in vizinhos(atual):
            novo_custo = custo[atual] + 1
            if viz not in custo or novo_custo < custo[viz]:
                custo[viz] = novo_custo
                heapq.heappush(fila, (novo_custo + manhattan(viz, destino), viz))
                veio_de[viz] = atual

    return []


def mover_serpente(serpente, jogador):
    destino = (jogador["linha"], jogador["coluna"])
    caminho = astar(serpente["pos"], destino)
    if caminho:
        serpente["pos"] = caminho[0]


def pegou_jogador(serpente, jogador):
    return serpente["pos"] == (jogador["linha"], jogador["coluna"])


# ===============================================================
# sprites e sons 
# ===============================================================

PASTA_IMG = os.path.join("assets", "imagens")
PASTA_SOM = os.path.join("assets", "sons")


def img(nome, tamanho=(CELULA, CELULA)):
    sprite = pygame.image.load(os.path.join(PASTA_IMG, nome)).convert_alpha()
    return pygame.transform.scale(sprite, tamanho)


def carregar_sprites():
    return {
        "parede": img("parede.png"),
        "caminho": img("caminho.png"),
        "jogador_cima": img("jogador_cima.png"),
        "jogador_baixo": img("jogador_baixo.png"),
        "jogador_esquerda": img("jogador_esquerda.png"),
        "jogador_direita": img("jogador_direita.png"),
        "chave": img("chave.png"),
        "porta": img("porta.png"),
        "serpente": img("serpente.png"),
        "menu_fundo": img("menu_fundo.jpg", (LARGURA, ALTURA)),
        "vitoria": img("vitoria.jpg", (LARGURA, ALTURA)),
        "derrota": img("derrota.jpg", (LARGURA, ALTURA)),
    }


def carregar_sons():
    return {
        "chave": pygame.mixer.Sound(os.path.join(PASTA_SOM, "coleta_chave.mp3")),
        "errou": pygame.mixer.Sound(os.path.join(PASTA_SOM, "chave_falsa.ogg")),
        "ganhou": pygame.mixer.Sound(os.path.join(PASTA_SOM, "vitoria.ogg")),
        "perdeu": pygame.mixer.Sound(os.path.join(PASTA_SOM, "derrota.wav")),
    }


# ===============================================================
# desenha as coisa
# ===============================================================

def pixel(linha, col):
    return col * CELULA, linha * CELULA


def desenhar_mapa(tela, sprites):
    for l in range(N_LINHAS):
        for c in range(N_COLS):
            sprite = sprites["parede"] if MAPA[l][c] == "#" else sprites["caminho"]
            tela.blit(sprite, pixel(l, c))


def desenhar_tudo(tela, sprites, jogador, chaves, porta, serpente, fonte, estado):
    tela.fill(COR_FUNDO)
    desenhar_mapa(tela, sprites)

    tela.blit(sprites["porta"], pixel(porta["linha"], porta["coluna"]))

    for chave in chaves:
        tela.blit(sprites["chave"], pixel(chave["linha"], chave["coluna"]))

    tela.blit(sprites["serpente"], pixel(*serpente["pos"]))
    tela.blit(sprites[f"jogador_{jogador['dir']}"], pixel(jogador["linha"], jogador["coluna"]))

    pygame.draw.rect(tela, COR_PAINEL, (0, N_LINHAS * CELULA, LARGURA, PAINEL))
    tem_chave = "sim" if jogador["chave"] else "não"
    texto = f"Tem chave? {tem_chave}   Chaves no mapa: {len(chaves)}   Estado: {estado}"
    tela.blit(fonte.render(texto, True, COR_TEXTO), (12, N_LINHAS * CELULA + 30))


def desenhar_fim(tela, fonte, imagem):
    tela.blit(imagem, (0, 0))
    dica = fonte.render("R para jogar de novo, ESC pra saída", True, COR_TEXTO)
    rect = dica.get_rect(center=(LARGURA // 2, ALTURA - 40))
    pygame.draw.rect(tela, (0, 0, 0), rect.inflate(20, 10))
    pygame.draw.rect(tela, COR_TEXTO, rect.inflate(20, 10), 2)
    tela.blit(dica, rect)


def desenhar_menu(tela, sprites, fonte_opcao, selecionado):
    tela.blit(sprites["menu_fundo"], (0, 0))

    for i, texto in enumerate(["Começar o jogo", "Sair"]):
        cor = COR_SELECAO if i == selecionado else COR_TEXTO
        linha = fonte_opcao.render(texto, True, cor)
        pos_y = 460 + i * 50
        caixa = linha.get_rect(center=(LARGURA // 2, pos_y)).inflate(40, 16)

        pygame.draw.rect(tela, COR_PAINEL, caixa, border_radius=6)
        if i == selecionado:
            pygame.draw.rect(tela, cor, caixa, 2, border_radius=6)

        tela.blit(linha, linha.get_rect(center=(LARGURA // 2, pos_y)))


# ===============================================================
# partida
# ===============================================================

def nova_partida():
    livres = celulas_livres()
    jogador = cria_jogador(livres)
    usadas = {(jogador["linha"], jogador["coluna"])}

    chaves, chave_correta = cria_chaves(livres, usadas)
    porta = cria_porta(livres, usadas)
    serpente = cria_serpente(livres, usadas)

    return jogador, chaves, chave_correta, porta, serpente


TECLAS = {
    pygame.K_w: (-1, 0), pygame.K_UP: (-1, 0),
    pygame.K_s: (1, 0), pygame.K_DOWN: (1, 0),
    pygame.K_a: (0, -1), pygame.K_LEFT: (0, -1),
    pygame.K_d: (0, 1), pygame.K_RIGHT: (0, 1),
}

MOVER_SERPENTE = pygame.USEREVENT + 1


def main():
    pygame.init()
    pygame.mixer.init()
    pygame.display.set_caption("Fuja da Serpente")
    pygame.key.set_repeat(DELAY_TECLA, REPETICAO_TECLA)

    tela = pygame.display.set_mode((LARGURA, ALTURA))
    relogio = pygame.time.Clock()

    fonte_ui = pygame.font.SysFont("arial", 18)
    fonte_menu = pygame.font.SysFont("arial", 26)

    sprites = carregar_sprites()
    sons = carregar_sons()

    pygame.mixer.music.load(os.path.join(PASTA_SOM, "musica.ogg"))
    pygame.mixer.music.set_volume(0.2)
    pygame.mixer.music.play(loops=-1)

    jogador = chaves = chave_correta = porta = serpente = None
    estado = "menu"
    opcao_menu = 0

    pygame.time.set_timer(MOVER_SERPENTE, VEL_SERPENTE)

    rodando = True
    while rodando:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False

            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    rodando = False

                elif estado == "menu":
                    if evento.key in (pygame.K_UP, pygame.K_w, pygame.K_DOWN, pygame.K_s):
                        opcao_menu = 1 - opcao_menu
                    elif evento.key in (pygame.K_RETURN, pygame.K_SPACE):
                        if opcao_menu == 0:
                            pygame.mixer.stop()
                            jogador, chaves, chave_correta, porta, serpente = nova_partida()
                            estado = "jogando"
                        else:
                            rodando = False

                elif estado == "jogando" and evento.key in TECLAS:
                    dl, dc = TECLAS[evento.key]
                    mover_jogador(jogador, dl, dc)

                    antes = len(chaves)
                    coletar_chave(jogador, chaves)
                    if len(chaves) < antes:
                        sons["chave"].play()

                    resultado = tentar_abrir_porta(jogador, porta, chave_correta)
                    if resultado == "vitoria":
                        estado = "vitoria"
                        pygame.mixer.music.stop()
                        sons["ganhou"].play()
                    elif resultado == "chave_errada":
                        sons["errou"].play()

                    if estado == "jogando" and pegou_jogador(serpente, jogador):
                        estado = "derrota"
                        pygame.mixer.music.stop()
                        sons["perdeu"].play()

                elif estado in ("vitoria", "derrota") and evento.key == pygame.K_r:
                    pygame.mixer.stop()
                    jogador, chaves, chave_correta, porta, serpente = nova_partida()
                    estado = "jogando"
                    pygame.mixer.music.play(loops=-1)

            elif evento.type == MOVER_SERPENTE and estado == "jogando":
                mover_serpente(serpente, jogador)
                if pegou_jogador(serpente, jogador):
                    estado = "derrota"
                    pygame.mixer.music.stop()
                    sons["perdeu"].play()

        if estado == "menu":
            desenhar_menu(tela, sprites, fonte_menu, opcao_menu)
        else:
            desenhar_tudo(tela, sprites, jogador, chaves, porta, serpente, fonte_ui, estado.upper())
            if estado == "vitoria":
                desenhar_fim(tela, fonte_ui, sprites["vitoria"])
            elif estado == "derrota":
                desenhar_fim(tela, fonte_ui, sprites["derrota"])

        pygame.display.flip()
        relogio.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
