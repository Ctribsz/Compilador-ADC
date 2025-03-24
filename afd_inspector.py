import pickle
import os

def mostrar_info_afd(ruta_pickle):
    """
    Carga un AFD desde un archivo .pkl y muestra su información textual:
    - Estado inicial
    - Estados de aceptación
    - Transiciones por estado
    """
    if not os.path.exists(ruta_pickle):
        print(f"❌ El archivo no existe: {ruta_pickle}")
        return

    try:
        with open(ruta_pickle, 'rb') as f:
            afd = pickle.load(f)

        if not isinstance(afd, dict):
            raise ValueError("El archivo no contiene un diccionario válido.")

        print(f"✅ AFD cargado desde: {ruta_pickle}")
        print(f"➡️  Estado inicial: {afd.get('initial', 'N/A')}")

        aceptacion = afd.get('accepted', [])
        print(f"✔️  Estados de aceptación: {', '.join(aceptacion) if aceptacion else 'Ninguno'}")

        transiciones = afd.get('transitions', {})
        print(f"🔁 Transiciones:")
        for estado, trans in transiciones.items():
            for simbolo, destino in trans.items():
                print(f"    {estado} --{simbolo}--> {destino}")

    except Exception as e:
        print(f"❌ Error al mostrar el AFD: {e}")
