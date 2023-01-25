from flask import Flask, Response, request
from flask_sqlalchemy import SQLAlchemy
import json
import datetime 
from sqlalchemy.orm import validates
from osirisvalidator.string import *
from osirisvalidator.exceptions import ValidationException
import os
     
        
app = Flask(__name__)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config.from_object(__name__)

db = SQLAlchemy(app)

class Fotos(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False)
    local_foto = db.Column(db.String(100), nullable=False)
    data_foto = db.Column(db.DateTime, nullable=False)
    fotografo = db.Column(db.String(100), nullable=False)
    flash = db.Column(db.Boolean, nullable=False)

    def __init__(self, json):
        if json is None:
            return

        self.nome = json['nome'] if 'nome' in json else None
        self.local_foto = json['local'] if 'local' in json else None
        self.data_foto = json['data'] if 'data' in json else None
        self.fotografo = json['fotografo'] if 'fotografo' in json else None
        self.flash = json['flash'] if 'flash' in json else None

    @validates('nome')
    @not_empty(field='nome')
    @string_len(field='nome', min=1, max=100)
    def valida_nome(self, key, nome):
        return nome

    @validates('local_foto')
    @not_empty(field='local_foto')
    @string_len(field='local_foto', min=1, max=100)
    def valida_local_foto(self, key, local_foto):
        return local_foto

    @validates('fotografo')
    @not_empty(field='fotografo')
    @string_len(field='fotografo', min=1, max=100)
    def valida_fotografo(self, key, fotografo):
        return fotografo

    def to_json(self):
        data_foto = self.data_foto.strftime("%Y-%m-%dT%H:%M:%SZ")
        return {"id": self.id, "nome": self.nome, "local": self.local_foto, "data": data_foto, "fotografo": self.fotografo, "flash": self.flash}

# Consulta
@app.route("/fotos", methods=["GET"])
def seleciona_todas_fotos():
    fotos_objeto = Fotos.query.all()
    fotos_json = [fotos.to_json() for fotos in fotos_objeto]
    return gera_response(200, "fotos", fotos_json)

@app.route("/fotos/nome/<nome>", methods=["GET"])
def seleciona_fotos_nome(nome):
    fotos_objeto = Fotos.query.filter_by(nome=nome).first()
    return gera_response(200, "fotos", fotos_objeto.to_json())

@app.route("/fotos/fotografo/<fotografo>", methods=["GET"])
def seleciona_fotos_local(fotografo):
    fotos_objeto = Fotos.query.filter_by(fotografo=fotografo).all()
    fotos_json = [fotos.to_json() for fotos in fotos_objeto]
    return gera_response(200, "fotos", fotos_json)

@app.route("/fotos/local/<local>", methods=["GET"])
def seleciona_fotos_fotografo(local):
    fotos_objeto = Fotos.query.filter_by(local_foto=local).all()
    fotos_json = [fotos.to_json() for fotos in fotos_objeto]
    return gera_response(200, "fotos", fotos_json)

@app.route("/fotos/flash/<flash>", methods=["GET"])
def seleciona_fotos_flash(flash):
    fotos_objeto = Fotos.query.filter_by(flash=flash).all()
    fotos_json = [fotos.to_json() for fotos in fotos_objeto]
    return gera_response(200, "fotos", fotos_json)

@app.route("/fotos/datas/<data_inicio>/<data_final>", methods=["GET"])
def seleciona_fotos_data(data_inicio, data_final):
    fotos_objeto = Fotos.query.filter(Fotos.data_foto.between(data_inicio, data_final))
    fotos_json = [fotos.to_json() for fotos in fotos_objeto]
    return gera_response(200, "fotos", fotos_json)

@app.route("/fotos", methods=["POST"])
def insere_foto():
    body = request.get_json()
    try:
        foto = Fotos(body)
        db.session.add(foto)
        db.session.commit()
        return gera_response(201, "foto", foto.to_json(), "Foto inserida com sucesso")
    except ValidationException as ve:
        return gera_response(400, "erro", ve.errors, "Erro ao inserir foto")
    except Exception as e:
        if data_invalida(body["data"]):
            return gera_response(400, "erro", "Formato de data inválido", "Erro ao inserir foto")
        elif bool_invalido(body["flash"]):
            return gera_response(400, "erro", "Formato de flash inválido", "Erro ao inserir foto")
        else:
            return gera_response(400, "erro", str(e), "Erro ao inserir foto")

@app.route("/fotos/atualiza/<nome>", methods=["PUT"])
def atualizar_foto(nome):
    body = request.get_json()
    foto_objeto = Fotos.query.filter_by(nome=nome).first()
    try:
        if 'nome' in body: foto_objeto.nome = body['nome']
        if 'local' in body: foto_objeto.local_foto = body['local']
        if 'data' in body: foto_objeto.data_foto = body['data']
        if 'fotografo' in body: foto_objeto.fotografo = body['fotografo']
        if 'flash' in body: foto_objeto.flash = body['flash']
        db.session.add(foto_objeto)
        db.session.commit()
        return gera_response(201, "foto", foto_objeto.to_json(), "Foto atualizada com sucesso")
    except ValidationException as ve:
        return gera_response(400, "erro", ve.errors, "Erro ao atualizar foto")
    except Exception as e:
        if data_invalida(body["data"]):
            return gera_response(400, "erro", "Formato de data inválido", "Erro ao atualizar foto")
        elif bool_invalido(body["flash"]):
            return gera_response(400, "erro", "Formato de flash inválido", "Erro ao atualizar foto")
        else:
            return gera_response(400, "erro", str(e), "Erro ao atualizar foto")

@app.route("/fotos/deleta/<nome>", methods=["DELETE"])
def deleta_foto(nome):
    foto_objeto = Fotos.query.filter_by(nome=nome).first()
    try:
        db.session.delete(foto_objeto)
        db.session.commit()
        return gera_response(200, "foto", foto_objeto.to_json(), "Foto deletada com sucesso")
    except Exception as e:
        return gera_response(400, "erro", str(e), "Erro ao deletar foto")


def gera_response(status, nome_conteudo, conteudo=False, mensagem=False):
    body = {}
    body[nome_conteudo] = conteudo

    if(mensagem): body["mensagem"]=mensagem
    return Response(json.dumps(body), status=status, mimetype="aplication/json" )

def data_invalida(dt_str: str):
    try:
        datetime.datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    except:
        return True
    return False

def bool_invalido(flash: str):
    if (flash != False) and (flash != True):
        return True
    else: return False
        
if __name__ == '__main__':
    app.run(debug=True)