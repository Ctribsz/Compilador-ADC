import pickle
import os

def guardar_afd_pickle(afd_dict, ruta):
    """
    Guarda el diccionario AFD en un archivo .pkl

    Parámetros:
        afd_dict (dict): El AFD generado, con claves como 'transitions', 'accepted', etc.
        ruta (str): Ruta donde se guardará el archivo .pkl
    """
    try:
        with open(ruta, 'wb') as f:
            pickle.dump(afd_dict, f)
        print(f"✅ AFD guardado exitosamente en: {ruta}")
    except Exception as e:
        print(f"❌ Error al guardar el AFD: {e}")

def cargar_afd_pickle(ruta):
    """
    Carga un AFD desde un archivo .pkl

    Parámetros:
        ruta (str): Ruta del archivo .pkl

    Retorna:
        dict: El AFD cargado con su estructura completa
    """
    if not os.path.exists(ruta):
        raise FileNotFoundError(f"❌ El archivo no existe: {ruta}")

    try:
        with open(ruta, 'rb') as f:
            afd_dict = pickle.load(f)

        # Validación mínima de estructura
        if not isinstance(afd_dict, dict):
            raise ValueError("❌ El archivo no contiene un diccionario válido.")

        if not all(k in afd_dict for k in ['transitions', 'accepted', 'initial']):
            raise ValueError("❌ El diccionario AFD cargado no tiene la estructura esperada.")

        print(f"✅ AFD cargado correctamente desde: {ruta}")
        print(f"   Estados: {len(afd_dict['transitions'])}, Estados de aceptación: {len(afd_dict['accepted'])}")
        return afd_dict

    except Exception as e:
        raise RuntimeError(f"❌ Error al cargar el AFD: {e}")