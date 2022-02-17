# This Python file uses the following encoding: utf-8

# Programma server Echo 
# import socket

# HOST = ''                 # Nome simbolico che rappresenta il nodo locale
# PORT = 50007              # Porta non privilegiata arbitraria 
# s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# s.bind((HOST, PORT))
# s.listen(1)
# conn, addr = s.accept()
# print 'Connected by', addr
# while 1:
#     data = conn.recv(1024)
#     if not data: break
#     conn.send(data)
# conn.close()
# Programma client Echo
# import socket

# HOST = 'daring.cwi.nl'    # Il nodo remoto
# PORT = 50007              # The La stessa porta usata dal server
# s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# s.connect((HOST, PORT))
# s.send('Hello, world')
# data = s.recv(1024)
# s.close()
# print 'Received', `data`

import socket
import logging

from time            import sleep,localtime,strftime
from oggetto         import oggetto

ATTESA_CICLO_PRINCIPALE = 0.01

class comunicazione_tcp(oggetto):
    def __init__(self,
                 file_configurazione,
                 coda_ipc_entrata,
                 lock_ipc_entrata,
                 coda_ipc_uscita,
                 lock_ipc_uscita):
        super().__init__(coda_ipc_entrata,
                         lock_ipc_entrata,
                         coda_ipc_uscita,
                         lock_ipc_uscita)

        logging.info(type(self).__name__ + " inizializzazione " + str(strftime("%H:%M:%S")))

        ##################### LETTURA DELLE IMPOSTAZIONI #######################
        self.file_configurazione = file_configurazione
        configurazione       = []
        lista_configurazione = []
        impostazioni         = []
        self.lista_segnali   = []
        self.server          = False
        # Leggi le impostazioni dal file configurazione e scompattale in una
        # lista di liste
        with open(file_configurazione) as f:
            configurazione = f.readlines()
        lista_configurazione[:] = [x.strip() for x in configurazione]
        # La lista delle impostazioni è una lista di liste, così da permettere
        # indici non unici. Per ogni lista (impostazione) trovata, il primo
        # elemento della lista è il nome dell'impostazione e il secondo
        # elemento è il valore dell'impostazione
        for impostazione in lista_configurazione:
            nome,valore = impostazione.split(" ")
            impostazioni.append([nome,valore])
        ################# FINE LETTURA IMPOSTAZIONI ######################

        logging.info(type(self).__name__ + " Fine lettura impostazioni " + str(strftime("%H:%M:%S")))

        for impostazione in impostazioni:
            nome,valore = impostazione
            if nome == "station":
                self.station = valore
                print("Server : ",self.station)
            elif nome == "server_address":
                self.server_address = valore
                print("Server Address: ",self.server_address)
            elif nome == "port":
                self.port = int(valore)
                print("Port : ",self.port)

    ############################ AVVIA PROCESSO ############################
    def avvia(self):
        pacchetto_segnale_entrata = []
        segnale                   = ""
        mittente                  = ""
        destinatario              = ""
        timestamp                 = 0

        errore_connessione        = False

        ###################### INIZIALIZZA IL SOCKET #####################

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        #################### INIZIO ATTIVAZIONE SERVER ###################

        if self.station == "server":
            self.socket.bind((self.server_address,self.port))

            logging.info(type(self).__name__ + " avvio server TCP" )

            self.socket.listen(1) # 5 è il numero (massimo) di connessioni prima di non accettarne altre
            logging.info(type(self).__name__ + " server TCP avviato")

        #################### FINE ATTIVAZIONE SERVER ###################

        ###################### INIZIO PARTE SERVER #########################
        # The important thing to understand now is this: this is all a “server”
        # socket does. It doesn’t send any data. It doesn’t receive any data.
        # It just produces “client” sockets. 
        # Each clientsocket is created in response to some other “client” socket
        # doing a connect() to the host and port we’re bound to. 
        # As soon as we’ve created that clientsocket, we go back to listening 
        # for more connections. 
        # The two “clients” are free to chat it up - they are using some dynamically
        # allocated port which will be recycled when the conversation ends.
            while True:
                # accetta connessioni dall'esterno
                try:
                    self.conn, self.client_address = self.socket.accept()

                    logging.info(type(self).__name__ + " Connesso da " + self.client_address)

                except:
                    errore_connessione = True
                if not errore_connessione:
                    break
                sleep(ATTESA_CICLO_PRINCIPALE)

            logging.info(type(self).__name__ + " ascoltando sulla porta " + str(self.port))

            while True:
                pacchetto_segnale_entrata[:] = []
                segnale                      = ""
                mittente                     = ""
                destinatario                 = ""
                timestamp                    = 0

                with self.lock_segnali_entrata:
                    if not self.coda_segnali_entrata.empty():
                        pacchetto_segnale_entrata[:] = \
                                         self.coda_segnali_entrata.get_nowait()
                if len(pacchetto_segnale_entrata) == 4:
                    segnale,mittente,destinatario,timestamp = \
                                                      pacchetto_segnale_entrata
                    pacchetto_segnale_entrata[:] = []
                elif len(pacchetto_segnale_entrata) == 3:
                    segnale,mittente,timestamp = pacchetto_segnale_entrata
                    pacchetto_segnale_entrata[:] = []
                elif len(pacchetto_segnale_entrata) == 0:
                    pass
                else:
                    with self.lock_segnali_uscita:
                        self.coda_segnali_uscita.put_nowait(
                                                        ["segnale mal formato",
                                                         ""])
                    pacchetto_segnale_entrata[:]
                    sleep(ATTESA_CICLO_PRINCIPALE)
                    continue

                if segnale == "stop":
                    clientsocket.close()
                    with self.lock_segnali_uscita:
                        self.coda_segnali_uscita.put_nowait(["stop", \
                                                            "gestore_segnali"])
                    return int(-1)


                dati = self.conn.recv(1024).decode('utf-8')
                if dati != "":
                    if dati.find("CIAO DA MODULO MONITOR") >= 0:
                        self.conn.send(dati)
                self.conn.close()
                sleep(ATTESA_CICLO_PRINCIPALE)

        ###################### FINE PARTE SERVER #######################
        
        else:

        ################### INIZIO ATTIVAZIONE CLIENT ##################

            self.socket.connect((self.server_address,self.port))

            logging.info(type(self).__name__ + " connettendo a " + str(self.server_address) + ":" + str(self.port))

            logging.info(type(self).__name__ + " connesso a " + str(self.server_address) + ":" + str(self.port))

            ################### INIZIO ATTIVAZIONE CLIENT ##################

            logging.info(type(self).__name__ + " Comunicazione TCP inizializzata")

            ##################### FINE INIZIALIZZAZIONE ####################

            ##################### INIZIO PARTE CLIENT ######################
            dati = ""

            while True:
                pacchetto_segnale_entrata[:] = []
                segnale                      = ""
                mittente                     = ""
                destinatario                 = ""
                timestamp                    = 0

                with self.lock_segnali_entrata:
                    if not self.coda_segnali_entrata.empty():
                        pacchetto_segnale_entrata[:] = \
                                         self.coda_segnali_entrata.get_nowait()
                if len(pacchetto_segnale_entrata) == 4:
                    segnale,mittente,destinatario,timestamp = \
                                                      pacchetto_segnale_entrata
                    pacchetto_segnale_entrata[:] = []
                elif len(pacchetto_segnale_entrata) == 3:
                    segnale,mittente,timestamp = pacchetto_segnale_entrata
                    pacchetto_segnale_entrata[:] = []
                elif len(pacchetto_segnale_entrata) == 0:
                    pass
                else:
                    with self.lock_segnali_uscita:
                        self.coda_segnali_uscita.put_nowait(
                                             clientsocket           ["segnale mal formato",
                                                         ""])
                    pacchetto_segnale_entrata[:]
                    sleep(ATTESA_CICLO_PRINCIPALE)
                    continue

                if segnale == "stop":
                    self.socket.close()
                    with self.lock_segnali_uscita:
                        self.coda_segnali_uscita.put_nowait(["stop", \
                                                            "gestore_segnali"])
                    return int(-1)


                elif segnale == "CIAO DA MODULO MONITOR":
                    try:
                        self.invia_dati("CIAO DA MODULO MONITOR")
                    except:
                        pass

                sleep(ATTESA_CICLO_PRINCIPALE)

        ###################### FINE PARTE CLIENT #########################
        
    def aggiornamento(self):
        pass

    def invia_dati(self,dati):
        if hasattr(self,'clientsocket'):
            try:
                self.socket.send(bytes(dati,'utf-8'))
                dati = self.socket.recv(1024)
                self.socket.close()
                logging.info(type(self).__name__ + " messaggio inviato su TCP")

            except:
                raise
        else:
            logging.error("Nessuna connessione stabilita")
