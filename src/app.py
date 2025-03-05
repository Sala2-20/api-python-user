from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flasgger import Swagger  # Importar Swagger
from flask_cors import CORS
import bcrypt
import json

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Inicializar Swagger
swagger = Swagger(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://sql8765576:5IicxCw7LJ@sql8.freesqldatabase.com:3306/sql8765576'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)
salt = bcrypt.gensalt()

class Usuarios(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    contrasenia = db.Column(db.String(60), nullable=False)
    
    def __init__(self, nombre, contrasenia):
        self.setNombre(nombre)
        contrasenia = contrasenia.encode('utf-8')
        self.setContrasenia(contrasenia)
        
    def setNombre(self, nombre):
        self.nombre = nombre
        
    def setContrasenia(self, contrasenia):
        self.contrasenia = bcrypt.hashpw(contrasenia, salt).decode('utf-8')

# Crear las tablas
with app.app_context():
    db.create_all()

class UsuarioSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Usuarios
        fields = ('id', 'nombre', 'contrasenia')

usuario_schema = UsuarioSchema()
usuarios_schema = UsuarioSchema(many=True)

@app.route('/usuarios', methods=['POST'])
def create():
    """
    Crear un nuevo usuario
    ---
    tags:
      - Usuarios
    parameters:
      - name: usuario
        in: body
        type: object
        required: true
        schema:
          type: object
          properties:
            nombre:
              type: string
              description: Nombre del usuario
            contrasenia:
              type: string
              description: Contraseña del usuario
    responses:
      200:
        description: Usuario creado con éxito
      400:
        description: Error en los datos o usuario ya existe
    """
    try:
        data = request.get_json()
        
        print("Datos recibidos:", data)
        if not data or 'nombre' not in data or 'contrasenia' not in data:
            return {'creado': False}, 400
        
        nombre = data['nombre']
        contrasenia = data['contrasenia']
        
        buscar = buscarUsu(nombre, contrasenia)
        if buscar["encontrado"]:
            return {'creado': True}, 200
        
        new_usuario = Usuarios(nombre, contrasenia)
        db.session.add(new_usuario)
        db.session.commit()
    
        return {'creado': True}, 200
    except Exception as e:
        print(e)
        return {'creado': False}, 400

@app.route('/usuarios', methods=['GET'])
def show():
    """
    Obtener la lista de todos los usuarios
    ---
    tags:
      - Usuarios
    parameters:
      - name: nombre
        in: query
        type: string
        description: Nombre del usuario a buscar
      - name: contrasenia
        in: query
        type: string
        description: Contraseña del usuario a buscar
    responses:
      200:
        description: Lista de usuarios o un usuario específico
        schema:
          type: array
          items:
            $ref: '#/definitions/Usuario'
      400:
        description: Error al obtener los usuarios
    """
    try:
        nombre = request.args.get('nombre')
        contrasenia = request.args.get('contrasenia')

        if nombre and contrasenia:
            return buscarUsu(nombre, contrasenia), 200
          
        usuarios = Usuarios.query.all()
        resultados = usuarios_schema.dump(usuarios)
    
        return jsonify(resultados)
    except:
        return {'message': 'Error'}, 400

@app.route('/usuarios/<id>', methods=['GET'])
def show_usuario(id):
    """
    Obtener los detalles de un usuario por ID
    ---
    tags:
      - Usuarios
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: ID del usuario
    responses:
      200:
        description: Detalles del usuario
        schema:
          $ref: '#/definitions/Usuario'
      400:
        description: Error al obtener el usuario
    """
    try:
        usuarios = Usuarios.query.get(id)
    
        return usuario_schema.jsonify(usuarios)
    except:
        return {'message': 'Error al crear usuario'}, 400

@app.route('/usuarios/<id>', methods=['PUT'])
def update(id):
    """
    Actualizar los datos de un usuario
    ---
    tags:
      - Usuarios
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: ID del usuario
      - name: usuario
        in: body
        required: true
        schema:
          type: object
          properties:
            nombre:
              type: string
            contrasenia:
              type: string
    responses:
      200:
        description: Usuario actualizado correctamente
        schema:
          $ref: '#/definitions/Usuario'
      400:
        description: Error al actualizar el usuario
    """
    try:
        usuario = Usuarios.query.get(id)
        nombre = request.json["nombre"]
        contrasenia = request.json["contrasenia"].encode('utf-8')
        if nombre and contrasenia:
            usuario.nombre = nombre
            usuario.contrasenia = bcrypt.hashpw(contrasenia, salt).decode('utf-8')
            
            db.session.commit()
    
        return usuario_schema.jsonify(usuario)
    except:
        return {'message': 'Error al crear usuario'}, 400

@app.route('/usuarios/<id>', methods=['DELETE'])
def destroy(id):
    """
    Eliminar un usuario por ID
    ---
    tags:
      - Usuarios
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: ID del usuario a eliminar
    responses:
      200:
        description: Usuario eliminado correctamente
        schema:
          $ref: '#/definitions/Usuario'
      400:
        description: Error al eliminar el usuario
    """
    try:
        usuario = Usuarios.query.get(id)
        
        db.session.delete(usuario)
        db.session.commit()
    
        return usuario_schema.jsonify(usuario)
    except:
        return {'message': 'Error al crear usuario'}, 400

def buscarUsu(nombre, contrasenia):
    usuarios = Usuarios.query.all()
    resultados = usuarios_schema.dump(usuarios)

    for obj in resultados:
        if obj["nombre"] == nombre and bcrypt.checkpw(contrasenia.encode('utf-8'), obj["contrasenia"].encode('utf-8')):
            return {"encontrado": True, "id": obj["id"]}
        
    return {"encontrado": False}
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
