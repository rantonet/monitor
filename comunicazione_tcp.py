# This Python file uses the following encoding: utf-8

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

            self.socket.listen()
            logging.info(type(self).__name__ + " server TCP avviato")

        #################### FINE ATTIVAZIONE SERVER ###################

        else:

        ################### INIZIO ATTIVAZIONE CLIENT ##################

            self.socket.connect((self.server_address,self.port))

            logging.info(type(self).__name__ + " connettendo a " + str(self.server_address) + ":" + str(self.port))

            logging.info(type(self).__name__ + " connesso a " + str(self.server_address) + ":" + str(self.port))

        ################### INIZIO ATTIVAZIONE CLIENT ##################

        logging.info(type(self).__name__ + " Comunicazione TCP inizializzata")

        ######################## FINE INIZIALIZZAZIONE #########################

        if self.station == "server":

        ###################### INIZIO PARTE SERVER #########################
            while True:
                try:
                    self.conn, self.client_address = self.socket.accept()

                    logging.info(type(self).__name__ + " inizio ascolto porta TCP")

                except:
                    errore_connessione = True
                if not errore_connessione:
                    break
                sleep(ATTESA_CICLO_PRINCIPALE)

            logging.info(type(self).__name__ + " ascoltando sulla porta " + str(self.port) + " dall'indirizzo " + str(self.client_address))

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
                    conn.close()
                    with self.lock_segnali_uscita:
                        self.coda_segnali_uscita.put_nowait(["stop", \
                                                            "gestore_segnali"])
                    return int(-1)


                dati = self.socket.recv(1024).decode('utf-8')
                if dati != "":
                    if dati.find("CIAO") >= 0:
                        print("CIAO")
                    elif dati.find("SONO IL MODULO MONITOR") >= 0:
                        PRINT("SONO IL MODULO MONITOR")

                sleep(ATTESA_CICLO_PRINCIPALE)

        ###################### FINE PARTE SERVER #########################
        
        else:

        ##################### INIZIO PARTE CLIENT ########################
            dati = ""
            #with open("codici_casse","a") as codici:
            #   pass
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
                    self.socket.close()
                    with self.lock_segnali_uscita:
                        self.coda_segnali_uscita.put_nowait(["stop", \
                                                            "gestore_segnali"])
                    return int(-1)


                elif segnale == "CIAO":
                    try:
                        self.invia_dati("CIAO")
                    except:
                        pass
                elif segnale == "SONO IL MODULO MONITOR":
                    try:
                        self.invia_dati("SONO IL MODULO MONITOR")
                    except:
                        pass
                elif segnale.find("CODICE") >= 0:
                    try:
                        self.invia_dati(segnale)
                    except:
                        pass
                sleep(ATTESA_CICLO_PRINCIPALE)

        ###################### FINE PARTE CLIENT #########################
        
    def aggiornamento(self):
        pass

    def invia_dati(self,dati):
        if hasattr(self,'conn'):
            try:
                self.conn.sendall(bytes(dati,'utf-8'))
                logging.info(type(self).__name__ + " messaggio inviato su TCP")

            except:
                raise
        else:
            logging.error("Nessuna connessione stabilita")
