import pickle
import os

def cargar_afd(ruta):
    if not os.path.exists(ruta):
        raise FileNotFoundError(f"Archivo no encontrado: {ruta}")
    with open(ruta, 'rb') as f:
        return pickle.load(f)

def ascii_de(char):
    return str(ord(char))

def lexer(cadena, afd_dict, mapping, output_file='salida_logs.txt', debug=True):
    pos = 0
    tokens = []
    with open(output_file, 'w', encoding='utf-8') as out:
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
                ascii_token_char = str(ord(char))
                if estado_actual in transiciones and ascii_token_char in transiciones[estado_actual]:
                    siguiente = transiciones[estado_actual][ascii_token_char]
                    recorrido.append((estado_actual, ascii_token_char, siguiente))
                    estado_actual = siguiente
                    i += 1
                    if estado_actual in aceptacion:
                        ultimo_estado_final = estado_actual
                        ultimo_token_pos = i
                else:
                    break

            if ultimo_estado_final is None:
                out.write(f"❌ Error léxico: símbolo inesperado '{cadena[pos]}' en posición {pos}\n")
                pos = pos + 1
                continue
            
            lexema = cadena[pos:ultimo_token_pos]
            if ultimo_estado_final in afd_dict.get('state_tags', {}):
                tag = afd_dict['state_tags'][ultimo_estado_final]
                token = mapping.get(tag, 'UNKNOWN')
            else:
                token = 'UNKNOWN'

            tokens.append((token, lexema))
            if debug:
                out.write(f"✔️ Token: {token}, lexema: '{lexema}'\n")
            pos = ultimo_token_pos

    return tokens