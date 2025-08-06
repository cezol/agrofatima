# config.py


import os
from dotenv import load_dotenv
from pymongo import MongoClient
acesso_pdf = ['LUIZ','JCB']
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_SID = os.getenv("TWILIO_SID")
IMGBB_API_KEY = os.getenv("IMGBB_API_KEY")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

GESTAO_Content_Type = 'application/json'
GESTAO_access_token = os.getenv("GESTAO_access_token")
GESTAO_secret_access_token = os.getenv("GESTAO_secret_access_token")
GESTAO_base_url = 'https://api.beteltecnologia.com/'
MONGODB_URI = os.getenv("MONGODB_URI")
cluster = MongoClient(MONGODB_URI, tls=True, tlsAllowInvalidCertificates=True)
db = cluster["Agrofatima"]
db_users = db["users"]
db_lista = db["lista_de_compras"]
db_lista_sinezia = db['lista_de_compras_sinezia']
PROMPT_DOC2 = """Analise o documento fornecido e extraia as seguintes informações de forma estruturada:

ara cada nota fiscal, gere um dicionario python separado com os campos:

{
  "cpf_cnpj": "<CNPJ ou CPF do *EMISSOR*>",
  "valor_produtos": <float>,
  "frete": <float>,
  "outras_despesas": <float>,
  "desconto": <float>,
  "valor_total_nota": <float>,
  "DANFE": "<número da nota se houver>",
  "data_emissao": "<yyyy-mm-dd>",
  "pagamentos": [
    {"valor": <float>, "vencimento": "<yyyy-mm-dd>"},
    ...
  ]
}

Regras:
- Todos os valores devem estar no formato numérico (float), sem aspas.
- Se houver mais de um pagamento ou fatura, inclua todos no array `pagamentos`.
- Se não houver uma informação, coloque '0'.
- Retorne **apenas o dicionario python**, sem explicações, cabeçalhos ou comentários.

Se o documento não contiver notas fiscais, retorne uma lista vazia: `[]`.

"""
PROMPT_DOC = """Analise o documento fornecido e extraia as seguintes informações na ordem:
1. Tipo de documento (NF, NFS, BL)
2. CNPJ ou CPF do emissor
3. Valor líquido
4. Valor bruto
5. Data de emissão (DD/MM/AAAA)
6. Data de vencimento (DD/MM/AAAA)
7. Número DANFE

Se não encontrar algum campo, use "None".

⚠️ A resposta deve ser apenas uma linha, em formato CSV, sem cabeçalho, sem comentários, sem aspas, sem colchetes e 
sem qualquer texto adicional. Apenas os dados, separados por vírgulas.
"""
PROMPT_AUDIO_ADD = """A partir do áudio recebido, extraia os itens agrícolas solicitados para compra, no contexto de uma fazenda de produção de café.

Para cada item mencionado, identifique:
- O nome do item (em letras minúsculas).
- A quantidade associada (com unidade, se aplicável).

⚠️ Responda com uma lista de dicionários no formato Python, como no exemplo abaixo:

[
  {"item": "adubo", "quantidade": "10 sacos"},
  {"item": "sementes de café", "quantidade": "5 kg"},
  {"item": "herbicida", "quantidade": "2 litros"}
]

⚠️ Não adicione explicações, nem texto adicional. Apenas a lista."""
PROMPT_AUDIO_REMOVE = """A partir do áudio recebido, extraia os itens agrícolas solicitados para remocao de uma lista, no contexto de uma fazenda de produção de café.

Para cada item mencionado, identifique:
- O nome do item (em letras minúsculas).
- A quantidade associada (se aplicável).

⚠️ Responda com uma lista de dicionários no formato Python,tudo em letra minuscula, como no exemplo abaixo:

[
  {"item": "adubo", "quantidade": "10 sacos"},
  {"item": "sementes de café", "quantidade": "5 kg"},
  {"item": "herbicida", "quantidade": "2 litros"}
]

⚠️ Não adicione explicações, nem texto adicional. Apenas a lista."""
PROMPT_FILTRAGEM = """
Você é um assistente de uma empresa agrícola que recebe comandos por áudio.

Sua tarefa é identificar qual é a intenção principal do usuário com base no texto transcrito do áudio. As intenções possíveis são:

- "adicionar": se o usuário estiver dizendo o que quer comprar, como produtos, insumos agrícolas etc.
- "remover": se o usuário estiver pedindo para retirar ou apagar algum item da lista de compras.
- "limpar": se o usuário estiver pedindo para apagar, limpar, deletar toda a lista. 
- "telefone": se o usuário estiver pedindo o número de telefone de um colaborador.
⚠️ Responda com **apenas** uma dessas quatro palavras: adicionar, remover, limpar ou telefone.
"""
PROMPT_TELEFONE = """
A partir da mensagem de voz recebida, extraia o nome completo do colaborador para o qual está sendo solicitado o telefone.

📌 Considere que o nome pode ser dito de forma parcial, composta ou com detalhes fonéticos, como:
- "com Z"
- "com S"
- "com dois Ls"
- "termina com TH"
- "com H mudo"
- "com C e não com K"
Essas pistas devem ser consideradas para tentar identificar a grafia mais provável do nome, mesmo que nem todas as letras sejam claramente pronunciadas.

⚠️ Extraia somente o nome mencionado, sem o cargo, nem outros dados.  
⚠️ A resposta deve conter apenas uma lista Python com **cada parte do nome** como strings separadas e **em letras minúsculas**, sem pontuação.

📌 Exemplo:

Entrada (áudio):  
"Quero o telefone do João Vítor com dois tês e h no final"

Saída:
["joao", "vittorh"]

Entrada:  
"Telefone do Julio Cezar, com z e sem acento"

Saída:
["julio", "cezar"]

⚠️ Não adicione explicações ou texto adicional. Apenas a lista, no formato exato solicitado.
"""





