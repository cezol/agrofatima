# modules/session.py
USER_MAP = {
    "996479181": "LEANDRO",
    "997543066": "JCBF",
    "999350358": "LUIZ",
    "981172066": "JCB"
}

class UserSession:
    def __init__(self, number, users_collection):
        self.number = number
        self.users = users_collection
        self.user = self.users.find_one({"number": number})
        nome = USER_MAP.get(self.number, "Usuário")
        if not self.user and self.number != '':
            self.users.insert_one({
                "number": number,
                "status": "main",
                "loja": "AGRO",
                "bot_active": True,
                "nome": nome,
            })
            self.user = self.users.find_one({"number": number})

    def get_status(self):
        return self.user.get("status", "main")
    def get_nome(self):
        return self.user.get("nome", "Usuário")

    def set_status(self, status):
        self.users.update_one({"number": self.number}, {"$set": {"status": status}})
        self.user["status"] = status

    def get_loja(self):
        return self.user.get("loja", "AGRO")

    def set_loja(self, loja):
        self.users.update_one({"number": self.number}, {"$set": {"loja": loja}})
        self.user["loja"] = loja

    def is_bot_active(self):
        return self.user.get("bot_active", False)

    def toggle_bot(self, res):
        new_status = not self.is_bot_active()
        self.users.update_one({"number": self.number}, {"$set": {"bot_active": new_status}})
        self.user["bot_active"] = new_status
        if new_status:
            from modules.texts import MENUS
            self.set_status("main")
        else:
            res.message("🤖🛑")
        return str(res)
    def is_authorized(self):
        return self.number in USER_MAP
    def get_temp_list(self):
        return self.user.get("lista_temp", [])
    def clear_temp_list(self):
        self.users.update_one({"number": self.number}, {"$unset": {"lista_temp": ""}})
        self.user.pop("lista_temp", None)




