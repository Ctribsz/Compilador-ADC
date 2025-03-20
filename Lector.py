def leer_archivo(ruta):
    """Lee y retorna el contenido completo de un archivo."""
    with open(ruta, 'r', encoding='utf-8') as f:
        return f.read()

def remove_comments(texto):
    """
    Elimina comentarios delimitados por (* y *).
    Se recorre el texto carácter a carácter, detectando la secuencia de inicio
    y saltando hasta la secuencia de cierre.
    """
    resultado = ""
    i = 0
    while i < len(texto):
        # Detecta inicio de comentario: '(*'
        if texto[i] == '(' and i + 1 < len(texto) and texto[i + 1] == '*':
            # Saltar el comentario
            i += 2  # Salta '(*'
            while i < len(texto):
                # Busca el cierre del comentario: '*)'
                if texto[i] == '*' and i + 1 < len(texto) and texto[i + 1] == ')':
                    i += 2  # Salta '*)'
                    break
                else:
                    i += 1
        else:
            resultado += texto[i]
            i += 1
    return resultado

def parse_definiciones(lineas):
    """
    Procesa las líneas del archivo YAL y extrae las definiciones.
    Cada definición tiene la forma:
      let <nombre> = <expresión>
    Se almacena en un diccionario {nombre: expresión}.
    """
    definiciones = {}
    for linea in lineas:
        linea = linea.strip()
        if linea.startswith("let"):
            # Removemos la palabra 'let' y separamos por el signo '='
            # Se asume que la estructura es: let <nombre> = <expresión>
            sin_let = linea[3:].strip()  # quita "let"
            if "=" in sin_let:
                # Separa en nombre y expresión
                partes = sin_let.split("=", 1)
                nombre = partes[0].strip()
                expresion = partes[1].strip()
                definiciones[nombre] = expresion
    return definiciones

def parse_reglas(lineas):
    """
    Procesa la sección de reglas del archivo YAL.
    Se espera que la sección comience con una línea que inicia con 'rule'.
    Luego, cada alternativa se define en líneas que pueden comenzar con '|'
    o directamente en la primera línea tras la cabecera de la regla.
    Se extrae la expresión regular y la acción (lo que esté entre '{' y '}').
    Retorna una lista de reglas en el orden en que aparecen.
    """
    reglas = []
    modo_reglas = False
    for linea in lineas:
        linea_limpia = linea.strip()
        if not modo_reglas:
            # Detectar el inicio de la sección de reglas
            if linea_limpia.startswith("rule"):
                modo_reglas = True
            continue
        # Una vez en la sección de reglas, ignoramos líneas vacías
        if linea_limpia == "":
            continue

        # En algunas definiciones, cada alternativa puede iniciar con '|' o sin él.
        if linea_limpia.startswith("|"):
            linea_limpia = linea_limpia[1:].strip()

        # Buscamos la apertura de la acción en llaves '{'
        if "{" in linea_limpia:
            partes = linea_limpia.split("{", 1)
            expresion = partes[0].strip()
            # Extraemos la acción: asumimos que termina con '}'
            accion_con_brace = partes[1]
            if "}" in accion_con_brace:
                accion = accion_con_brace.split("}", 1)[0].strip()
            else:
                accion = accion_con_brace.strip()
        else:
            # Si no hay acción definida, se puede asignar None
            expresion = linea_limpia
            accion = None

        reglas.append({
            "expresion": expresion,
            "accion": accion
        })
    return reglas

def parse_yal_config(texto):
    """
    Procesa el contenido del archivo YAL:
      1. Elimina comentarios.
      2. Separa el contenido en líneas.
      3. Extrae definiciones y reglas.
    Retorna un diccionario con las definiciones y una lista de reglas.
    """
    # Paso 1: Eliminar comentarios
    texto_sin_comentarios = remove_comments(texto)
    # Paso 2: Separar en líneas
    lineas = texto_sin_comentarios.splitlines()
    
    # Extraer definiciones: se asume que aparecen antes de la sección de reglas
    definiciones = parse_definiciones(lineas)
    
    # Extraer reglas: se busca la sección que comienza con "rule"
    reglas = parse_reglas(lineas)
    
    return {
        "definiciones": definiciones,
        "reglas": reglas
    }

# Ejemplo de uso:
if __name__ == '__main__':
    ruta_yal = "config.yal"  # Cambia esto por la ruta a tu archivo YAL
    contenido_yal = leer_archivo(ruta_yal)
    
    # Procesa el archivo YAL para extraer definiciones y reglas
    config = parse_yal_config(contenido_yal)
    
    print("Definiciones encontradas:")
    for nombre, expresion in config["definiciones"].items():
        print(f"  {nombre} = {expresion}")
    
    print("\nReglas encontradas:")
    for regla in config["reglas"]:
        print(f"  Expresión: {regla['expresion']}")
        print(f"  Acción: {regla['accion']}")
        print("-" * 40)
