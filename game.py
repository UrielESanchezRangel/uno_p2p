import pygame
import random
import requests
import string
import socket
import subprocess
import os
import sys
import json
from network import P2PNode
from config import PORT, RELAY_SERVER

pygame.init()
WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("UNO P2P")
font = pygame.font.SysFont(None, 28)

def draw_text(text, x, y, color=(255, 255, 255)):
    label = font.render(text, True, color)
    screen.blit(label, (x, y))

def draw_centered_text(text, rect, color=(255, 255, 255)):
    label = font.render(text, True, color)
    text_rect = label.get_rect(center=rect.center)
    screen.blit(label, text_rect)

def generar_codigo():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def obtener_ip_local():
    return socket.gethostbyname(socket.gethostname())

def crear_mazo():
    colores = ["Rojo", "Verde", "Azul", "Amarillo"]
    valores = [str(i) for i in range(0, 10)] + ["Salto", "+2", "Reversa"]
    mazo = []
    for color in colores:
        for valor in valores:
            mazo.append(f"{color} {valor}")
            mazo.append(f"{color} {valor}")
    comodines = ["Comodín", "Comodín +4"] * 4
    mazo.extend(comodines)
    random.shuffle(mazo)
    return mazo

def carta_valida(carta, actual):
    if not actual:
        return True
    color, valor = carta.split(" ", 1) if " " in carta else (carta, "")
    a_color, a_valor = actual.split(" ", 1) if " " in actual else (actual, "")
    return color == a_color or valor == a_valor or "Comodín" in carta

def obtener_color_rgb(carta):
    if "Rojo" in carta:
        return (220, 30, 30)
    elif "Verde" in carta:
        return (30, 180, 70)
    elif "Azul" in carta:
        return (30, 100, 220)
    elif "Amarillo" in carta:
        return (230, 230, 50)
    elif "Comodín" in carta:
        return (0, 0, 0)
    else:
        return (100, 100, 100)

def reciclar_mazo(mazo, pila):
    if not mazo and len(pila) > 1:
        carta_superior = pila[-1]
        mazo.extend(pila[:-1])
        random.shuffle(mazo)
        pila[:] = [carta_superior]

def seleccionar_color():
    colores = [("Rojo", (220, 30, 30)), ("Verde", (30, 180, 70)),
               ("Azul", (30, 100, 220)), ("Amarillo", (230, 230, 50))]
    opciones = []
    while True:
        screen.fill((20, 20, 20))
        draw_text("Selecciona un color:", 380, 150)
        for i, (nombre, color) in enumerate(colores):
            rect = pygame.Rect(370 + i * 100, 200, 80, 80)
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, (255, 255, 255), rect, 3)
            draw_centered_text(nombre, rect)
            opciones.append((rect, nombre))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                for rect, nombre in opciones:
                    if rect.collidepoint(mx, my):
                        return nombre
