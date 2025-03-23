# shunting.py

# Tabla de precedencia: mayor número = mayor prioridad.
precedence = {
    "#": 4,   # Diferencia de conjuntos
    "*": 3,   # Cerradura
    "+": 3,   # Positiva
    "?": 3,   # Opcional
    ".": 2,   # Concatenación
    "|": 1    # Unión
}

def is_operator(token: str) -> bool:
    """Devuelve True si el token es un operador según la tabla de precedencia."""
    return token in precedence

def tokenize(expr: str) -> list:
    """
    Tokeniza la expresión:
    - Acumula dígitos (operandos, representados como cadenas numéricas)
    - Los operadores y paréntesis se toman como tokens individuales.
    """
    tokens = []
    i = 0
    while i < len(expr):
        if expr[i].isdigit():
            num = ""
            while i < len(expr) and expr[i].isdigit():
                num += expr[i]
                i += 1
            tokens.append(num)
        elif expr[i] in ['(', ')', '|', '.', '*', '+', '?', '#']:
            tokens.append(expr[i])
            i += 1
        elif expr[i].isspace():
            i += 1  # Ignora espacios
        else:
            tokens.append(expr[i])
            i += 1
    return tokens

def insert_concatenation(expr: str) -> str:
    """
    Inserta '.' entre tokens que deben concatenarse.
    """
    tokens = tokenize(expr)
    result = []
    for i in range(len(tokens)):
        result.append(tokens[i])
        if i + 1 < len(tokens):
            curr = tokens[i]
            nxt = tokens[i + 1]
            # Condiciones para insertar concatenación
            if (curr.isdigit() or curr == ')' or curr in ['*', '+', '?']) and \
               (nxt.isdigit() or nxt == '('):
                result.append('.')
    return ''.join(result)

def shunting_yard(master_expr: str) -> str:
    """
    Convierte la expresión infix (en formato ASCII) a notación postfix.
    """
    master_expr = insert_concatenation(master_expr)
    tokens = tokenize(master_expr)
    output = []  # Lista para la salida en notación postfix.
    op_stack = []  # Pila para los operadores.

    for token in tokens:
        if token.isdigit():
            output.append(token)
        elif token == "(":
            op_stack.append(token)
        elif token == ")":
            while op_stack and op_stack[-1] != "(":
                output.append(op_stack.pop())
            if op_stack and op_stack[-1] == "(":
                op_stack.pop()
        elif is_operator(token):
            while (op_stack and op_stack[-1] != "(" and
                   is_operator(op_stack[-1]) and
                   precedence[op_stack[-1]] >= precedence[token]):
                output.append(op_stack.pop())
            op_stack.append(token)
        else:
            output.append(token)

    while op_stack:
        output.append(op_stack.pop())

    return " ".join(output)