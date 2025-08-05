# modules/utils.py

def get_raw_itens(db_lista):
    doc = db_lista.find_one({}, {"_id": 0, "ITENS": 1})
    return [
        f"{item['item']} ({item['quantidade']})"
        for item in doc.get("ITENS", [])
    ] if doc else [],doc

def format_lista(db_lista):
    doc = db_lista.find_one({}, {"_id": 0, "ITENS": 1})
    itens = doc.get("ITENS", []) if doc else []
    if not itens:
        return "❌ Sua lista está vazia."
    return "\n".join(
        f"• {item['item']} {item['quantidade']} _({item['nome']})_"
        for item in itens
    )
def remover_duplicados(lista):
    resultado = []
    vistos = set()
    for item in lista:
        if item not in vistos:
            vistos.add(item)
            resultado.append(item)
    return resultado