def main():
    state = "menu"
    name_text = ""
    code_text = ""
    active_name = False
    active_code = False
    is_join = False
    is_host_selected = True

    clock = pygame.time.Clock()
    chat_input = ""
    chat_messages = []

    player_name = ""
    node = None
    codigo_sala = ""
    jugadores = []
    manos = {}
    turno_actual = 0
    mazo = []
    pila = []
    carta_actual = None

    while True:
        clock.tick(30)
        screen.fill((30, 30, 30))

        if state == "menu":
            draw_text("Tu nombre:", 100, 80)
            pygame.draw.rect(screen, (255, 255, 255), (220, 75, 200, 30), 2)
            draw_text(name_text + "_", 225, 80)

            draw_text("Modo:", 100, 130)
            pygame.draw.rect(screen, (80, 180, 80) if is_host_selected else (100, 100, 100), (220, 125, 120, 30))
            draw_text("Crear sala", 230, 130)

            pygame.draw.rect(screen, (80, 180, 80) if is_join else (100, 100, 100), (360, 125, 120, 30))
            draw_text("Unirse", 380, 130)

            if is_join:
                draw_text("Código de sala:", 100, 180)
                pygame.draw.rect(screen, (255, 255, 255), (250, 175, 150, 30), 2)
                draw_text(code_text + "_", 255, 180)

            pygame.draw.rect(screen, (255, 255, 255), (300, 250, 160, 40), 2)
            draw_text("Continuar", 340, 260)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); return

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    active_name = pygame.Rect(220, 75, 200, 30).collidepoint(mx, my)
                    active_code = pygame.Rect(250, 175, 150, 30).collidepoint(mx, my)
                    if pygame.Rect(220, 125, 120, 30).collidepoint(mx, my):
                        is_host_selected = True; is_join = False
                    if pygame.Rect(360, 125, 120, 30).collidepoint(mx, my):
                        is_join = True; is_host_selected = False
                    if pygame.Rect(300, 250, 160, 40).collidepoint(mx, my):
                        player_name = name_text.strip() or "Jugador"
                        if is_host_selected:
                            try:
                                subprocess.Popen([sys.executable, "relay_server.py"], cwd=os.getcwd())
                            except: pass
                            codigo_sala = generar_codigo()
                            ip = obtener_ip_local()
                            try:
                                requests.post(f"{RELAY_SERVER}/register", json={"codigo": codigo_sala, "ip": ip})
                            except: pass
                            node = P2PNode(player_name, True, ip)
                            jugadores = [player_name]
                            mazo = crear_mazo()
                            manos[player_name] = [mazo.pop() for _ in range(7)]
                            carta_actual = mazo.pop()
                            pila = [carta_actual]
                            state = "lobby"
                        elif is_join:
                            r = requests.get(f"{RELAY_SERVER}/sala/{code_text.strip().upper()}")
                            if r.status_code == 200:
                                ip = r.json()["ip"]
                                node = P2PNode(player_name, False, ip)
                                jugadores = []
                                state = "lobby"

                if event.type == pygame.KEYDOWN:
                    if active_name:
                        if event.key == pygame.K_BACKSPACE:
                            name_text = name_text[:-1]
                        else:
                            name_text += event.unicode
                    elif active_code:
                        if event.key == pygame.K_BACKSPACE:
                            code_text = code_text[:-1]
                        else:
                            code_text += event.unicode
        elif state == "lobby":
            draw_text(f"Código de sala: {codigo_sala}", 50, 10)
            draw_text("Jugadores:", 50, 50)
            for i, name in enumerate(jugadores):
                draw_text(f"{i+1}. {name}", 70, 80 + i * 30)

            draw_text("Chat:", 500, 50)
            for i, msg in enumerate(chat_messages[-10:]):
                draw_text(msg, 500, 80 + i * 20)
            pygame.draw.rect(screen, (255, 255, 255), (500, 300, 250, 30), 2)
            draw_text(chat_input + "_", 505, 305)

            if node.is_host:
                pygame.draw.rect(screen, (0, 150, 0), (300, 500, 200, 40))
                draw_text("Iniciar partida", 330, 510)

            for m in node.get_messages():
                if m["type"] == "join":
                    jugadores.append(m["name"])
                    manos[m["name"]] = []
                elif m["type"] == "chat":
                    chat_messages.append(m["msg"])

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); return
                if event.type == pygame.MOUSEBUTTONDOWN and node.is_host:
                    if pygame.Rect(300, 500, 200, 40).collidepoint(event.pos):
                        for i, conn in enumerate(node.peers):
                            conn.send(json.dumps({
                                "type": "start_game",
                                "players": jugadores + [f"Jugador{i+2}"],
                                "mano": [mazo.pop() for _ in range(7)],
                                "carta_actual": carta_actual
                            }).encode())
                        state = "game"

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if chat_input.strip():
                            mensaje = f"{player_name}: {chat_input.strip()}"
                            chat_messages.append(mensaje)
                            node.send_to_all({"type": "chat", "msg": mensaje})
                            chat_input = ""
                    elif event.key == pygame.K_BACKSPACE:
                        chat_input = chat_input[:-1]
                    else:
                        chat_input += event.unicode
        elif state == "game":
            screen.fill((30, 30, 30))
            draw_text(f"Carta actual: {carta_actual}", 50, 20)
            draw_text(f"Turno actual: {jugadores[turno_actual]}", 600, 20)
            draw_text("Tu mano:", 50, 60)

            card_rects = []
            for i, carta in enumerate(manos[player_name]):
                x = 70 + (i % 8) * 90
                y = 100 + (i // 8) * 60
                rect = pygame.Rect(x, y, 80, 50)
                color = obtener_color_rgb(carta) if carta_valida(carta, carta_actual) else (80, 80, 80)
                pygame.draw.rect(screen, color, rect)
                pygame.draw.rect(screen, (255, 255, 255), rect, 2)
                draw_centered_text(carta, rect)
                card_rects.append((rect, carta))

            robar_rect = pygame.Rect(70, HEIGHT - 100, 160, 40)
            pygame.draw.rect(screen, (200, 50, 50), robar_rect)
            pygame.draw.rect(screen, (255, 255, 255), robar_rect, 2)
            draw_text("Robar carta", robar_rect.x + 20, robar_rect.y + 10)

            draw_text("Chat:", 600, 100)
            for i, msg in enumerate(chat_messages[-6:]):
                draw_text(msg, 400, 130 + i * 20)

            for m in node.get_messages():
                if m["type"] == "jugada" and m["jugador"] != player_name:
                    carta_actual = m["carta"]
                    pila.append(carta_actual)
                    chat_messages.append(f"{m['jugador']} jugó {m['carta']}")
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); return
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    if robar_rect.collidepoint(mx, my) and jugadores[turno_actual] == player_name:
                        reciclar_mazo(mazo, pila)
                        if mazo:
                            nueva = mazo.pop()
                            manos[player_name].append(nueva)
                            chat_messages.append(f"{player_name} robó una carta.")
                    for rect, carta in card_rects:
                        if rect.collidepoint(mx, my) and jugadores[turno_actual] == player_name:
                            if carta_valida(carta, carta_actual):
                                carta_actual = carta
                                pila.append(carta)
                                node.send_to_all({
                                    "type": "jugada",
                                    "carta": carta,
                                    "jugador": player_name
                                })
                                manos[player_name].remove(carta)
                                chat_messages.append(f"{player_name} jugó {carta}")
                                efecto = carta.split(" ", 1)[-1] if " " in carta else carta
                                if efecto == "+2":
                                    turno_siguiente = (turno_actual + 1) % len(jugadores)
                                    reciclar_mazo(mazo, pila)
                                    for _ in range(2):
                                        if mazo:
                                            manos[jugadores[turno_siguiente]].append(mazo.pop())
                                    chat_messages.append(f"{jugadores[turno_siguiente]} robó 2 cartas.")
                                    turno_actual = (turno_actual + 2) % len(jugadores)
                                elif efecto == "Salto":
                                    chat_messages.append(f"{jugadores[(turno_actual + 1) % len(jugadores)]} fue saltado.")
                                    turno_actual = (turno_actual + 2) % len(jugadores)
                                elif efecto == "Reversa":
                                    jugadores.reverse()
                                    turno_actual = 1 if len(jugadores) > 2 else (turno_actual + 1) % len(jugadores)
                                elif "Comodín +4" in carta:
                                    color_escogido = seleccionar_color()
                                    carta_actual = f"{color_escogido} Comodín +4"
                                    turno_siguiente = (turno_actual + 1) % len(jugadores)
                                    reciclar_mazo(mazo, pila)
                                    for _ in range(4):
                                        if mazo:
                                            manos[jugadores[turno_siguiente]].append(mazo.pop())
                                    chat_messages.append(f"{jugadores[turno_siguiente]} robó 4 cartas.")
                                    turno_actual = (turno_actual + 1) % len(jugadores)
                                elif "Comodín" in carta:
                                    color_escogido = seleccionar_color()
                                    carta_actual = f"{color_escogido} Comodín"
                                    turno_actual = (turno_actual + 1) % len(jugadores)
                                else:
                                    turno_actual = (turno_actual + 1) % len(jugadores)
                            else:
                                chat_messages.append(f"{carta} no se puede jugar.")
        pygame.display.flip()

if __name__ == "__main__":
    main()
