import grpc
import mangle_pb2
import mangle_pb2_grpc

def run():
    # Establece una conexión con el servidor gRPC.
    with grpc.insecure_channel('localhost:8080') as channel:
        # Crea un cliente (stub) para llamar a los métodos del servidor.
        stub = mangle_pb2_grpc.MangleStub(channel)
        
        # Define la consulta que queremos hacer.
        query = "contacto_prioritario(X)."
        print(f"--- Enviando consulta: {query} ---")
        
        # Crea el objeto de solicitud y llama al método 'Query' del servidor.
        response = stub.Query(mangle_pb2.QueryRequest(query=query))
        
        # Itera sobre los resultados y los imprime.
        print("--- Resultados recibidos ---")
        for result in response:
            print(result)

if __name__ == '__main__':
    run()
