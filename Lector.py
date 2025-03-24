def sp_manual(texto):
    inicio = 0
    while inicio < len(texto) and texto[inicio] in [' ', '\t', '\n', '\r']:
        inicio += 1

    fin = len(texto) - 1
    while fin >= 0 and texto[fin] in [' ', '\t', '\n', '\r']:
        fin -= 1

    return texto[inicio:fin+1] if inicio <= fin else ''

def sp_rstrip(texto, char='\n'):
    fin = len(texto)
    while fin > 0 and texto[fin-1] == char:
        fin -= 1
    return texto[:fin]

def sp_strip_chars(texto, chars=" ()"):
    inicio = 0
    while inicio < len(texto) and texto[inicio] in chars:
        inicio += 1

    fin = len(texto) - 1
    while fin >= 0 and texto[fin] in chars:
        fin -= 1

    return texto[inicio:fin+1] if inicio <= fin else ''
# ====================================

def obtener_alfabeto():
    """Retorna el conjunto de caracteres ASCII imprimibles (del 32 al 126)."""
    return set(chr(i) for i in range(32, 127))

def ascii_token(tok):
    """
    Si el token es de longitud 1, devuelve su código ASCII (en forma de string);
    de lo contrario, lo devuelve tal cual.
    """
    if len(tok) == 1:
        return str(ord(tok))
    return tok

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
            expresion = sp_rstrip(line[i:], '\n')
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
                accion = sp_manual(accion_temp)
        reglas.append({"expresion": sp_manual(expresion), "accion": accion})
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

def manual_split(expr, delimiter):
    """
    Separa manualmente una cadena por el delimitador, carácter a carácter.
    """
    parts = []
    current = ""
    for ch in expr:
        if ch == delimiter:
            parts.append(sp_manual(current))
            current = ""
        else:
            current += ch
    if current:
        parts.append(sp_manual(current))
    return parts


