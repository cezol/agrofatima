# modules/document.py
import json

import requests
import io
import openai
from config import TWILIO_SID, TWILIO_AUTH_TOKEN, IMGBB_API_KEY, PROMPT_DOC,PROMPT_DOC2
from modules.gestao import NotaFiscal

class DocumentHandler:
    @staticmethod
    def handle_upload(media_type, url, res, user):
        try:
            file = requests.get(url, auth=(TWILIO_SID, TWILIO_AUTH_TOKEN)).content
            if media_type == "application/pdf":
                return DocumentHandler._handle_pdf(file,user.get_loja())
            elif "image" in media_type:
                return DocumentHandler._handle_image(file, user.get_loja())
            else:
                res.message("❌ Tipo de arquivo não suportado.")
        except Exception as e:
            res.message(f"❌ Erro ao baixar o arquivo11: {e}")

        return str(res)


    @staticmethod
    def _handle_pdf(pdf_bytes, loja):
        try:
            upload = openai.files.create(
                file=("boleto.pdf", io.BytesIO(pdf_bytes), "application/pdf"),
                purpose="assistants"
            )

            messages = [{
                "role": "user",
                "content": [
                    {"type": "file", "file": {"file_id": upload.id}},
                    {"type": "text", "text": PROMPT_DOC2}
                ]
            }]

            completion = openai.chat.completions.create(
                model="gpt-4o",
                messages=messages
            )
            csv = completion.choices[0].message.content.strip()
            csv = csv.strip().removeprefix("```python").removesuffix("```").strip()
            csv = json.loads(csv)
            add_nota = NotaFiscal(csv, loja)
            mensagem = add_nota.message
        except Exception as e:
            mensagem = (f"❌ Erro ao processar PDF: {e}")
        return str(mensagem)
    @staticmethod
    def _handle_image(image_bytes,loja):
        try:
            response = requests.post(
                "https://api.imgbb.com/1/upload",
                params={"key": IMGBB_API_KEY, "expiration": "61"},
                files={"image": image_bytes}
            )
            response.raise_for_status()

            image_url = response.json()["data"]["url"]

            messages = [{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": image_url}},
                    {"type": "text", "text": PROMPT_DOC}
                ]
            }]

            completion = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages
            )
            result = completion.choices[0].message.content.strip()
            mensagem = result
            print(result)
        except Exception as e:
            mensagem = f"❌ Erro ao processar imagem: {e}"
        return str(mensagem)

