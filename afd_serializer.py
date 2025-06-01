import pickle
import os

def guardar_afd_pickle(afd_dict, mapping, ruta):
    data = {
        "afd": afd_dict,
        "mapping": mapping
    }
    with open(ruta, 'wb') as f:
        pickle.dump(data, f)

def cargar_afd_pickle(ruta):
    with open(ruta, 'rb') as f:
        data = pickle.load(f)
        afd_dict = data.get("afd", {})
        mapping = data.get("mapping", {})
        return afd_dict, mapping