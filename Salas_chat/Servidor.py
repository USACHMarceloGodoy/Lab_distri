import socket
import threading
import pymongo
from datetime import datetime

# Conexión a la base de datos MongoDB
cliente = pymongo.MongoClient("mongodb://localhost:27017/")
db = cliente["stream"]
salas = db["salas"]
users = db["users"]

# Diccionario en memoria para conexiones activas
connections = {}

# Función para manejar las conexiones de los clientes
def handle_client(client_socket, address):
    try:
        # Solicitar el nombre de usuario
        client_socket.send("Nombre de usuario: ".encode())
        username = client_socket.recv(1024).decode().strip()

        # Al momento de seleccionar un stream desde el frontend se debe enviar el nombre del streamer y el nombre del stream
        # Ejemplo: streamer_name = "Xodaaaa", stream_name = "Al vardoc lo engañaron de nuevo"
        # De esta manera podemos diferenciar entre los distintos streams de un distinto streamer en los resubido
        # Y tambien podemos diferenciar entre los distintos streams de distintos streamers (Nos enfocaremos ahora en eso)
        # Solicitar el nombre del streamer
        client_socket.send("Nombre del streamer: ".encode())
        streamer_name = client_socket.recv(1024).decode().strip()

        # Solicitar el nombre del stream
        client_socket.send("Nombre del stream: ".encode())
        stream_name = client_socket.recv(1024).decode().strip()

        # Verificar si la sala existe en MongoDB, si no, crearla
        # Debiesemos crear de por si la DB si no existe, pero por simplicidad lo dejaremos asi
        specific_room = salas.find_one({"streamer": streamer_name, "stream": stream_name})
        if not specific_room:
            salas.insert_one({"streamer": streamer_name, "stream": stream_name, "messages": []})

        # Guardar usuario en MongoDB si no existe
        # Esto de por si debiese estar en el frontend, pero ya que de momento no implementaremos cuentas como tal lo dejaremos asi
        
        # Creamos la llave única para la sala
        room_key = f"{streamer_name}-{stream_name}"  # Llave única para la sala
        if room_key not in connections:
            connections[room_key] = []
        connections[room_key].append((client_socket, username))

        # Indicamos al usuario que se ha unido a la sala
        client_socket.send(f"Bienvenido al stream '{stream_name}' de {streamer_name}, {username}!\n".encode())
        broadcast(f"{username} se ha unido al stream '{stream_name}' de {streamer_name}.\n", room_key, client_socket)

        # Manejo de mensajes
        while True:
            
            # Necesitamos un comando para salir de la sala, normalmente seria el cerrar el chat para dejar de recibir mensajes
            message = client_socket.recv(1024).decode().strip()
            if message.lower() == "/salir":
                break  

            # Guardar mensaje en MongoDB
            #De esa manera se pueden retrasmitir despues
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            salas.update_one(
                {"streamer": streamer_name, "stream": stream_name},
                {"$push": {"messages": {"username": username, "message": message, "timestamp": timestamp}}}
            )

            # Enviar mensaje a otros usuarios en la sala
            broadcast(f"{username} ({timestamp}): {message}\n", room_key, client_socket)

    except Exception as e:
        print(f"Error con {address}: {e}")
    finally:
        # Manejar desconexión del cliente
        client_socket.close()
        if room_key in connections:
            connections[room_key] = [
                conn for conn in connections[room_key] if conn[0] != client_socket
            ]
            #Mensaje del usuario que se ha desconectado
            broadcast(f"{username} ha salido del stream '{stream_name}' de {streamer_name}.\n", room_key)
        print(f"Conexión cerrada: {address}")

# Función para enviar mensajes a todos los usuarios de una sala
def broadcast(message, room_key, sender_socket=None):
    """Envía un mensaje a todos los usuarios de una sala excepto al remitente."""
    if room_key in connections:
        for client_socket, _ in connections[room_key]:
            if client_socket != sender_socket:
                try:
                    client_socket.send(message.encode())
                except:
                    pass

# Función para iniciar el servidor
def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", 6789))
    server.listen(5)
    print("Servidor iniciado en el puerto 6789.")

    while True:
        client_socket, address = server.accept()
        print(f"Conexión nueva: {address}")
        threading.Thread(target=handle_client, args=(client_socket, address)).start()

if __name__ == "__main__":
    start_server()
