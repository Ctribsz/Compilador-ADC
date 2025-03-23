from Lector import leer_archivo, parse_yal_config, combine_expressions
from shunting import shunting_yard

def main():
    # Ruta al archivo YAL que querés analizar (podés cambiar esto directamente)
    ruta = "slr-1.yal"  # ← Cambialo según el archivo que quieras probar

    contenido = leer_archivo(ruta)
    config = parse_yal_config(contenido)
    
    master_expr, mapping = combine_expressions(config)
    
    print("Expresión maestra combinada para Shunting:")
    print(master_expr)
    
    print("\nMapping de procedencia:")
    for tag, accion in mapping.items():
        print(f"{tag}: {accion}")
    
    resultado = shunting_yard(master_expr)
    print("\nResultado en notación Postfix:")
    print(resultado)

if __name__ == '__main__':
    main()