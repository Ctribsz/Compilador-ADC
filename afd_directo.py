import os
import graphviz

class Node:
    def __init__(self, value, left=None, right=None):
        self.value = value
        self.left = left
        self.right = right
        self.firstpos = set()
        self.lastpos = set()
        self.nullable = False
        self.position = None

def is_operator(c):
    return c in {'|', '.', '*', '(', ')', '#'}

def is_operand(c):
    return c.isalnum() and not is_operator(c)

def insert_concatenation_operators(infix):
    output = []
    for i in range(len(infix)):
        output.append(infix[i])
        if i + 1 < len(infix):
            if (is_operand(infix[i]) or infix[i] in {')', '*'}) and \
               (is_operand(infix[i + 1]) or infix[i + 1] == '(' or infix[i + 1] == '#'):
                output.append('.')
    return ''.join(output)

def to_postfix(infix):
    precedence = {'|': 1, '.': 2, '*': 3}
    output = []
    stack = []

    # Tokenización manual con soporte para números y tags como #1000
    i = 0
    while i < len(infix):
        c = infix[i]

        # Tokens tipo #1000
        if c == '#' and i + 1 < len(infix):
            j = i + 1
            while j < len(infix) and infix[j].isdigit():
                j += 1
            output.append(infix[i:j])
            i = j
            continue

        # Números de más de un dígito
        elif c.isdigit():
            j = i
            while j < len(infix) and infix[j].isdigit():
                j += 1
            output.append(infix[i:j])
            i = j
            continue

        elif c.isalpha():
            output.append(c)
            i += 1
            continue

        elif c == '(':
            stack.append(c)
            i += 1
            continue

        elif c == ')':
            while stack and stack[-1] != '(':
                output.append(stack.pop())
            if stack and stack[-1] == '(':
                stack.pop()
            i += 1
            continue

        elif c in precedence:
            while stack and stack[-1] != '(' and precedence.get(stack[-1], 0) >= precedence[c]:
                output.append(stack.pop())
            stack.append(c)
            i += 1
            continue

        else:
            # Saltar espacios u otros caracteres no relevantes
            i += 1

    while stack:
        output.append(stack.pop())

    return output

def build_syntax_tree(postfix):
    stack = []
    positions = {}
    pos = 1

    for token in postfix:
        token = sp_manual(token)
        if not token:
            continue

        # Si el token es un número (ASCII)
        if token.isdigit():
            node = Node(token)
            node.position = pos
            node.firstpos = node.lastpos = {pos}
            node.nullable = False
            positions[pos] = node
            stack.append(node)
            pos += 1
            continue

        # 🔧 FIX: Si el token es #1000, #1001, etc. → también es hoja con posición
        if token.startswith('#') and token[1:].isdigit():
            node = Node(token)
            node.position = pos
            node.firstpos = node.lastpos = {pos}
            node.nullable = False
            positions[pos] = node
            stack.append(node)
            pos += 1
            continue

        # Si es épsilon explícito
        if token == '949':
            node = Node(token)
            node.nullable = True
            node.firstpos = node.lastpos = set()
            stack.append(node)
            continue

        # Operadores unarios
        if token in {'*', '?', '+'}:
            if not stack:
                raise ValueError(f"Error: '{token}' requiere un operando.")
            child = stack.pop()

            if token == '*':
                node = Node('*', child)
                node.nullable = True
                node.firstpos = child.firstpos
                node.lastpos = child.lastpos

            elif token == '?':
                node = Node('|', child, Node('949'))  # A | ε
                node.nullable = True
                node.firstpos = child.firstpos | set()
                node.lastpos = child.lastpos | set()

            elif token == '+':
                node_star = Node('*', child)
                node = Node('.', child, node_star)
                node.nullable = child.nullable
                node.firstpos = child.firstpos
                node.lastpos = node_star.lastpos

            stack.append(node)
            continue

        # Operadores binarios
        if token in {'|', '.'}:
            if len(stack) < 2:
                print("Estado de la pila antes del error:", stack)
                raise ValueError(f"Error: operador '{token}' requiere dos operandos.")
            right = stack.pop()
            left = stack.pop()
            node = Node(token, left, right)

            if token == '|':
                node.nullable = left.nullable or right.nullable
                node.firstpos = left.firstpos | right.firstpos
                node.lastpos = left.lastpos | right.lastpos
            else:  # Concatenación
                node.nullable = left.nullable and right.nullable
                node.firstpos = left.firstpos if not left.nullable else left.firstpos | right.firstpos
                node.lastpos = right.lastpos if not right.nullable else left.lastpos | right.lastpos

            stack.append(node)
            continue

        raise ValueError(f"Token desconocido: '{token}'")

    if len(stack) != 1:
        print("Estado final de la pila (debería tener solo un nodo):", stack)
        raise ValueError("Error: expresión inválida, árbol no puede construirse.")

    return stack[0], positions