def expand_repetition_operators(expr: str) -> str:
    """
    Reemplaza:
    - A+ por (A)(A)*
    - A? por (A|_)
    """
    i = 0
    result = ""
    while i < len(expr):
        if expr[i] in ['+', '?'] and i > 0:
            # Extraer el operando que antecede al operador de repetición.
            prev = ""
            j = len(result) - 1
            if result[j] == ')':
                # Si termina en ')', buscar la pareja de paréntesis de apertura
                count = 1
                j -= 1
                while j >= 0:
                    if result[j] == ')':
                        count += 1
                    elif result[j] == '(':
                        count -= 1
                    if count == 0:
                        break
                    j -= 1
                prev = result[j:]
                result = result[:j]
            else:
                # Si no está entre paréntesis, se asume que el operando es de longitud 1.
                prev = result[-1]
                result = result[:-1]
            if expr[i] == '+':
                # Agrupar A y luego concatenar con (A)*
                result += "(" + prev + ")(" + prev + ")*"
            elif expr[i] == '?':
                # Agrupar A en la unión con épsilon
                result += "(" + prev + "|949)"
            i += 1
        else:
            result += expr[i]
            i += 1
    return result


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
    # Si el contenido está completamente entre comillas, procesarlo teniendo en cuenta los escapes
    if (content.startswith('"') and content.endswith('"')) or (content.startswith("'") and content.endswith("'")):
        literal = content[1:-1]
        tokens = []
        k = 0
        while k < len(literal):
            if literal[k] == '\\' and k + 1 < len(literal):
                esc = literal[k+1]
                if esc == 's':
                    tokens.append(ascii_token(' '))
                elif esc == 't':
                    tokens.append(ascii_token('\t'))
                elif esc == 'n':
                    tokens.append(ascii_token('\n'))
                else:
                    tokens.append(ascii_token(esc))
                k += 2
            else:
                tokens.append(ascii_token(literal[k]))
                k += 1
        return set(tokens)
    
    # Código original para procesar el conjunto
    tokens = []
    k = 0
    while k < len(content):
        # Procesa escapes explícitos fuera de comillas
        if content[k] == '\\' and k+1 < len(content):
            next_char = content[k+1]
            if next_char == 's':       # detecta \s → espacio
                tokens.append(ascii_token(' '))
            elif next_char == 't':     # detecta \t → tabulación
                tokens.append(ascii_token('\t'))
            elif next_char == 'n':     # detecta \n → salto de línea
                tokens.append(ascii_token('\n'))
            else:
                tokens.append(ascii_token(next_char))
            k += 2
            continue

        # Si el caracter está entre comillas, se procesa como literal
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
                    elif seq == '\\s':
                        literal += ' '
                    else:
                        literal += content[k+1]
                    k += 2
                else:
                    literal += content[k]
                    k += 1
            if k < len(content) and content[k] == quote_char:
                k += 1
            for char in literal:
                tokens.append(ascii_token(char))
            continue

        # Manejo de espacios y rangos
        elif content[k].isspace():
            tokens.append(ascii_token(content[k]))
            k += 1
            continue
        elif (k+2 < len(content) and content[k+1] == '-' and content[k] not in ["'", '"']):
            start = content[k]
            end = content[k+2]
            for c in range(ord(start), ord(end)+1):
                tokens.append(chr(c))
            k += 3
            continue
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
    Los tokens se convierten a código ASCII usando ascii_token.
    """
    if expresion == "_":
        ALPHABET = obtener_alfabeto()
        union = "|".join(tok for tok in sorted(ascii_token(x) for x in ALPHABET) if tok)
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
        left_parts = [sp_strip_chars(p, " ()") for p in manual_split(left_clean, '|')]
        right_parts = [sp_strip_chars(p, " ()") for p in manual_split(right_clean, '|')]
        diff_set = sorted(set(left_parts) - set(right_parts))
        return "(" + "|".join(tok for tok in (ascii_token(tok) for tok in diff_set) if tok) + ")"
    
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
                union = "|".join(sorted(ascii_token(x) for x in diff))
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
                                elif seq == '\\s':
                                    literal += ' '   # Aquí convertimos \s en espacio
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
                                if len(literal) > 1:
                                        for char in literal:
                                            tokens.append(char)
                                else:
                                    tokens.append(literal)

                                tokens.append('-')
                                tokens.append(literal2)
                        else:
                            if len(literal) > 1:
                                for char in literal:
                                    tokens.append(char)
                            else:
                                tokens.append(literal)

                    elif contenido[k].isspace():
                        tokens.append(contenido[k])
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
                ascii_tokens = [ascii_token(tok) for tok in tokens]
                ascii_tokens = [tok for tok in ascii_tokens if tok and tok != '|']

                # REVISIÓN CLAVE AQUÍ:
                if not ascii_tokens:
                    expanded = '949'  # Épsilon explícito cuando no hay tokens válidos
                else:
                    expanded = "(" + "|".join(ascii_tokens) + ")"


            resultado += expanded
            i = j + 1
        else:
        # Si es una comilla abriendo literal
            if expresion[i] in ["'", '"']:
                quote_char = expresion[i]
                i += 1
                literal = ""
                while i < len(expresion) and expresion[i] != quote_char:
                    if expresion[i] == '\\' and i+1 < len(expresion):
                        esc = expresion[i+1]
                        if esc == 's':
                            literal += ' '
                        elif esc == 't':
                            literal += '\t'
                        elif esc == 'n':
                            literal += '\n'
                        else:
                            literal += esc
                        i += 2
                    else:
                        literal += expresion[i]
                        i += 1
                i += 1  # Saltar comilla final
                resultado += "(" + "|".join(tok for tok in (ascii_token(c) for c in literal) if tok) + ")"
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
                    union = "|".join(tok for tok in sorted(ascii_token(x) for x in ALPHABET) if tok)
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
    No se aplicará transformación a '?'; se retorna la expresión sin cambios.
    """
    return expr

def limpiar_expresion(expr):
    """
    Limpia la expresión eliminando dobles operadores y paréntesis vacíos.
    Reemplaza:
      - '||' por '|'
      - '..' por '.'
      - '()' por '949'
    """
    # Reemplazos repetidos hasta que no se encuentren más patrones
    anterior = None
    while anterior != expr:
        anterior = expr
        expr = expr.replace("||", "|")
        expr = expr.replace("..", ".")
        expr = expr.replace("()", "949")
    return expr

def insertar_concatenaciones(expr):
    """
    Inserta '.' explícitamente donde se requiere concatenación entre tokens,
    respetando números de más de un dígito como 43 o 949.
    """
    resultado = ""
    i = 0
    while i < len(expr):
        actual = expr[i]

        # Leer token actual completo (por ejemplo: un número como 43 o 949)
        token = ""
        if actual.isdigit():
            while i < len(expr) and expr[i].isdigit():
                token += expr[i]
                i += 1
        else:
            token = actual
            i += 1

        # Agregar '.' si corresponde con el anterior
        if resultado:
            prev = resultado[-1]
            if (
                (prev.isdigit() or prev == ')' or prev == '*') and
                (token[0].isdigit() or token[0] == '(' or token[0] in ['"', "'"])
            ):
                resultado += '.'

        resultado += token

    return resultado

