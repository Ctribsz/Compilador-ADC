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
    output, stack = [], []
    infix = insert_concatenation_operators(infix)
    for c in infix:
        if is_operand(c) or c == '#':
            output.append(c)
        elif c == '(':
            stack.append(c)
        elif c == ')':
            while stack and stack[-1] != '(':
                output.append(stack.pop())
            stack.pop()
        else:
            while stack and stack[-1] != '(' and precedence.get(stack[-1], 0) >= precedence[c]:
                output.append(stack.pop())
            stack.append(c)
    while stack:
        output.append(stack.pop())
    return output

def build_syntax_tree(postfix):
    stack = []
    positions = {}
    pos = 1

    for token in postfix:
        if token == '_':
            continue  # Epsilon no se convierte en nodo

        if token.isdigit():
            node = Node(token)
            node.position = pos
            node.firstpos = node.lastpos = {pos}
            node.nullable = False
            positions[pos] = node
            stack.append(node)
            pos += 1

        elif token == '*':
            if not stack:
                raise ValueError("Error: '*' requiere un operando.")
            child = stack.pop()
            node = Node(token, child)
            node.nullable = True
            node.firstpos = child.firstpos
            node.lastpos = child.lastpos
            stack.append(node)

        elif token in {'|', '.'}:
            if len(stack) < 2:
                raise ValueError(f"Error: operador '{token}' requiere dos operandos.")
            right = stack.pop()
            left = stack.pop()
            node = Node(token, left, right)
            if token == '|':
                node.nullable = left.nullable or right.nullable
                node.firstpos = left.firstpos | right.firstpos
                node.lastpos = left.lastpos | right.lastpos
            else:  # '.'
                node.nullable = left.nullable and right.nullable
                node.firstpos = (left.firstpos | right.firstpos) if left.nullable else left.firstpos
                node.lastpos = (left.lastpos | right.lastpos) if right.nullable else right.lastpos
            stack.append(node)

        elif token == '?':
            if not stack:
                raise ValueError("Error: '?' requiere un operando.")
            child = stack.pop()
            node = Node('|', child, Node('_'))  # A | ε
            node.nullable = True
            node.firstpos = child.firstpos
            node.lastpos = child.lastpos
            stack.append(node)

        elif token == '+':
            if not stack:
                raise ValueError("Error: '+' requiere un operando.")
            child = stack.pop()
            node_star = Node('*', child)
            node = Node('.', child, node_star)
            node.nullable = child.nullable
            node.firstpos = child.firstpos
            node.lastpos = child.lastpos
            stack.append(node)

    if len(stack) != 1:
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
    final_positions = [pos for pos, node in positions.items() if node.value.isdigit() and int(node.value) >= 1000]

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
    for group, rep in state_map.items():
        if any(s in accepted for s in group):
            min_accepted.add(rep)
        min_trans[rep] = {}
        original = next(iter(group))
        for sym, dest in afd_dict['transitions'][original].items():
            for g, gname in state_map.items():
                if dest in g:
                    min_trans[rep][sym] = gname
                    break
    for state, trans in min_trans.items():
        shape = 'doublecircle' if state in min_accepted else 'circle'
        min_afd.node(state, shape=shape)
        for sym, dest in trans.items():
            min_afd.edge(state, dest, sym)
    return min_afd