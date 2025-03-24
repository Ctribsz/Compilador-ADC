import pickle
import os

def cargar_afd(ruta):
    if not os.path.exists(ruta):
        raise FileNotFoundError(f"Archivo no encontrado: {ruta}")
    with open(ruta, 'rb') as f:
        return pickle.load(f)

def ascii_de(char):
    return str(ord(char))

def lexer(cadena, afd_dict, mapping, debug=True):
    """
    Analiza una cadena y retorna una lista de tokens usando el AFD minimizado y el mapping.

    Parámetros:
        cadena (str): la cadena a analizar (ej: "x+y")
        afd_dict (dict): el AFD cargado desde el pickle
        mapping (dict): diccionario que asocia tags (#1001, etc.) con acciones (ej: return ID)
        debug (bool): si True, muestra el recorrido por el AFD

    Retorna:
        list: lista de tuplas (token, lexema)
    """
    pos = 0
    tokens = []
    while pos < len(cadena):
        estado_actual = afd_dict['initial']
        transiciones = afd_dict['transitions']
        aceptacion = set(afd_dict['accepted'])

        ultimo_estado_final = None
        ultimo_token_pos = pos
        recorrido = []

        i = pos
        while i < len(cadena):
            char = cadena[i]
            ascii_token = ascii_de(char)
            if estado_actual in transiciones and ascii_token in transiciones[estado_actual]:
                siguiente = transiciones[estado_actual][ascii_token]
                recorrido.append((estado_actual, ascii_token, siguiente))
                estado_actual = siguiente
                i += 1
                if estado_actual in aceptacion:
                    ultimo_estado_final = estado_actual
                    ultimo_token_pos = i
            else:
                break

        if ultimo_estado_final is None:
            raise ValueError(f"❌ Error léxico: símbolo inesperado '{cadena[pos]}' en posición {pos}")

        lexema = cadena[pos:ultimo_token_pos]
        token = None

        # Buscar el tag correspondiente al estado final
        for tag, accion in mapping.items():
            if accion is not None and tag[1:] == str(ord(lexema[-1])):
                token = accion
                break

        # Si no se encuentra por símbolo final, usar el estado directamente
        if token is None:
            for tag, accion in mapping.items():
                if accion and tag[1:] in afd_dict['transitions'].get(ultimo_estado_final, {}):
                    token = accion
                    break

        if token is None:
            token = 'UNKNOWN'

        tokens.append((token, lexema))
        if debug:
            print(f"✔️ Token: {token}, lexema: '{lexema}'")
            for est, sym, sig in recorrido:
                print(f"   {est} --{sym}--> {sig}")
        pos = ultimo_token_pos

    return tokens