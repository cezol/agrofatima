
import requests
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from modules.session import UserSession
from modules.menu import MenuManager
from modules.document import DocumentHandler
from config import db_users, db_lista, db_lista_sinezia, OPENAI_API_KEY, TWILIO_AUTH_TOKEN, TWILIO_SID, PROMPT_FILTRAGEM, \
    PROMPT_AUDIO_REMOVE, PROMPT_AUDIO_ADD, acesso_pdf, PROMPT_TELEFONE
import openai

openai.api_key = OPENAI_API_KEY
app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def reply():
    number = (request.form.get("From") or "").replace("whatsapp:+5527", "")
    text = (request.form.get("Body") or "").strip()
    media_url = request.form.get("MediaUrl0", "")
    media_type = request.form.get("MediaContentType0", "")
    num_media = int(request.form.get("NumMedia", 0))
    res = MessagingResponse()

    user = UserSession(number, db_users)
    if not user.is_authorized():
        return str(res)
    if user.get_nome() == 'JCBF':
        lista = db_lista_sinezia
    else:
        lista = db_lista
    if text == 'aa':
        ENCONTRADOS = MenuManager.buscarTelefones('["julio", "cesar"]')
        if ENCONTRADOS:
            for i, (nome, telefone) in enumerate(ENCONTRADOS, 1):
                res.message((f"{i}. {nome} - {telefone}"))
        else:
            res.message(f'nao encontrado')
        return str(res)
    if text == "..":
        user.toggle_bot(res)
        if user.is_bot_active():
            res.message(MenuManager.menu_principal(user.get_loja(), lista,user.get_nome()))
            user.set_status("main")
        return str(res)
    if not user.is_bot_active():
        return str(res)
    if media_url and ("pdf" in media_type.lower() or "image" in media_type.lower()) and user.get_nome() in acesso_pdf:
        res.message(DocumentHandler.handle_upload(media_type, media_url, res, user))
        return str(res)
    if media_url and "audio" in media_type:
        try:
            response = requests.get(media_url, auth=(TWILIO_SID, TWILIO_AUTH_TOKEN))
            response.raise_for_status()
            audio_data = response.content
            audio_path = "/tmp/audio.ogg"
            with open(audio_path, "wb") as f:
                f.write(audio_data)
            with open(audio_path, "rb") as audio_file:
                transcript = openai.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
                text = transcript.text
            gpt_response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system",
                     "content": PROMPT_FILTRAGEM},
                    {"role": "user",
                     "content": f"O usuário disse: '{text}'"}
                ]
            )
            option = gpt_response.choices[0].message.content.strip()
            if option == 'adicionar':
                gpt_response = openai.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system",
                         "content": PROMPT_AUDIO_ADD},
                        {"role": "user",
                         "content": f"O usuário disse: '{text}'. Interprete como um item para adicionar à lista de compras, sem explicações."}
                    ]
                )
                text = gpt_response.choices[0].message.content.strip()
                MenuManager._handle_lista_add(text, res, user, lista)
            elif option == 'remover':
                gpt_response = openai.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system",
                         "content": PROMPT_AUDIO_REMOVE},
                        {"role": "user",
                         "content": f"O usuário disse: '{text}'. Interprete como um item para remover de uma lista de compras, sem explicações."}
                    ]
                )
                text = gpt_response.choices[0].message.content.strip()
                MenuManager.handle_remove_item(text, res, user, lista)
            elif option == 'limpar':
                MenuManager.clear_lista(res, user, lista)
            elif option == 'telefone':
                gpt_response = openai.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system",
                         "content": PROMPT_TELEFONE},
                        {"role": "user",
                         "content": f"O usuário disse: '{text}'"}
                    ]
                )
                nome = gpt_response.choices[0].message.content.strip()
                ENCONTRADOS = MenuManager.buscarTelefones(nome)
                print(nome)
                if ENCONTRADOS:
                    for i, (nome, telefone) in enumerate(ENCONTRADOS, 1):
                        res.message((f"{i}. {nome} - {telefone}"))
                else:
                    res.message(f'{nome}nao encontrado')
            return str(res)
        except Exception as e:
            res.message(f"❌ Erro ao transcrever áudio: {e}")
            return str(res)

    return MenuManager.process_input(text, res, user, lista)


if __name__ == "__main__":
    app.run()




