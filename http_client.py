# This Python file uses the following encoding: utf-8

import http.client
import logging

from time            import sleep,time
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
        logging.info(type(self).__name__ + " inizializzazione")
        ##################### Lettura delle impostazioni #######################
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
        ################# Fine lettura delle impostazioni ######################
        for impostazione in impostazioni:
            nome,valore = impostazione
            if nome == "server":
                self.server = valore
                #print(impostazione)
                print("Server : ",self.server)                
            elif nome == "indirizzo":
                self.indirizzo_server = valore
                #print(impostazione)
                print("Indirizzo Server: ",self.indirizzo_server)
            elif nome == "porta":
                self.porta = int(valore)
                #print(impostazione)
                print("Porta : ",self.porta)

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        if self.server == True:
            logging.info(type(self).__name__ + " avvio server TCP" + self.socket.bind(('0.0.0.0', self.porta)))
            self.socket.listen(1)
            logging.info(type(self).__name__ + " server TCP avviato")
        else:
            logging.info(type(self).__name__ + " connettendo a " + str(self.indirizzo_server) + ":" + str(self.porta))

            self.socket.connect((self.indirizzo_server,self.porta))
            logging.info(type(self).__name__ + " connesso a " + str(self.indirizzo_server) + ":" + str(self.porta))
        ######################## Fine inizializzazione #########################
        logging.info(type(self).__name__ + " inizializzato")
    def avvia(self):
        pacchetto_segnale_entrata = []
        segnale                   = ""
        mittente                  = ""
        destinatario              = ""
        timestamp                 = 0

        errore_connessione        = False

        if self.server == True:
            logging.info(type(self).__name__ + " inizio ascolto porta TCP")
            while True:
                try:
                    self.conn, self.indirizzo_client = self.socket.accept()
                except:
                    errore_connessione = True
                if not errore_connessione:
                    break
                sleep(ATTESA_CICLO_PRINCIPALE)
            logging.info(type(self).__name__ + " ascoltando sulla porta " + str(self.porta) + " all'indirizzo " + str(self.indirizzo_client))

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
                elif segnale == "cassa presente":
                    try:
                        self.invia_dati("cassa presente")
                    except:
                        pass
                elif segnale == "rilascia cassa":
                    try:
                        self.invia_dati("rilascia cassa")
                    except:
                        pass
                elif segnale.find("CODICE") >= 0:
                    try:
                        self.invia_dati(segnale)
                    except:
                        pass
                sleep(ATTESA_CICLO_PRINCIPALE)
        else:
            dati = ""
            with open("codici_casse","a") as codici:
                pass
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

                dati = self.socket.recv(1024).decode('utf-8')
                if dati != "":
                    print(dati)
                    if dati.find("cassa presente") >= 0:
                        try:
                            self.invia_dati("cassa presente")
                        except:
                            pass
                    elif dati.find("rilascia cassa") >= 0:
                        try:
                            self.invia_dati("rilascia cassa")
                        except:
                            pass
                    elif dati.find("stop") >= 0:
                        pass
                    elif segnale.find("CODICE") >= 0:
                        try:
                            self.invia_dati(segnale)
                        except:
                            pass
                sleep(ATTESA_CICLO_PRINCIPALE)
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