import pickle
import os

def convertir_a_ascii_tokens(cadena: str) -> list:
    """
    Convierte una cadena como 'x + y' en tokens ASCII como ['120', '43', '121']
    Ignora espacios y tabulaciones.
    """
    ascii_tokens = []
    for ch in cadena:
        if ch in [' ', '\t', '\n', '\r']:
            continue  # ignorar espacios
        ascii_tokens.append(str(ord(ch)))
    return ascii_tokens

def simular_afd_tokens(afd_dict, tokens, debug=True):
    """
    Simula el AFD utilizando una lista de tokens en formato ASCII (ej: ['120', '43', '121']).

    Parámetros:
        afd_dict (dict): Diccionario del AFD
        tokens (list[str]): Lista de tokens en ASCII como strings
        debug (bool): Mostrar trazado paso a paso o no

    Retorna:
        bool: True si la cadena es aceptada, False si no
    """
    estado_actual = afd_dict['initial']
    transiciones = afd_dict['transitions']
    aceptacion = set(afd_dict['accepted'])

    if debug:
        print(f"➡️  Estado inicial: {estado_actual}")
        print(f"📥 Tokens de entrada: {tokens}")

    for token in tokens:
        if debug:
            print(f"🔸 Token: {token}")

        if estado_actual not in transiciones or token not in transiciones[estado_actual]:
            if debug:
                print(f"❌ No hay transición desde '{estado_actual}' con '{token}'")
            return False

        siguiente_estado = transiciones[estado_actual][token]
        if debug:
            print(f"➡️  Transición: {estado_actual} --{token}--> {siguiente_estado}")
        estado_actual = siguiente_estado

    if estado_actual in aceptacion:
        if debug:
            print(f"✅ Cadena aceptada. Estado final: {estado_actual}")
        return True
    else:
        if debug:
            print(f"❌ Cadena rechazada. Estado final: {estado_actual} no es de aceptación.")
        return False

def simular_afd_desde_texto(ruta_pickle, cadena_texto, debug=True):
    """
    Carga el AFD y simula una cadena normal (tipo 'x+y') convirtiéndola a tokens ASCII.

    Parámetros:
        ruta_pickle (str): Ruta del archivo .pkl
        cadena_texto (str): Cadena legible para el usuario
        debug (bool): Mostrar recorrido completo

    Retorna:
        bool: True si aceptada, False si no
    """
    if not os.path.exists(ruta_pickle):
        print(f"❌ El archivo no existe: {ruta_pickle}")
        return False

    try:
        with open(ruta_pickle, 'rb') as f:
            afd = pickle.load(f)
        ascii_tokens = convertir_a_ascii_tokens(cadena_texto)
        return simular_afd_tokens(afd, ascii_tokens, debug)
    except Exception as e:
        print(f"❌ Error al simular el AFD: {e}")
        return False