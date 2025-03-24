precedence = {
    "#": 4,  # Diferencia de conjuntos (si aplica)
    "*": 3,  # Cerradura
    "+": 3,  # Cerradura positiva
    "?": 3,  # Opcional
    ".": 2,  # Concatenación
    "|": 1   # Unión
}

def is_operator(token: str) -> bool:
    return token in precedence

def tokenize(expr: str) -> list:
    tokens = []
    i = 0
    while i < len(expr):
        if expr[i] == '#' and i + 1 < len(expr) and expr[i+1].isdigit():
            tag = "#"
            i += 1
            while i < len(expr) and expr[i].isdigit():
                tag += expr[i]
                i += 1
            tokens.append(tag)
        elif expr[i].isdigit():
            num = ""
            while i < len(expr) and expr[i].isdigit():
                num += expr[i]
                i += 1
            tokens.append(num)
        elif expr[i] in ['(', ')', '|', '.', '*', '+', '?', '#']:
            tokens.append(expr[i])
            i += 1
        elif expr[i] == '_':
            tokens.append('949')
            i += 1
        elif expr[i].isspace():
            i += 1
        else:
            tokens.append(expr[i])
            i += 1
    return tokens

def insert_concatenation(expr: str) -> str:
    tokens = tokenize(expr)
    result = []

    for i in range(len(tokens)):
        result.append(tokens[i])
        if i + 1 < len(tokens):
            curr = tokens[i]
            nxt = tokens[i + 1]

            # Condiciones para insertar '.'
            if (
                (curr not in {'|', '.', '(',} and not curr.startswith('#')) and
                (nxt not in {'|', '.', ')', '*', '+', '?'} and not nxt.startswith('#'))
            ):
                result.append('.')

    return ' '.join(result)

def shunting_yard(master_expr: str) -> str:
    expr_with_concat = insert_concatenation(master_expr)
    tokens = expr_with_concat.split()

    output = []
    stack = []

    for token in tokens:
        if token.isdigit() or token == '949' or (token.startswith('#') and token[1:].isdigit()):
            output.append(token)
        elif token == '(':
            stack.append(token)
        elif token == ')':
            while stack and stack[-1] != '(':
                output.append(stack.pop())
            if stack and stack[-1] == '(':
                stack.pop()
        elif is_operator(token):
            while (stack and stack[-1] != '(' and
                   precedence.get(stack[-1], 0) >= precedence.get(token, 0)):
                output.append(stack.pop())
            stack.append(token)
        else:
            output.append(token)

    while stack:
        output.append(stack.pop())

    return ' '.join(output)

def limpiar_postfix(postfix_expr: str) -> str:
    tokens = postfix_expr.strip().split()
    cleaned = []
    stack_depth = 0

    for token in tokens:
        if token in {'.', '|'}:
            if stack_depth < 2:
                continue  # operador binario sin suficientes operandos
            stack_depth -= 1  # combina dos en uno
        elif token in {'*', '+', '?'}:
            if stack_depth < 1:
                continue  # operador unario sin operando
            # stack_depth no cambia
        else:
            stack_depth += 1  # nuevo operando válido

        cleaned.append(token)

    # Solo devolver si la expresión termina con un stack válido
    if stack_depth == 1:
        return ' '.join(cleaned)
    else:
        raise ValueError("Postfix no válida incluso tras limpieza")