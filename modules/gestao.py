from datetime import datetime
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import json
import unicodedata

from config import GESTAO_access_token, GESTAO_secret_access_token, GESTAO_base_url


class GestaoAPI:
    def __init__(self):
        self.base_url = GESTAO_base_url
        self.headers = {
            'Content-Type': 'application/json',
            'access-token': GESTAO_access_token,
            'secret-access-token': GESTAO_secret_access_token
        }

    def get(self, endpoint, params):
        url = f"{self.base_url}{endpoint}?{urlencode(params)}"
        request = Request(url, headers=self.headers)
        try:
            with urlopen(request) as response:
                return json.loads(response.read())
        except Exception as e:
            print(f"Erro na requisição GET: {e}")
            return {}

    def post(self, endpoint, params):
        url = f"{self.base_url}{endpoint}"
        data = json.dumps(params).encode("utf-8")
        request = Request(url, data=data, headers=self.headers, method="POST")
        try:
            with urlopen(request) as response:
                status_code = response.getcode()
                body = response.read()
                return status_code, json.loads(body)
        except HTTPError as e:
            msg = e.read().decode()
            return e.code, {"erro": msg}
        except URLError as e:
            return 0, {"erro": str(e.reason)}
        except Exception as e:
            print(f"❌ Erro inesperado - {e}")
            return 0, {"erro": str(e)}


class FuncionarioAPI:
    def __init__(self):
        self.base_url = f"{GESTAO_base_url}funcionarios"
        self.headers = GestaoAPI().headers

    def _normalizar(self, texto):
        return unicodedata.normalize('NFKD', texto.lower()).encode('ASCII', 'ignore').decode('utf-8').strip()

    def listar_funcionarios(self, nome_tokens):
        tokens = json.loads(nome_tokens)
        normalizados = [self._normalizar(t) for t in tokens]
        pagina = 1
        encontrados = []

        while True:
            url = f"{self.base_url}?pagina={pagina}"
            try:
                req = Request(url, headers=self.headers)
                response = urlopen(req).read()
                data = json.loads(response)
                for f in data.get("data", []):
                    nome = f.get("nome", "")
                    if all(t in self._normalizar(nome) for t in normalizados):
                        encontrados.append((nome, f.get("telefone", "Sem telefone")))

                if not data.get("meta", {}).get("proxima_pagina"):
                    break
                pagina = data["meta"]["proxima_pagina"]

            except Exception as e:
                print(f"Erro ao buscar página {pagina}: {e}")
                break

        return encontrados


class NotaFiscal:
    LOJAS = {'AGRO': 313046, 'LDMB': 313950, 'JCBF': 317166}

    def __init__(self, csv, loja):
        self.api = GestaoAPI()
        self.loja = loja
        self.loja_id = self.LOJAS.get(loja)
        self.message = ''
        self.compra_id = ''
        self.cpf_cnpj = csv['cpf_cnpj']
        self.valor_produtos = csv['valor_produtos']
        self.frete = csv['frete']
        self.outras_despesas = csv['outras_despesas']
        self.desconto = csv['desconto']
        self.valor_total_nota = csv['valor_total_nota']
        self.DANFE = str(int(csv['DANFE'].replace('.', '')))
        self.data_emissao = csv['data_emissao']
        self.pagamentos = csv['pagamentos']
        self.fornecedor_id = self._buscar_fornecedor_id()
        if not self.fornecedor_id:
            self.message = ('Fornecedor não encontrado. Cadastre em:'
                           'https://gestaoclick.com/fornecedores/adicionar')
            return
        if self._verifica_duplicidade():
            return
        self._criar_nova_compra()

    def _buscar_fornecedor_id(self):
        r = self.api.get('fornecedores', {"cpf_cnpj": self.cpf_cnpj})
        return r.get('data', [{}])[0].get('id') if r.get('meta', {}).get('total_registros') else None

    def _verifica_duplicidade(self):
        for nome_loja, loja_id in self.LOJAS.items():
            r = self.api.get('compras', {"loja_id": loja_id, 'fornecedor_id': self.fornecedor_id})
            for c in r.get('data', []):
                if str(int(c['Compra']['numero_nfe'])) == str(self.DANFE):
                    self.compra_id = c['Compra']['id']
                    link = f"https://gestaoclick.com/compras/editar/{self.compra_id}"
                    self.message = (f"CANCELADO! Nota já existente na loja *{nome_loja}*: {link}\n"
                                    "Envie outro arquivo ou escolha uma opção:\n1️⃣ AGRO\n2️⃣ LDMB\n3️⃣ JCBF")
                    return True
        return False

    def _formatar_pagamentos(self):
        return [{"pagamento": {
                    "data_vencimento": p["vencimento"],
                    "valor": p["valor"],
                    "forma_pagamento_id": "3263239",
                    "plano_contas_id": "4878060"
                }} for p in self.pagamentos]

    def _criar_nova_compra(self):
        print(33)
        params = {
            "fornecedor_id": self.fornecedor_id,
            "loja_id": self.loja_id,
            "data_emissao": self.data_emissao,
            "situacao_id": 1170235,
            "valor_frete": self.frete,
            "numero_nfe": self.DANFE,
            "pagamentos": self._formatar_pagamentos(),
            "produtos": [{"produto": {"valor_custo": self.valor_produtos+self.outras_despesas-self.desconto}}]
        }
        status, r = self.api.post('compras', params)
        if status != 200:
            erro = r.get('erro', 'Erro desconhecido')
            self.message = (f"❌ Erro ao cadastrar nota na loja *{self.loja}*:\n{erro}\n"
                            "Verifique e tente novamente: https://gestaoclick.com/compras")
            return
        print('ssssssssssssssssssssssssssssssssssssss')
        self.compra_id = r['data']['id']
        link = f'https://gestaoclick.com/compras/editar/{self.compra_id}'
        parcelas = "".join(
            f"Parcela {i+1}: {p['vencimento']} — 💵 R$ {float(p['valor']):,.2f}\n"
            for i, p in enumerate(self.pagamentos)
        )
        self.message = (f"✅ Nota adicionada com sucesso!\n{link}\n"
                        f"🏬 Loja: {self.loja}\n💰 Valor: {self.valor_total_nota}\n📅 Emissão: {self.data_emissao}\n"
                        f"{parcelas}\nEnvie outro arquivo ou escolha:\n1️⃣ AGRO\n2️⃣ LDMB\n3️⃣ JCBF")
