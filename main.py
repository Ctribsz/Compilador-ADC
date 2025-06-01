import os
from Lector import leer_archivo, parse_yal_config, combine_expressions, validar_estructura_yal
from shunting import shunting_yard, limpiar_postfix
from afd_serializer import guardar_afd_pickle, cargar_afd_pickle
from afd_inspector import mostrar_info_afd
from lexer import lexer
import json

from afd_directo import (
    build_syntax_tree,
    generate_ast_graph,
    compute_followpos,
    generate_afd,
    minimize_afd,
    st_m
)

def afd_to_json(afd_dict):
    return {
        "transitions": afd_dict["transitions"],
        "accepted": afd_dict["accepted"],
        "initial": afd_dict["initial"],
        "states": {str(list(k)): v for k, v in afd_dict["states"].items()},
        "state_tags": afd_dict.get("state_tags", {})
    }

def main():
    ruta = "slr-4" 
    contenido = leer_archivo(ruta + ".yal")
     # 🔍 Validar estructura del archivo YAL
    errores = validar_estructura_yal(contenido)
    if errores:
        print("🚫 El archivo .yal contiene errores de estructura:\n")
        for error in errores:
            print(error)
        print("\n🛑 Corre los errores y volvé a intentar.")
        return  # Cortamos ejecución si hay errores
    
    config = parse_yal_config(contenido)
    master_expr, mapping = combine_expressions(config)
    
    
    print("Expresión maestra combinada para Shunting:")
    print(master_expr)

    print("\nMapping de procedencia:")
    for tag, accion in mapping.items():
        print(f"{tag}: {accion}")

    postfix_expr = shunting_yard(master_expr)

    
    # Intentamos construir el árbol. Si falla, aplicamos limpieza.
    try:
        root, positions = build_syntax_tree(st_m(postfix_expr))
    except ValueError as e:
        print("\n⚠️ Error al construir el árbol, aplicando limpieza de postfix...")
        postfix_expr = limpiar_postfix(postfix_expr)
        print("Postfix corregida:")
        print(postfix_expr)
        tokens = (st_m(postfix_expr))
        root, positions = build_syntax_tree(tokens)

    print("\nResultado en notación Postfix (con #):")
    print(postfix_expr)

    followpos = compute_followpos(root, positions)

    output_dir = f"output_afds/{ruta.split('.')[0]}"
    os.makedirs(output_dir, exist_ok=True)

    generate_ast_graph(root).render(f"{output_dir}/ast", format="png", cleanup=True)
    afd, afd_dict = generate_afd(root, positions, followpos)

    afd.render(f"{output_dir}/afd", format="png", cleanup=True)
    minimized_afd, afd_dict_min = minimize_afd(afd_dict)
    minimized_afd.attr(rankdir='LR', size='500,10', dpi='300')
    minimized_afd.render(f"{output_dir}/afd_minimized", format="png", cleanup=True)
    minimized_afd.render(f"{output_dir}/afd_minimized", format="pdf", cleanup=True)

    print(json.dumps(afd_to_json(afd_dict_min), indent=4))
        
    # Guardar el AFD minimizado en .pkl
    afd_pickle_path = f"{output_dir}/afd_min.pkl"
    guardar_afd_pickle(afd_dict_min, mapping, afd_pickle_path)

    print("\nEstados de aceptación:", afd_dict['accepted'])
    print(f"\nDiagramas generados en: {output_dir}")
    mostrar_info_afd("output_afds/" + ruta + "/afd_min.pkl")
    print(mapping)
    
    # Simulación desde archivo guardado
    print("\n🔍 ¿Cómo querés ingresar la entrada para tokenizar?")
    print("1. Ingresar una cadena manualmente")
    print("2. Leer la cadena desde un archivo de texto")

    opcion = input("Seleccioná una opción (1 o 2): ")

    if opcion == '1':
        cadena_usuario = input("🔤 Ingresá una cadena para tokenizar: ")
    elif opcion == '2':
        ruta_archivo = input("📄 Ingresá la ruta del archivo de texto: ")
        if not os.path.isfile(ruta_archivo):
            print("⚠️ Archivo no encontrado.")
            return
        with open(ruta_archivo, "r", encoding="utf-8") as f:
            cadena_usuario = f.read()
            print(f"\n📚 Contenido del archivo leído:\n{cadena_usuario}")
    else:
        print("⚠️ Opción inválida. Saliendo.")
        return

    # Cargar el AFD minimizado
    afd_dict = cargar_afd_pickle(afd_pickle_path)

    # Simular el análisis léxico
    tokens = lexer(cadena_usuario, afd_dict, mapping, debug=True)

    # Mostrar tokens finales
    print("\n🎯 Tokens generados:")
    for tipo, lexema in tokens:
        print(f"  {tipo}: '{lexema}'")


if __name__ == '__main__':
    main()