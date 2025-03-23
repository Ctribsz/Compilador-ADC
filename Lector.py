def obtener_alfabeto():
    """Retorna el conjunto de caracteres ASCII imprimibles (del 32 al 126)."""
    return set(chr(i) for i in range(32, 127))

def leer_archivo(ruta):
    """Lee y retorna el contenido completo de un archivo."""
    with open(ruta, 'r', encoding='utf-8') as f:
        return f.read()

def remove_comments(texto):
    """
    Elimina comentarios delimitados por (* y *) recorriendo el texto carácter a carácter.
    """
    resultado = ""
    i = 0
    while i < len(texto):
        if texto[i] == '(' and i + 1 < len(texto) and texto[i+1] == '*':
            i += 2  # Salta "(*"
            while i < len(texto):
                if texto[i] == '*' and i + 1 < len(texto) and texto[i+1] == ')':
                    i += 2
                    break
                else:
                    i += 1
        else:
            resultado += texto[i]
            i += 1
    return resultado

def skip_whitespace(line, i):
    """Avanza el índice 'i' mientras haya espacios, tabs o saltos de línea."""
    while i < len(line) and line[i] in [' ', '\t', '\n', '\r']:
        i += 1
    return i

def parse_definiciones_char_by_char(lines):
    """
    Extrae las definiciones (let <ident> = <expresión>) del archivo YAL
    de forma manual, carácter a carácter.
    Retorna un diccionario {ident: expresión}.
    """
    definiciones = {}
    for line in lines:
        i = skip_whitespace(line, 0)
        if i >= len(line):
            continue
        if i + 3 <= len(line) and line[i:i+3] == "let":
            i += 3
            i = skip_whitespace(line, i)
            inicio_ident = i
            while i < len(line) and not line[i].isspace() and line[i] != '=':
                i += 1
            nombre = line[inicio_ident:i]
            i = skip_whitespace(line, i)
            if i < len(line) and line[i] == '=':
                i += 1
            i = skip_whitespace(line, i)
            expresion = ""
            while i < len(line):
                expresion += line[i]
                i += 1
            definiciones[nombre] = expresion
    return definiciones

def parse_reglas_char_by_char(lines):
    """
    Extrae la sección de reglas del archivo YAL, carácter a carácter.
    Cada regla tiene la forma:
         regexp { acción }
    o solo la regexp.
    Retorna una lista de diccionarios con 'expresion' y 'accion'.
    """
    reglas = []
    modo_reglas = False
    for line in lines:
        i = skip_whitespace(line, 0)
        if i >= len(line):
            continue
        if not modo_reglas:
            if line[i:i+4] == "rule":
                modo_reglas = True
            continue
        if line[i] == '|':
            i += 1
            i = skip_whitespace(line, i)
        if i >= len(line):
            continue
        expresion = ""
        accion = None
        j = i
        brace_index = -1
        while j < len(line):
            if line[j] == '{':
                brace_index = j
                break
            j += 1
        if brace_index == -1:
            expresion = line[i:].rstrip('\n')
        else:
            expresion = line[i:brace_index]
            j = brace_index + 1
            accion_temp = ""
            llave_cerrada = False
            while j < len(line):
                if line[j] == '}':
                    llave_cerrada = True
                    break
                accion_temp += line[j]
                j += 1
            if llave_cerrada:
                accion = accion_temp.strip()
        reglas.append({"expresion": expresion.strip(), "accion": accion})
    return reglas

def parse_yal_config(texto):
    """
    Procesa el archivo YAL:
      1) Elimina comentarios.
      2) Separa el texto en líneas manualmente.
      3) Extrae definiciones y reglas.
    Retorna un diccionario con 'definiciones' y 'reglas'.
    """
    texto_sin_comentarios = remove_comments(texto)
    lines = []
    current_line = ""
    for ch in texto_sin_comentarios:
        if ch == '\n':
            lines.append(current_line)
            current_line = ""
        else:
            current_line += ch
    if current_line:
        lines.append(current_line)
    definiciones = parse_definiciones_char_by_char(lines)
    reglas = parse_reglas_char_by_char(lines)
    return {"definiciones": definiciones, "reglas": reglas}

# Función auxiliar para separar una cadena manualmente por un delimitador.
def manual_split(expr, delimiter):
    parts = []
    current = ""
    for ch in expr:
        if ch == delimiter:
            parts.append(current.strip())
            current = ""
        else:
            current += ch
    if current:
        parts.append(current.strip())
    return parts

def find_top_level_hash(expr):
    """
    Busca el operador '#' a nivel superior (fuera de comillas y paréntesis)
    y retorna su índice o -1 si no lo encuentra.
    """
    level = 0
    in_quote = False
    quote_char = ''
    for i, ch in enumerate(expr):
        if in_quote:
            if ch == quote_char:
                in_quote = False
            continue
        if ch in ["'", '"']:
            in_quote = True
            quote_char = ch
        elif ch == '(':
            level += 1
        elif ch == ')':
            level -= 1
        elif ch == '#' and level == 0:
            return i
    return -1

