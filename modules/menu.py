# modules/menu.py
from config import acesso_pdf
from modules.gestao import FuncionarioAPI
from .utils import format_lista, get_raw_itens, remover_duplicados
import ast


class MenuManager:
    @staticmethod
    def process_input(text, res, user, db_lista):
        status = user.get_status()
        if status == "main":
            return MenuManager._handle_main(text, res, user, db_lista)

        elif status == "remove_item":
            return MenuManager.handle_remove_item(text, res, user, db_lista)

        elif status == "confirm_clear":
            return MenuManager._handle_confirm_clear(text, res, user, db_lista)

        res.message("❌ Por favor, digite uma opção válida.")
        return str(res)

    @staticmethod
    def menu_principal(loja="AGRO", db_lista='', nome=None):

        menu_principal = (
                "*AgroFátima ☕🌱*\n\n"
                f"🛒 *Lista de compras:*\n{format_lista(db_lista)}\n\n" +
                (f"0️⃣ Para Limpar Lista 🗑️\n\n" if format_lista(db_lista)[0] != '❌' else '') +
                "🎙️ Envie um áudio para adicionar ou remover itens à lista de compras!\n"
                "📞 Envie um áudio para solicitar o telefone de um *fornecedor* ou *colaborador*\n\n"

        )

        if nome in acesso_pdf:
            return (f'{menu_principal}\n'
                    "📎📤 Envie a nota fiscal ou boleto (PDF ou imagem):\n"
                    f"🏬 Loja selecionada: *{loja}*\n"
                    "🛠️ Se quiser trocar a loja, selecione uma das opções abaixo:\n"
                    "1️⃣ AGRO\n"
                    "2️⃣ LDMB\n"
                    "3️⃣ JCBF\n\n"
                    )
        else:
            return menu_principal

    @staticmethod
    def buscarTelefones(nome):
        return FuncionarioAPI().listar_funcionarios(nome)

    @staticmethod
    def _handle_main(text, res, user, db_lista):
        lojas = {"1": "AGRO", "2": "LDMB", "3": "JCBF"}
        if text == '0':
            return MenuManager.clear_lista(res, user, db_lista)
        elif text in lojas and user.get_nome() in acesso_pdf:
            user.set_loja(lojas[text])
            res.message(MenuManager.menu_principal(user.get_loja(), db_lista, user.get_nome()))
        else:
            res.message(MenuManager.menu_principal(user.get_loja(), db_lista, user.get_nome()))
        return str(res)

    @staticmethod
    def clear_lista(res, user, db_lista):
        if get_raw_itens(db_lista)[0]:  # acessa só a lista de itens
            user.set_status("confirm_clear")
            res.message("⚠️ Digite `SIM` para apagar todos os itens ou 0️⃣ para cancelar.")
        else:
            res.message(MenuManager.menu_principal(user.get_loja(), db_lista, user.get_nome()))
            user.set_status("main")
        return str(res)

    @staticmethod
    def _handle_lista_add(text, res, user, db_lista):
        try:
            lista_itens = ast.literal_eval(text)
            for item_dict in lista_itens:
                if "item" in item_dict and "quantidade" in item_dict:
                    item = item_dict["item"].strip()
                    quantidade = item_dict["quantidade"].strip()
                    nome = user.get_nome()
                    novo_item = {
                        "item": item,
                        "quantidade": quantidade,
                        "nome": nome
                    }
                    if user.get_nome() == 'JCBF':
                        print('jcbfffffffffffffffffff')
                    db_lista.update_one({}, {"$push": {"ITENS": novo_item}}, upsert=True)
            res.message(f"*✅ Lista atualizada!!*"+ "\n\n" + MenuManager.menu_principal(user.get_loja(), db_lista, user.get_nome()))
        except:
            res.message('FORMATAO INVALIDO')
        return str(res)

    @staticmethod
    def handle_remove_item(text, res, user, db_lista):
        try:
            print(00000)
            lista_itens = ast.literal_eval(text)
            doc = db_lista.find_one({}, {"_id": 0, "ITENS": 1})
            itens = doc.get("ITENS", []) if doc else []

            removidos = []
            nao_encontrados = []
            print(1)
            for item_audio in lista_itens:
                nome_item = item_audio.get("item", "").strip().lower()
                encontrado = False
                print(2)
                for item_salvo in itens:
                    if item_salvo.get("item", "").strip().lower() == nome_item:
                        db_lista.update_one({}, {"$pull": {"ITENS": item_salvo}})
                        removidos.append(item_salvo["item"])
                        encontrado = True
                        break

                if not encontrado:
                    nao_encontrados.append(nome_item)
            print(3)
            nao_encontrados = remover_duplicados(nao_encontrados)
            
            msg = ""
            if removidos:
                msg += "❌ Itens removidos:\n" + "\n".join(f"• {i}" for i in removidos) + "\n"
            if nao_encontrados:
                msg += "\n⚠️ Não encontrados na lista:\n" + "\n".join(f"• {i}" for i in nao_encontrados)
            print(4)
            res.message((msg or "⚠️ Nenhum item válido informado.") + "\n" +
                        MenuManager.menu_principal(user.get_loja(), db_lista, user.get_nome()))

        except Exception as e:
            res.message(f"❌ Erro ao processar a remoção:\n{e}")
        return str(res)

    @staticmethod
    def _handle_confirm_clear(text, res, user, db_lista):
        if text.upper() == "SIM":
            db_lista.update_one({}, {"$set": {"ITENS": []}})
            user.set_status("main")
            res.message("🧹 *Lista apagada com sucesso!*\n\n" + MenuManager.menu_principal(user.get_loja(), db_lista,
                                                                                           user.get_nome()))
        elif text == "0":
            user.set_status("main")
            res.message(
                "❌ Ação cancelada.\n\n" + MenuManager.menu_principal(user.get_loja(), db_lista, user.get_nome()))
        else:
            res.message("❌ Digite `SIM` para confirmar ou 0️⃣ para cancelar.")
        return str(res)