def generate_ast_graph(root):
    dot = graphviz.Digraph('AST')
    def add_nodes(node, parent_id=None):
        if node:
            node_id = str(id(node))
            label = f"{node.value}"
            if node.position:
                label += f" ({node.position})"
            dot.node(node_id, label)
            if parent_id:
                dot.edge(parent_id, node_id)
            add_nodes(node.left, node_id)
            add_nodes(node.right, node_id)
    add_nodes(root)
    return dot

def compute_followpos(root, positions):
    followpos = {pos: set() for pos in positions}
    def compute(node):
        if node:
            if node.value == '.':
                for i in node.left.lastpos:
                    followpos[i] |= node.right.firstpos
            elif node.value == '*':
                for i in node.lastpos:
                    followpos[i] |= node.firstpos
            compute(node.left)
            compute(node.right)
    compute(root)
    return followpos

def st_m(texto):
    partes = []
    actual = ""
    for ch in texto:
        if ch == ' ':
            if actual:
                partes.append(actual)
                actual = ""
        else:
            actual += ch
    if actual:
        partes.append(actual)
    return partes

def sp_manual(texto):
    inicio = 0
    while inicio < len(texto) and texto[inicio] in [' ', '\t', '\n', '\r']:
        inicio += 1

    fin = len(texto) - 1
    while fin >= 0 and texto[fin] in [' ', '\t', '\n', '\r']:
        fin -= 1

    return texto[inicio:fin+1] if inicio <= fin else ''

def generate_afd(root, positions, followpos):
    import graphviz
    afd = graphviz.Digraph('AFD')
    afd.attr(rankdir='LR')

    initial = frozenset(root.firstpos)
    states = {initial: 'A'}
    unmarked = [initial]
    count = 0
    afd_dict = {'transitions': {}, 'accepted': [], 'initial': 'A', 'states': {}}

    # Nodo de inicio invisible
    afd.node('', shape='none')
    afd.edge('', 'A', label='')

    # Encontrar posiciones de aceptación (tokens >= 1000)
    final_positions = {pos for pos, node in positions.items() if node.value.startswith('#')}

    while unmarked:
        state = unmarked.pop(0)
        state_name = states[state]

        # Guardar el conjunto de posiciones en el diccionario
        afd_dict['states'][state] = state_name

        # Marcar si el estado es de aceptación
        if any(p in state for p in final_positions):
            afd_dict['accepted'].append(state_name)

        transiciones = {}
        for pos in state:
            symbol = positions[pos].value
            if symbol.isdigit() and int(symbol) >= 1000:
                continue  # no usar marcadores como símbolos
            if symbol not in transiciones:
                transiciones[symbol] = set()
            transiciones[symbol] |= followpos[pos]

        afd_dict['transitions'][state_name] = {}

        for symbol, next_positions in transiciones.items():
            if not next_positions:
                continue
            next_state = frozenset(next_positions)
            if next_state not in states:
                count += 1
                states[next_state] = chr(ord('A') + count)
                unmarked.append(next_state)
            afd.edge(state_name, states[next_state], label=str(symbol))
            afd_dict['transitions'][state_name][symbol] = states[next_state]

    for state_set, name in states.items():
        shape = 'doublecircle' if name in afd_dict['accepted'] else 'circle'
        afd.node(name, shape=shape)

    return afd, afd_dict

def minimize_afd(afd_dict):
    accepted = set(afd_dict['accepted'])
    groups, min_trans, min_accepted, state_map = {}, {}, set(), {}
    
    for state, trans in afd_dict['transitions'].items():
        key = (frozenset(trans.items()), state in accepted)
        groups.setdefault(key, []).append(state)
    
    for i, group in enumerate(groups.values()):
        name = f"M{i}"
        state_map[frozenset(group)] = name
    
    min_afd = graphviz.Digraph('MinAFD')
    min_afd.attr(rankdir='LR')
    min_afd.node("", shape="none")
    
    initial_group = next(g for g in state_map if afd_dict['initial'] in g)
    min_afd.edge("", state_map[initial_group], label="")

    afd_dict_min = {
        'transitions': {},
        'accepted': [],
        'initial': state_map[initial_group],
        'states': {}
    }

    for group, rep in state_map.items():
        if any(s in accepted for s in group):
            afd_dict_min['accepted'].append(rep)
        afd_dict_min['states'][group] = rep
        min_trans[rep] = {}
        original = next(iter(group))
        for sym, dest in afd_dict['transitions'][original].items():
            for g, gname in state_map.items():
                if dest in g:
                    min_trans[rep][sym] = gname
                    afd_dict_min['transitions'].setdefault(rep, {})[sym] = gname
                    break

    for state, trans in min_trans.items():
        shape = 'doublecircle' if state in afd_dict_min['accepted'] else 'circle'
        min_afd.node(state, shape=shape)
        for sym, dest in trans.items():
            min_afd.edge(state, dest, sym)

    return min_afd, afd_dict_min