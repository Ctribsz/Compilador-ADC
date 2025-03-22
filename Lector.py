def expand_rangos(expresion):
    """
    Expande los rangos en expresiones que usan corchetes.
    Por ejemplo, convierte:
       [0-9]     -> (0|1|2|3|4|5|6|7|8|9)
       [a-zA-Z]  -> (a|b|...|z|A|B|...|Z)
    Si se detecta una negación (p.ej. [^a-z]), no se expande y se deja tal cual.
    """
    resultado = ""
    i = 0
    while i < len(expresion):
        if expresion[i] == '[':
            j = expresion.find(']', i)
            if j == -1:
                # Si no se encuentra cierre, se agrega el resto literal
                resultado += expresion[i:]
                break
            contenido = expresion[i+1:j]
            # Si se trata de una negación, lo dejamos sin expandir
            if contenido.startswith('^'):
                expanded = '[' + contenido + ']'
            else:
                union_parts = []
                k = 0
                while k < len(contenido):
                    # Si se detecta un rango del tipo X-Y
                    if k+2 < len(contenido) and contenido[k+1] == '-':
                        start = contenido[k]
                        end = contenido[k+2]
                        # Generamos todos los caracteres entre start y end (inclusive)
                        for c in range(ord(start), ord(end) + 1):
                            union_parts.append(chr(c))
                        k += 3
                    else:
                        # Si no hay guión, se toma el carácter individual
                        union_parts.append(contenido[k])
                        k += 1
                expanded = "(" + "|".join(union_parts) + ")"
            resultado += expanded
            i = j + 1
        else:
            resultado += expresion[i]
            i += 1
    return resultado

# ------------------------------------------------------
# Ejemplo de uso: Lectura y expansión de rangos en el archivo YAL
# ------------------------------------------------------
def leer_archivo(ruta):
    """Lee y retorna el contenido completo de un archivo."""
    with open(ruta, 'r', encoding='utf-8') as f:
        return f.read()

def remove_comments(texto):
    """
    Elimina comentarios delimitados por (* y *).
    Se recorre el texto carácter a carácter.
    """
    resultado = ""
    i = 0
    while i < len(texto):
        if texto[i] == '(' and i + 1 < len(texto) and texto[i + 1] == '*':
            i += 2  # Salta '(*'
            while i < len(texto):
                if texto[i] == '*' and i + 1 < len(texto) and texto[i + 1] == ')':
                    i += 2
                    break
                else:
                    i += 1
        else:
            resultado += texto[i]
            i += 1
    return resultado

def parse_definiciones(lineas):
    """
    Extrae las definiciones (let <nombre> = <expresión>) del archivo YAL.
    Retorna un diccionario {nombre: expresión}.
    """
    definiciones = {}
    for linea in lineas:
        linea = linea.strip()
        if linea.startswith("let"):
            sin_let = linea[3:].strip()
            if "=" in sin_let:
                partes = sin_let.split("=", 1)
                nombre = partes[0].strip()
                expresion = partes[1].strip()
                definiciones[nombre] = expresion
    return definiciones

def parse_reglas(lineas):
    """
    Extrae la sección de reglas del archivo YAL.
    Retorna una lista de reglas (cada regla es un diccionario con 'expresion' y 'accion').
    """
    reglas = []
    modo_reglas = False
    for linea in lineas:
        linea_limpia = linea.strip()
        if not modo_reglas:
            if linea_limpia.startswith("rule"):
                modo_reglas = True
            continue
        if linea_limpia == "":
            continue
        if linea_limpia.startswith("|"):
            linea_limpia = linea_limpia[1:].strip()
        if "{" in linea_limpia:
            partes = linea_limpia.split("{", 1)
            expresion = partes[0].strip()
            accion_con_brace = partes[1]
            if "}" in accion_con_brace:
                accion = accion_con_brace.split("}", 1)[0].strip()
            else:
                accion = accion_con_brace.strip()
        else:
            expresion = linea_limpia
            accion = None
        reglas.append({
            "expresion": expresion,
            "accion": accion
        })
    return reglas

def parse_yal_config(texto):
    """
    Procesa el archivo YAL: elimina comentarios, separa en líneas, y extrae definiciones y reglas.
    Retorna un diccionario con las definiciones y una lista de reglas.
    """
    texto_sin_comentarios = remove_comments(texto)
    lineas = texto_sin_comentarios.splitlines()
    definiciones = parse_definiciones(lineas)
    reglas = parse_reglas(lineas)
    return {
        "definiciones": definiciones,
        "reglas": reglas
    }

# Ejemplo de uso:
if __name__ == '__main__':
    ruta_yal = "config.yal"  # Actualiza con la ruta a tu archivo YAL
    contenido_yal = leer_archivo(ruta_yal)
    
    config = parse_yal_config(contenido_yal)
    
    print("Definiciones encontradas:")
    for nombre, expresion in config["definiciones"].items():
        print(f"  {nombre} = {expresion}")
        expanded = expand_rangos(expresion)
        print(f"    Expandidas: {expanded}")
    
    print("\nReglas encontradas:")
    for regla in config["reglas"]:
        print(f"  Expresión: {regla['expresion']}")
        print(f"  Acción: {regla['accion']}")
        expanded = expand_rangos(regla["expresion"])
        print(f"    Expandidas: {expanded}")
        print("-" * 40)
