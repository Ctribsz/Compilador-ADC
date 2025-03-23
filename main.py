import os
from Lector import leer_archivo, parse_yal_config, combine_expressions
from shunting import shunting_yard
from afd_directo import (
    build_syntax_tree,
    generate_ast_graph,
    compute_followpos,
    generate_afd,
    minimize_afd
)

def main():
    ruta = "slr-1.yal"  # Cambiar si se usa otro archivo .yal
    contenido = leer_archivo(ruta)
    config = parse_yal_config(contenido)
    master_expr, mapping = combine_expressions(config)

    print("Expresión maestra combinada para Shunting:")
    print(master_expr)

    print("\nMapping de procedencia:")
    for tag, accion in mapping.items():
        print(f"{tag}: {accion}")

    postfix_expr = shunting_yard(master_expr)


    print("\nResultado en notación Postfix (con #):")
    print(postfix_expr)

    # Construcción del AFD Directo
    root, positions = build_syntax_tree(postfix_expr.split())
    followpos = compute_followpos(root, positions)

    output_dir = f"output_afds/{ruta.split('.')[0]}"
    os.makedirs(output_dir, exist_ok=True)

    generate_ast_graph(root).render(f"{output_dir}/ast", format="png", cleanup=True)
    afd, afd_dict = generate_afd(root, positions, followpos)

    afd.render(f"{output_dir}/afd", format="png", cleanup=True)
    minimized_afd = minimize_afd(afd_dict)
    minimized_afd.render(f"{output_dir}/afd_minimized", format="png", cleanup=True)

    print("\nEstados de aceptación:", afd_dict['accepted'])
    print(f"\nDiagramas generados en: {output_dir}")

if __name__ == '__main__':
    main()