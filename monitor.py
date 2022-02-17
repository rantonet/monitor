# This Python file uses the following encoding: utf-8

import os
import sys
import fileinput
import logging

from time     import sleep,localtime,strftime
from oggetto  import oggetto

ATTESA_CICLO_PRINCIPALE = 0.01

class monitor(oggetto):
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
        ##################### Lettura delle impostazioni #######################
        self.file_configurazione = file_configurazione
        configurazione       = []
        lista_configurazione = []
        impostazioni         = []
        self.lista_segnali   = []
        self.modalita        = ""
        self.inRegistrazione = False
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
            #print(impostazione)
        ################# Fine lettura delle impostazioni ######################
        logging.info(type(self).__name__ + " Fine lettura impostazioni " + str(strftime("%H:%M:%S")))

    def avvia(self):
        logging.info(type(self).__name__ + " avviato " + str(strftime("%H:%M:%S")))

        ######### Variabili d'appoggio per il segnale in entrata/uscita ########
        pacchetto_segnale = []
        segnale           = ""
        mittente          = ""
        destinatario      = ""
        timestamp         = 0
        ###### Fine variabili d'appoggio per il segnale in entrata/uscita ######

        # Segnala a chiunque sia in ascolto che sei entrato nello stato avviato
        with self.lock_segnali_uscita:
            if not self.coda_segnali_uscita.full():
                self.coda_segnali_uscita.put_nowait(["avviato",""])

        tentata_lettura = False

        while True:
            #print("In attesa di un segnale in entrata")
            # Ripulisci le variabili d'appoggio all'inizio di ogni iterazione
            # per evitare inconsistenza dei segnali
            pacchetto_segnale[:] = []
            segnale              = ""
            mittente             = ""
            destinatario         = ""
            timestamp            = 0

            ########################## Lettura Segnale #########################
            # Se la coda dei segnali in entrata non è vuota, quindi c'è almeno
            # un segnale, leggi il primo segnale della coda
            with self.lock_segnali_entrata:
                if not self.coda_segnali_entrata.empty():
                    pacchetto_segnale[:] = self.coda_segnali_entrata.get_nowait()
            ####################### Fine Lettura Segnale #######################

            ########### Inizio Controllo consistenza del segnale ################
            if len(pacchetto_segnale) == 4:
                # La lista con quatto elementi significa che è un messaggio
                # diretto
                segnale,mittente,destinatario,timestamp = pacchetto_segnale
                pacchetto_segnale[:] = []
            elif len(pacchetto_segnale) == 3:
                # La lista con tre elementi significa che è un messaggio in
                # broadcast
                segnale,mittente,timestamp = pacchetto_segnale
                pacchetto_segnale[:] = []
            elif len(pacchetto_segnale) == 0:
                # sleep(ATTESA_CICLO_PRINCIPALE)
                # continue
                pass
            else:
                with self.lock_segnali_uscita:
                    self.coda_segnali_uscita.put_nowait(["segnale mal formato",
                                                         ""])
                pacchetto_segnale[:] = []
                sleep(ATTESA_CICLO_PRINCIPALE)
                continue
            ############ Fine Controllo consistenza del segnale ###############

            ################ Inizio programma vero e proprio ##################

            ################ Comunica al modulo comunicazioni_tcp #############
            ##################### di inviare un messaggio #####################
            with self.lock_segnali_uscita:
                    self.coda_segnali_uscita.put_nowait(["CIAO DA MODULO MONITOR",
                                                        "comunicazione_tcp"])
            pacchetto_segnale[:] = []

            sleep(ATTESA_CICLO_PRINCIPALE)