def leer_archivo(ruta):
    """
    Lee y retorna el contenido completo de un archivo.
    """
    with open(ruta, 'r', encoding='utf-8') as f:
        contenido = f.read()
    return contenido

def remove_comments(texto):
    """
    Elimina comentarios delimitados por (* y *) recorriendo el texto carácter a carácter.
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
                i += 1
        else:
            resultado += texto[i]
            i += 1
    return resultado

def skip_whitespace(line, i):
    """
    Avanza el índice 'i' mientras haya espacios, tabs o saltos de línea.
    Retorna el nuevo índice.
    """
    while i < len(line) and line[i] in [' ', '\t', '\n', '\r']:
        i += 1
    return i

def parse_definiciones_char_by_char(lines):
    """
    Busca líneas que empiecen con 'let' y extrae:
       let <ident> = <expresión>
    sin usar split, de manera carácter a carácter.
    Retorna un diccionario {ident: expresion}.
    """
    definiciones = {}

    for line in lines:
        i = 0
        # Saltar espacios en blanco iniciales
        i = skip_whitespace(line, i)
        if i >= len(line):
            continue

        # Verificar si empieza con "let"
        # (sin usar line.startswith('let'), lo hacemos manual)
        if i + 3 <= len(line) and line[i:i+3] == "let":
            i += 3
            # Saltar espacios
            i = skip_whitespace(line, i)

            # 1) Leer identificador hasta espacio, '=' o fin de línea
            inicio_ident = i
            while i < len(line):
                c = line[i]
                if c.isspace() or c == '=':
                    break
                i += 1
            nombre = line[inicio_ident:i]

            # Saltar espacios
            i = skip_whitespace(line, i)

            # 2) Esperar un '='
            if i < len(line) and line[i] == '=':
                i += 1  # saltar '='
            # Saltar espacios
            i = skip_whitespace(line, i)

            # 3) El resto de la línea es la expresión
            expresion = ""
            while i < len(line):
                expresion += line[i]
                i += 1

            # Guardar en el diccionario
            definiciones[nombre] = expresion

    return definiciones

def parse_reglas_char_by_char(lines):
    """
    Busca la línea que empieza con 'rule' y a partir de ahí
    interpreta cada línea como una regla:
        regexp { action }
    o bien:
        regexp
    También maneja líneas que empiezan con '|'.
    Retorna una lista de reglas (dict con 'expresion' y 'accion').
    """
    reglas = []
    modo_reglas = False

    for line in lines:
        i = 0
        i = skip_whitespace(line, i)
        if i >= len(line):
            continue

        # Verificar si la línea empieza con "rule"
        if not modo_reglas:
            # Sin usar startswith:
            if line[i:i+4] == "rule":
                modo_reglas = True
            continue

        # Ya estamos en modo reglas
        # 1) Saltar '|' si aparece
        if line[i] == '|':
            i += 1
            i = skip_whitespace(line, i)

        # Si tras saltar espacios no queda nada, seguimos
        if i >= len(line):
            continue

        # 2) Extraer la parte de expresión hasta '{' (o fin de línea)
        expresion = ""
        accion = None
        brace_index = -1

        # Buscamos manualmente '{'
        j = i
        while j < len(line):
            if line[j] == '{':
                brace_index = j
                break
            j += 1

        if brace_index == -1:
            # No se encontró '{', así que todo es expresión
            expresion = line[i:].rstrip('\n')
        else:
            # Expresión es lo que hay antes de '{'
            expresion = line[i:brace_index]
            # Extraemos la acción dentro de '{...}'
            # y lo que quede después, lo ignoramos
            # (carácter a carácter, sin split)
            j = brace_index + 1
            accion_temp = ""
            llaves_cerradas = False
            while j < len(line):
                if line[j] == '}':
                    llaves_cerradas = True
                    break
                accion_temp += line[j]
                j += 1
            # Convertimos la acción en un string final (sin la '}')
            if llaves_cerradas:
                accion = accion_temp.strip()

        reglas.append({
            "expresion": expresion.strip(),
            "accion": accion
        })

    return reglas

def parse_yal_config(texto):
    """
    Procesa el archivo YAL (sin usar split ni re):
      1) Elimina comentarios
      2) Separa en líneas
      3) Extrae definiciones con parse_definiciones_char_by_char
      4) Extrae reglas con parse_reglas_char_by_char
    """
    texto_sin_comentarios = remove_comments(texto)

    # Convertir a lista de líneas manualmente (carácter a carácter)
    # Python normal usaría .splitlines(), pero aquí te muestro cómo
    # hacerlo sin 'split'. Sin embargo, es bastante estándar permitir .splitlines().
    lines = []
    current_line = ""
    for ch in texto_sin_comentarios:
        if ch == '\n':
            lines.append(current_line)
            current_line = ""
        else:
            current_line += ch
    # Agregar la última línea si existe
    if current_line:
        lines.append(current_line)

    definiciones = parse_definiciones_char_by_char(lines)
    reglas = parse_reglas_char_by_char(lines)
    return {
        "definiciones": definiciones,
        "reglas": reglas
    }

# ----------------------------------------------------------------
# Expansión de rangos, identificadores y limpieza de paréntesis
# (igual que antes, sin usar re ni split)
# ----------------------------------------------------------------

def expand_rangos(expresion):
    """
    Expande los rangos en expresiones que usan corchetes, carácter a carácter.
    """
    resultado = ""
    i = 0
    while i < len(expresion):
        if expresion[i] == '[':
            j = expresion.find(']', i)
            if j == -1:
                # No se encuentra el cierre, se agrega lo restante de forma literal.
                resultado += expresion[i:]
                break
            contenido = expresion[i+1:j]
            if contenido.startswith('^'):
                # Negación, no se expande
                expanded = '[' + contenido + ']'
            else:
                tokens = []
                k = 0
                while k < len(contenido):
                    if contenido[k] in ["'", '"']:
                        # Literal con comillas
                        quote_char = contenido[k]
                        k += 1
                        literal = ""
                        while k < len(contenido) and contenido[k] != quote_char:
                            if contenido[k] == '\\' and (k+1 < len(contenido)):
                                seq = contenido[k:k+2]
                                if seq == '\\t':
                                    literal += '\t'
                                elif seq == '\\n':
                                    literal += '\n'
                                else:
                                    literal += contenido[k+1]
                                k += 2
                            else:
                                literal += contenido[k]
                                k += 1
                        if k < len(contenido) and contenido[k] == quote_char:
                            k += 1
                        # Ver si hay rango 'A'-'Z'
                        if k < len(contenido) and contenido[k] == '-' and (k+1 < len(contenido)) and contenido[k+1] in ["'", '"']:
                            k += 1
                            next_quote = contenido[k]
                            k += 1
                            literal2 = ""
                            while k < len(contenido) and contenido[k] != next_quote:
                                if contenido[k] == '\\' and (k+1 < len(contenido)):
                                    seq = contenido[k:k+2]
                                    if seq == '\\t':
                                        literal2 += '\t'
                                    elif seq == '\\n':
                                        literal2 += '\n'
                                    else:
                                        literal2 += contenido[k+1]
                                    k += 2
                                else:
                                    literal2 += contenido[k]
                                    k += 1
                            if k < len(contenido) and contenido[k] == next_quote:
                                k += 1
                            # Expandir si son un solo caracter
                            if len(literal) == 1 and len(literal2) == 1:
                                for c in range(ord(literal), ord(literal2) + 1):
                                    tokens.append(chr(c))
                            else:
                                tokens.append(literal)
                                tokens.append('-')
                                tokens.append(literal2)
                        else:
                            tokens.append(literal)
                    elif contenido[k].isspace():
                        k += 1
                    elif (k+2 < len(contenido) and contenido[k+1] == '-' and contenido[k] not in ["'", '"']):
                        # Rango tipo 0-9
                        start = contenido[k]
                        end = contenido[k+2]
                        for c in range(ord(start), ord(end) + 1):
                            tokens.append(chr(c))
                        k += 3
                    else:
                        tokens.append(contenido[k])
                        k += 1
                # Si todo era un literal, no lo expandimos, etc.
                # Convertir tokens en unión
                escaped_tokens = [tok.encode('unicode_escape').decode('utf-8') for tok in tokens]
                expanded = "(" + "|".join(escaped_tokens) + ")"
            resultado += expanded
            i = j + 1
        else:
            resultado += expresion[i]
            i += 1
    return resultado

def expand_identificadores(expresion, definiciones):
    """
    Reemplaza recursivamente los identificadores (definidos con let)
    por sus expresiones correspondientes, carácter a carácter.
    """
    resultado = ""
    i = 0
    while i < len(expresion):
        ch = expresion[i]
        if ch in ["'", '"']:
            # Copiar literal hasta la comilla de cierre
            quote_char = ch
            resultado += ch
            i += 1
            while i < len(expresion):
                resultado += expresion[i]
                if expresion[i] == quote_char:
                    i += 1
                    break
                i += 1
        elif ch.isalpha() or ch == '_':
            # Leer identificador
            inicio = i
            while i < len(expresion) and (expresion[i].isalnum() or expresion[i] == '_'):
                i += 1
            token = expresion[inicio:i]
            if token in definiciones:
                subexp = expand_identificadores(definiciones[token], definiciones)
                resultado += "(" + subexp + ")"
            else:
                resultado += token
        else:
            resultado += ch
            i += 1
    return resultado

def limpiar_parentesis(expresion):
    """
    Elimina paréntesis externos redundantes que envuelven toda la expresión,
    sin usar split ni re.
    """
    while expresion.startswith("(") and expresion.endswith(")"):
        count = 0
        redundant = True
        for i, char in enumerate(expresion):
            if char == '(':
                count += 1
            elif char == ')':
                count -= 1
            if count == 0 and i < len(expresion) - 1:
                redundant = False
                break
        if redundant:
            expresion = expresion[1:-1]
        else:
            break
    return expresion

# ------------------------------------------------------
# MAIN de ejemplo
# ------------------------------------------------------
if __name__ == '__main__':
    ruta_yal = "slr-4.yal"  # Ajusta con tu archivo
    contenido = leer_archivo(ruta_yal)
    config = parse_yal_config(contenido)

    print("Definiciones encontradas:")
    for nombre, expresion in config["definiciones"].items():
        print(f"{nombre} = {expresion}")
        exp_ids = expand_identificadores(expresion, config["definiciones"])
        expanded = expand_rangos(exp_ids)
        limpio = limpiar_parentesis(expanded)
        print(f"  Expandidas: {expanded}")
        print(f"  Limpio: {limpio}\n")

    print("Reglas encontradas:")
    for regla in config["reglas"]:
        print(f"Expresión: {regla['expresion']}")
        print(f"  Acción: {regla['accion']}")
        exp_ids = expand_identificadores(regla["expresion"], config["definiciones"])
        expanded = expand_rangos(exp_ids)
        limpio = limpiar_parentesis(expanded)
        print(f"  Expandidas: {expanded}")
        print(f"  Limpio: {limpio}")
        print("-" * 40)