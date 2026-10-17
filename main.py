#Projeto L.A.I.S.S. | Laminadora Automatizada Integrada a Sistemas de Segurança
#Autores: Arthur Vaz, Emmanuel Ozorio, Giuliana Simões, Heitor Santos e Raphael Antonio

#imports
import json
import utime
from machine import Pin, PWM


#variaveis
pos = 25
p1d = None
p2d = None
p3d = None
intr = 0

#carregamento de posições salvas
POSITIONS_FILE = "position.json"

def load_positions():
    global pos, p1d, p2d, p3d
    try:
        with open(POSITIONS_FILE) as f:
            data = json.load(f)
        pos = data.get("pos", pos)
        p1d = data.get("p1d")
        p2d = data.get("p2d")
        p3d = data.get("p3d")
    except (OSError, ValueError):
        pass

def save_positions():
    data = {"pos": pos, "p1d": p1d, "p2d": p2d, "p3d": p3d}
    with open(POSITIONS_FILE, "w") as f:
        json.dump(data, f)

#pinos motor de passo
DIR_PIN = Pin(2, Pin.OUT)
STEP_PIN = Pin(3, Pin.OUT)
DIR_PIN2 = Pin(26, Pin.OUT)
STEP_PIN2 = Pin(27, Pin.OUT)
#motor 12v
IN1 = Pin(20, Pin.OUT)
IN2 = Pin(19, Pin.OUT)
ENA = PWM(Pin(22))
ENA.freq(1000)
VEL_MIN = 30
TEMPO_TROCA = 1000   # ms parado antes de poder inverter
intervalo = 50
a = VEL_MIN
ultimo = utime.ticks_ms()
rodando = None           # sentido em que está girando agora (None = parado)
ultimo_sentido = None    # último sentido em que girou
parado_desde = utime.ticks_ms()

#pinos botoes
b1 = Pin(17, Pin.IN, Pin.PULL_UP)
b2 = Pin(1, Pin.IN, Pin.PULL_UP)
p1 = Pin(10, Pin.IN, Pin.PULL_UP)
p2 = Pin(11, Pin.IN, Pin.PULL_UP)
p3 = Pin(12, Pin.IN, Pin.PULL_UP)
md = Pin(15, Pin.IN, Pin.PULL_UP)
ma =  Pin(14, Pin.IN, Pin.PULL_UP)
mr = Pin(13, Pin.IN, Pin.PULL_UP)
intb = Pin(16, Pin.IN, Pin.PULL_UP)

DEBOUNCE_MS = 30

#intertravamento insanamente foda pra krl
def intertravamento():
    global intr
    if pressed(intb):
        intr = 1

def pressed(pin):
    if pin.value() != 0:
        return False
    utime.sleep_ms(DEBOUNCE_MS)
    return pin.value() == 0

RELEASE_TIMEOUT_MS = 1000
HOLD_MS = 800   # tempo pressionado para entrar em modo de redefinição do preset

def held(pin, hold_ms=HOLD_MS):
    start = utime.ticks_ms()
    while utime.ticks_diff(utime.ticks_ms(), start) < hold_ms:
        if pin.value() == 1:
            return False
        utime.sleep_ms(5)
    return True

def wait_released(pin, timeout_ms=RELEASE_TIMEOUT_MS):
    start = utime.ticks_ms()
    while utime.ticks_diff(utime.ticks_ms(), start) < timeout_ms:
        if pin.value() == 1:
            utime.sleep_ms(DEBOUNCE_MS)
            if pin.value() == 1:
                return
        utime.sleep_ms(5)


def move_stepper(steps, direction, delay_micros):
    DIR_PIN.value(direction)
    DIR_PIN2.value(direction)
    for _ in range(steps):
        STEP_PIN.value(1)
        STEP_PIN2.value(1)
        utime.sleep_us(delay_micros)
        STEP_PIN.value(0)
        STEP_PIN2.value(0)
        utime.sleep_us(delay_micros)

def upmotor(x):
    global pos
    move_stepper(x, 0, 5000)
    pos += 25
    print("subiuuuuuuuuuuu")
    
def downmotor(x):
    global pos
    move_stepper(x, 1, 5000)
    pos -= 25
   
def preset(x):
    global pos
    if x is None:
        return
    x = max(25, min(1000, x))
    if x < pos:
        move_stepper(pos - x, 0, 5000)
        pos = x
    elif x > pos:
        move_stepper(x - pos, 1, 5000)
        pos = x
    print(pos)

def mover_motor(velocidade, sentido_avanco=True):
    duty = int(velocidade / 100 * 65535)
    IN1.value(1 if sentido_avanco else 0)
    IN2.value(0 if sentido_avanco else 1)
    ENA.duty_u16(duty)

def parar_motor():
    ENA.duty_u16(0)
    IN1.value(0)
    IN2.value(0)

def modo_preset():
    global pos, p1d, p2d, p3d
    while True:
        if pressed(b1) and pos < 1000:
            upmotor(25)
            wait_released(b1)
            print(pos)
        if pressed(b2) and pos > 25:
            downmotor(25)
            wait_released(b2)
            print(pos)
        if pressed(p1):
            p1d = pos
            save_positions()
            print("p1d", pos)
            wait_released(p1)
            break
        if pressed(p2):
            p2d = pos
            save_positions()
            print("p2d", pos)
            wait_released(p2)
            break
        if pressed(p3):
            p3d = pos
            save_positions()
            print("p3d", pos)
            wait_released(p3)
            break
        if pressed(md):
            wait_released(md)
            break

def main():
    global pos, p1d, p2d, p3d, rodando, ultimo_sentido, parado_desde, a, ultimo
    while True:
        #Regular espessura dos rolos:
        if pressed(b1) and pos < 1000:
            upmotor(25)
            wait_released(b1)
            print(pos)

        if pressed(b2) and pos > 25:
            downmotor(25)
            wait_released(b2)
            print(pos)
        #modo de pressets:
        if pressed(md):
            print("modo preset")
            wait_released(md)
            modo_preset()

        if pressed(p1):
            if p1d is None or held(p1):
                wait_released(p1)
                modo_preset()
            else:
                preset(p1d)
            wait_released(p1)
        if pressed(p2):
            if p2d is None or held(p2):
                wait_released(p2)
                modo_preset()
            else:
                preset(p2d)
            wait_released(p2)
        if pressed(p3):
            if p3d is None or held(p3):
                wait_released(p3)
                modo_preset()
            else:
                preset(p3d)
            wait_released(p3)

        #avanço e recuo da esteira:
        agora = utime.ticks_ms()
        recuando = mr.value() == 0
        avancando = ma.value() == 0

        if recuando and not avancando:
            pedido = False   # recua
        elif avancando and not recuando:
            pedido = True    # avança
        else:
            pedido = None    # nenhum ou os dois

        # Girando e o pedido mudou: para primeiro
        if rodando is not None and pedido != rodando:
            parar_motor()
            rodando = None
            parado_desde = agora
            a = VEL_MIN

        # Parado e tem pedido: verifica o intertravamento
        if rodando is None and pedido is not None:
            inversao = ultimo_sentido is not None and pedido != ultimo_sentido
            liberado = utime.ticks_diff(agora, parado_desde) >= TEMPO_TROCA
            if not inversao or liberado:
                rodando = pedido
                ultimo_sentido = pedido
                a = VEL_MIN
                ultimo = agora

        # Rampa
        if rodando is not None:
            if a < 100 and utime.ticks_diff(agora, ultimo) >= intervalo:
                a += 1
                ultimo = agora
            mover_motor(a, sentido_avanco=rodando)

#inicialização
load_positions()
main()