def expand_charset(content):
    """
    Procesa el contenido de un conjunto (ej. "a-z") y retorna un set de caracteres.
    """
    tokens = []
    k = 0
    while k < len(content):
        if content[k] in ["'", '"']:
            quote_char = content[k]
            k += 1
            literal = ""
            while k < len(content) and content[k] != quote_char:
                if content[k] == '\\' and k+1 < len(content):
                    seq = content[k:k+2]
                    if seq == '\\t':
                        literal += '\t'
                    elif seq == '\\n':
                        literal += '\n'
                    else:
                        literal += content[k+1]
                    k += 2
                else:
                    literal += content[k]
                    k += 1
            if k < len(content) and content[k] == quote_char:
                k += 1
            tokens.append(literal)
        elif content[k].isspace():
            k += 1
        elif (k+2 < len(content) and content[k+1] == '-' and content[k] not in ["'", '"']):
            start = content[k]
            end = content[k+2]
            for c in range(ord(start), ord(end)+1):
                tokens.append(chr(c))
            k += 3
        else:
            tokens.append(content[k])
            k += 1
    return set(tokens)

def expand_rangos(expresion):
    """
    Expande rangos y conjuntos en la expresión.
    - Si la expresión es "_" se reemplaza por el alfabeto completo.
    - Para [^...] se calcula la diferencia entre el alfabeto y el conjunto.
    - Si se encuentra el operador diferencia '#' a nivel superior,
      se expande la diferencia entre la parte izquierda y la derecha.
    """
    if expresion == "_":
        ALPHABET = obtener_alfabeto()
        union = "|".join(sorted(ALPHABET))
        return "(" + union + ")"
    
    expresion = limpiar_parentesis(expresion)
    diff_index = find_top_level_hash(expresion)
    if diff_index != -1:
        left_expr = expresion[:diff_index]
        right_expr = expresion[diff_index+1:]
        left_expanded = expand_rangos(left_expr)
        right_expanded = expand_rangos(right_expr)
        left_clean = limpiar_parentesis(left_expanded)
        right_clean = limpiar_parentesis(right_expanded)
        left_parts = [p.strip(" ()") for p in manual_split(left_clean, '|')]
        right_parts = [p.strip(" ()") for p in manual_split(right_clean, '|')]
        diff_set = sorted(set(left_parts) - set(right_parts))
        return "(" + "|".join(diff_set) + ")"
    
    resultado = ""
    i = 0
    while i < len(expresion):
        if expresion[i] == '[':
            j = expresion.find(']', i)
            if j == -1:
                resultado += expresion[i:]
                break
            contenido = expresion[i+1:j]
            if contenido.startswith('^'):
                char_set = expand_charset(contenido[1:])
                ALPHABET = obtener_alfabeto()
                diff = ALPHABET - char_set
                union = "|".join(sorted(diff))
                expanded = "(" + union + ")"
            else:
                tokens = []
                k = 0
                while k < len(contenido):
                    if contenido[k] in ["'", '"']:
                        quote_char = contenido[k]
                        k += 1
                        literal = ""
                        while k < len(contenido) and contenido[k] != quote_char:
                            if contenido[k] == '\\' and k+1 < len(contenido):
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
                        if k < len(contenido) and contenido[k] == '-' and (k+1 < len(contenido)) and contenido[k+1] in ["'", '"']:
                            k += 1
                            next_quote = contenido[k]
                            k += 1
                            literal2 = ""
                            while k < len(contenido) and contenido[k] != next_quote:
                                if contenido[k] == '\\' and k+1 < len(contenido):
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
                            if len(literal) == 1 and len(literal2) == 1:
                                for c in range(ord(literal), ord(literal2)+1):
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
                        start = contenido[k]
                        end = contenido[k+2]
                        for c in range(ord(start), ord(end)+1):
                            tokens.append(chr(c))
                        k += 3
                    else:
                        tokens.append(contenido[k])
                        k += 1
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
            inicio = i
            while i < len(expresion) and (expresion[i].isalnum() or expresion[i] == '_'):
                i += 1
            token = expresion[inicio:i]
            if token in definiciones:
                subexp = expand_identificadores(definiciones[token], definiciones)
                resultado += "(" + subexp + ")"
            else:
                if token == "_":
                    ALPHABET = obtener_alfabeto()
                    union = "|".join(sorted(ALPHABET))
                    resultado += "(" + union + ")"
                else:
                    resultado += token
        else:
            resultado += ch
            i += 1
    return resultado

def limpiar_parentesis(expresion):
    """
    Elimina paréntesis externos redundantes que envuelven toda la expresión,
    carácter a carácter.
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

def expand_optionals(expr):
    """
    (No se aplicará transformación a '?' para que se conserve tal cual).
    Retorna la expresión sin modificar.
    """
    return expr

# MAIN
if __name__ == '__main__':
    ruta_yal = "config.yal"  # Cambia este nombre por el de tu archivo YAL.
    contenido = leer_archivo(ruta_yal)
    config = parse_yal_config(contenido)

    print("Definiciones encontradas:")
    for nombre, expresion in config["definiciones"].items():
        print(f"{nombre} = {expresion}")
        exp_ids = expand_identificadores(expresion, config["definiciones"])
        expanded = expand_rangos(exp_ids)
        limpio = limpiar_parentesis(expanded)
        # Aquí no aplicamos expand_optionals para que '?' se mantenga igual.
        final = limpio
        print(f"  Expandidas: {expanded}")
        print(f"  Limpio: {limpio}")
        print(f"  Final con opcionales: {final}\n")

    print("Reglas encontradas:")
    for regla in config["reglas"]:
        print(f"Expresión: {regla['expresion']}")
        print(f"  Acción: {regla['accion']}")
        exp_ids = expand_identificadores(regla["expresion"], config["definiciones"])
        expanded = expand_rangos(exp_ids)
        limpio = limpiar_parentesis(expanded)
        final = limpio
        print(f"  Expandidas: {expanded}")
        print(f"  Limpio: {limpio}")
        print(f"  Final con opcionales: {final}")
        print("-" * 40)