def combine_expressions(config):
    combined = []
    mapping = {}
    rule_id = 0

    for regla in config["reglas"]:
        raw_expr = regla["expresion"]

        # Convertimos caracteres literales a ASCII
        if ((raw_expr.startswith("'") and raw_expr.endswith("'")) or 
            (raw_expr.startswith('"') and raw_expr.endswith('"'))) and len(raw_expr[1:-1]) == 1:
            final_expr = ascii_token(raw_expr[1:-1])
        elif len(raw_expr) == 1:
            final_expr = ascii_token(raw_expr)
        else:
            exp_ids = expand_identificadores(raw_expr, config["definiciones"])
            expanded = expand_rangos(exp_ids)
            limpio = limpiar_parentesis(expanded)
            final_expr = expand_repetition_operators(expand_optionals(limpio))

        # Caso especial: si la expresión está vacía o es solo épsilon
        if not final_expr or final_expr in ['|', '.', '()', '', '949']:
            final_expr = '949'

        # Agrega puntos de concatenación explícitos
        final_expr = insertar_concatenaciones(final_expr)

        tag_number = 1000 + rule_id

        # Concatenamos la expresión con su tag como hoja final
        annotated_expr = f"(({final_expr}).#{tag_number})"

        combined.append(annotated_expr)
        mapping[f"#{tag_number}"] = regla["accion"]
        rule_id += 1

    # Unimos todas las expresiones usando unión
    master_expr = " | ".join(expr for expr in combined if sp_manual(expr))
    master_expr = limpiar_expresion(master_expr)

    return master_expr, mapping

# MAIN
if __name__ == '__main__':
    ruta_yal = "slr-2.yal"  # Cambia este nombre por el de tu archivo YAL.
    contenido = leer_archivo(ruta_yal)
    config = parse_yal_config(contenido)

    print("Definiciones encontradas:")
    for nombre, expresion in config["definiciones"].items():
        print(f"{nombre} = {expresion}")
        exp_ids = expand_identificadores(expresion, config["definiciones"])
        expanded = expand_rangos(exp_ids)
        limpio = limpiar_parentesis(expanded)
        final = expand_optionals(limpio)
        print(f"  Expandidas: {expanded}")
        print(f"  Limpio: {limpio}")
        print(f"  Final con opcionales: {final}\n")

    print("Reglas encontradas:")
    for regla in config["reglas"]:
        print(f"Expresión: {regla['expresion']}")
        print(f"  Acción: {regla['accion']}")
        raw_expr = regla["expresion"]
        
        # Si la expresión está entre comillas y tiene un solo carácter, extrae ese carácter
        if ((raw_expr.startswith("'") and raw_expr.endswith("'")) or 
            (raw_expr.startswith('"') and raw_expr.endswith('"'))) and len(raw_expr[1:-1]) == 1:
            literal = raw_expr[1:-1]
            ascii_literal = ascii_token(literal)
            print(f"  Expandidas: {ascii_literal}")
            print(f"  Limpio: {ascii_literal}")
            print(f"  Final con opcionales: {ascii_literal}")
        # O si la cadena es de longitud 1 sin comillas
        elif len(raw_expr) == 1:
            ascii_literal = ascii_token(raw_expr)
            print(f"  Expandidas: {ascii_literal}")
            print(f"  Limpio: {ascii_literal}")
            print(f"  Final con opcionales: {ascii_literal}")
        else:
            exp_ids = expand_identificadores(raw_expr, config["definiciones"])
            expanded = expand_rangos(exp_ids)
            limpio = limpiar_parentesis(expanded)
            final = expand_optionals(limpio)
            print(f"  Expandidas: {expanded}")
            print(f"  Limpio: {limpio}")
            print(f"  Final con opcionales: {final}")
        print("-" * 40)

    master_expr, mapping = combine_expressions(config)
    print("Expresión maestra combinada para Shunting:")
    print(master_expr)
    print("\nMapping de procedencia:")
    for tag, accion in mapping.items():
        print(f"{tag}: {accion}")