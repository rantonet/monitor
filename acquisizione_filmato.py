"""
Autore: Francesco Antonetti Lamorgese Passeri
Copyright: Massimo Manco & Co. SNC 2020
"""

import os
import sys
import fileinput
import logging

from time     import sleep,localtime,strftime
from oggetto  import oggetto
from picamera import PiCamera
from gpiozero import LED,Button

ATTESA_CICLO_PRINCIPALE = 0.01

class acquisizione_filmato(oggetto):
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
            if nome == "modalità":
                self.modalita = valore
            elif nome == "trigger":
                self.trigger = Button(valore)
            elif nome == "trigger_lettore":
                self.trigger_lettore = Button(valore)
        ################# Fine lettura delle impostazioni ######################
        with open("identificativo_shotstation.conf") as f:
            identificativo = f.readline()
            self.identificativo_shotstation = str(identificativo).strip()
        ######################## Fine inizializzazione #########################
        logging.info(type(self).__name__ + " inizializzato " + str(strftime("%H:%M:%S")))
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

        ########################## Impostazioni ################################
        camera                             = PiCamera()
        risoluzione                        = ""
        auto_bilanciamento_bianco_guadagno = 0
        auto_bilanciamento_bianco_modalita = ""
        luminosita                         = 0
        contrasto                          = 0
        compensazione_esposizione          = 0
        modalita_esposizione               = ""
        flash                              = ""
        hflip                              = ""
        vflip                              = ""
        effetto_immagine                   = ""
        iso                                = 0
        rotazione                          = 0
        saturazione                        = 0
        nitidezza                          = 0
        velocita_otturatore                = 0
        ########################## Fine impostazioni ###########################
        ########## Preleva le impostazioni dal file di configuraizone ##########
        with open(self.file_configurazione) as file_configurazione:
            for linea in file_configurazione:
                linea = linea.strip()
                opzione,valore = linea.split(" ")
                if opzione   == "risoluzione":
                    risoluzione = valore
                elif opzione == "auto-bilanciamento-bianco-guadagno":
                    auto_bilanciamento_bianco_guadagno = float(valore)
                elif opzione == "auto-bilanciamento-bianco-modalita":
                    auto_bilanciamento_bianco_modalita = valore
                elif opzione == "luminosita":
                    luminosita = int(valore)
                elif opzione == "contrasto":
                    contrasto = int(valore)
                elif opzione == "compensazione-esposizione":
                    compensazione_esposizione = int(valore)
                elif opzione == "modalita-esposizione":
                    modalita_esposizione = valore
                elif opzione == "flash":
                    flash = valore
                elif opzione == "hflip":
                    if valore.lower() == "true":
                        hflip = True
                    elif valore.lower() == "false":
                        hflip = False
                elif opzione == "vflip":
                    if valore.lower() == "true":
                        vflip = True
                    elif valore.lower() == "false":
                        vflip = False
                elif opzione == "effetto-immagine":
                    effetto_immagine = valore
                elif opzione == "iso":
                    iso = int(valore)
                elif opzione == "rotazione":
                    rotazione = int(valore)
                elif opzione == "saturazione":
                    saturazione = int(valore)
                elif opzione == "nitidezza":
                    nitidezza = int(valore)
                elif opzione == "velocita-otturatore":
                    velocita_otturatore = int(valore)
        ############### Scrivi le impostazioni lette dal file ##################
        camera.awb_gains             = auto_bilanciamento_bianco_guadagno
        camera.awb_mode              = auto_bilanciamento_bianco_modalita
        camera.brightness            = luminosita
        camera.contrast              = contrasto
        camera.exposure_compensation = compensazione_esposizione
        camera.exposure_mode         = modalita_esposizione
        camera.flash_mode            = flash
        camera.hflip                 = hflip
        camera.vflip                 = vflip
        camera.image_effect          = effetto_immagine
        camera.iso                   = iso
        camera.resolution            = risoluzione
        camera.rotation              = rotazione
        camera.saturation            = saturazione
        camera.sharpness             = nitidezza
        camera.shutter_speed         = velocita_otturatore

        # Directory temporanea
        if not os.path.exists("tmp"):
            os.system("mkdir tmp")

        tentata_lettura = False

        codice_cassa = ""

        while True:
            # Ripulisci le variabili d'appoggio all'inizio di ogni iterazione
            # per evitare inconsistenza dei segnali
            pacchetto_segnale[:] = []
            segnale              = ""
            mittente             = ""
            destinatario         = ""
            timestamp            = 0
            percorso_filmato     = strftime("%Y-%m-%d",localtime())

            ########################## Lettura Segnale #########################
            # Se la coda dei segnali in entrata non è vuota, quindi c'è almeno
            # un segnale, leggi il primo segnale della coda
            with self.lock_segnali_entrata:
                if not self.coda_segnali_entrata.empty():
                    pacchetto_segnale[:] = self.coda_segnali_entrata.get_nowait()
            ####################### Fine Lettura Segnale #######################
            ################# Controllo consistenza del segnale ################
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
            # Aggiunta riga log per verifica condizione di presenza cassa
            #if (self.trigger_lettore.is_pressed and (not self.trigger.is_pressed)) and (not tentata_lettura):
            if (self.trigger_lettore.is_pressed) and (not tentata_lettura) and (not self.inRegistrazione):
                if self.modalita == "master":
                    with self.lock_segnali_uscita:
                        if not self.coda_segnali_uscita.full():
                            self.coda_segnali_uscita.put_nowait(["cassa presente","lettore_codice_a_barre"])
                            ## logging.info(str(type(self).__name__) + " attiva lettore codice " + str(strftime("%H:%M:%S")))
                    sleep(ATTESA_CICLO_PRINCIPALE)
                codice_cassa            = ""
                attesa_codice           = False
                codice_inviato          = False
                tentativi_attesa_codice = 40

                while True:
                    pacchetto_segnale[:]    = []
                    segnale                 = ""
                    mittente                = ""
                    destinatario            = ""
                    timestamp               = 0

                    with self.lock_segnali_entrata:
                        if not self.coda_segnali_entrata.empty():
                            pacchetto_segnale[:] = \
                                                  self.coda_segnali_entrata.get_nowait()
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
                            self.coda_segnali_uscita.put_nowait(["segnale mal formato",""])
                        pacchetto_segnale[:] = []
                        sleep(ATTESA_CICLO_PRINCIPALE)
                        continue
                    if self.modalita == "master":
                        if segnale == "pronto lettura codice":
                            with self.lock_segnali_uscita:
                                self.coda_segnali_uscita.put_nowait(["leggi codice","lettore_codice_a_barre"])
                            attesa_codice = True
                        else:
                            #if (((self.trigger_lettore.is_pressed and not self.trigger.is_pressed) and (self.modalita=="master")) and self.inRegistrazione):
                            #if (((self.trigger_lettore.is_pressed) and (self.modalita == "master")) and self.inRegistrazione):
                            #    logging.info(type(self).__name__ + " trigger rilasciato prima del lettore")
                            #    with self.lock_segnali_uscita:
                            #        if not self.coda_segnali_uscita.full():
                            #            self.coda_segnali_uscita.put_nowait(["invia","comunicazione_seriale"])
                            #    sleep(ATTESA_CICLO_PRINCIPALE)
                            #    with self.lock_segnali_uscita:
                            #        if not self.coda_segnali_uscita.full():
                            #            self.coda_segnali_uscita.put_nowait(["ferma acquisizione","comunicazione_seriale"])
                            #    tentata_lettura = False
                            #    camera.stop_recording()
                            #    camera.stop_preview()
                            #    self.inRegistrazione = False
                            #    codice_cassa = ""
                            #    os.system("mv tmp/* " + percorso_filmato)
                            #    break

                            # Se il codice cassa ha un valore forzo attesa_codice a True
                            codice_cassa = str(segnale)
                            if codice_cassa !="":
                                attesa_codice= True
                            if attesa_codice and (mittente == "lettore_codice_a_barre"):
                                if segnale.find(" ") >= 0:
                                    sleep(ATTESA_CICLO_PRINCIPALE)
                                    continue
                                codice_cassa = str(segnale)
                                with self.lock_segnali_uscita:
                                    if not self.coda_segnali_uscita.full():
                                        self.coda_segnali_uscita.put_nowait(["codice ricevuto","lettore_codice_a_barre"])
                                sleep(0.001)
                                with self.lock_segnali_uscita:
                                    if not self.coda_segnali_uscita.full():
                                        self.coda_segnali_uscita.put_nowait(["invia","comunicazione_seriale"])
                                timer = 100

                                while True:
                                    pacchetto_segnale[:]    = []
                                    segnale                 = ""
                                    mittente                = ""
                                    destinatario            = ""
                                    timestamp               = 0

                                    with self.lock_segnali_entrata:
                                        if not self.coda_segnali_entrata.empty():
                                            pacchetto_segnale[:] = self.coda_segnali_entrata.get_nowait()
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
                                            self.coda_segnali_uscita.put_nowait(["segnale mal formato",""])
                                        pacchetto_segnale[:] = []
                                        timer -= 1
                                        if timer <= 0:
                                            sleep(ATTESA_CICLO_PRINCIPALE)
                                            break
                                        sleep(ATTESA_CICLO_PRINCIPALE)
                                        continue
                                    if segnale == "aspettando codice":
                                        with self.lock_segnali_uscita:
                                            if not self.coda_segnali_uscita.full():
                                                self.coda_segnali_uscita.put_nowait(["CODICE_" + str(codice_cassa),"comunicazione_seriale"])
                                        codice_inviato  = True
                                        tentata_lettura = False
                                        sleep(ATTESA_CICLO_PRINCIPALE)
                                        break
                                    elif timer <= 0:
                                        codice_inviato  = True
                                        tentata_lettura = True
                                        sleep(ATTESA_CICLO_PRINCIPALE)
                                        break
                                    else:
                                        timer -= 1
                                    sleep(ATTESA_CICLO_PRINCIPALE)
                                attesa_codice = False
                                sleep(ATTESA_CICLO_PRINCIPALE)
                                break
                            #elif ((tentativi_attesa_codice <= 0) or (self.trigger.is_pressed)):
                            elif (tentativi_attesa_codice <= 0):
                                codice_cassa = ""
                                tentata_lettura = True
                                with self.lock_segnali_uscita:
                                    if not self.coda_segnali_uscita.full():
                                        self.coda_segnali_uscita.put_nowait(["annulla lettura", "lettore_codice_a_barre"])
                                attesa_codice  = False
                                codice_cassa   = ""
                                codice_inviato = ""
                                sleep(ATTESA_CICLO_PRINCIPALE)
                                break
                            elif not attesa_codice:
                                tentativi_attesa_codice -= 1
                                codice_cassa             = ""
                                codice_inviato           = False
                                sleep(ATTESA_CICLO_PRINCIPALE)
                                continue
                            else:
                                tentativi_attesa_codice -= 1
                                codice_cassa             = ""
                                codice_inviato           = False
                                sleep(ATTESA_CICLO_PRINCIPALE)
                                continue
                        #if (tentativi_attesa_codice <= 0) or codice_inviato or (codice_cassa != "") or self.trigger.is_pressed:
                        if (tentativi_attesa_codice <= 0) or codice_inviato or (codice_cassa != ""):
                            sleep(ATTESA_CICLO_PRINCIPALE)
                            break
                    else:
                        if mittente == "comunicazione_seriale":
                            if segnale.find(" ") >= 0:
                                segnale = ""
                                sleep(ATTESA_CICLO_PRINCIPALE)
                                continue
                            else:
                                codice_cassa = segnale
                                sleep(ATTESA_CICLO_PRINCIPALE)
                                break
                        elif tentativi_attesa_codice <= 0:
                            codice_cassa = ""
                            sleep(ATTESA_CICLO_PRINCIPALE)
                            break
                        else:
                            tentativi_attesa_codice -= 1
                            sleep(ATTESA_CICLO_PRINCIPALE)
                    if codice_cassa != "":
                        sleep(ATTESA_CICLO_PRINCIPALE)
                        break
                    sleep(ATTESA_CICLO_PRINCIPALE)
                tentata_lettura = True
            ############### Fine controllo consistenza del segnale #############
            #if (((segnale == "avvia acquisizione") and (self.modalita=="slave")) and (not self.inRegistrazione)) or \
            #   (((self.trigger_lettore.is_pressed and self.trigger.is_pressed) and (self.modalita=="master")) and (not self.inRegistrazione)):
            if (((segnale == "avvia acquisizione") and (self.modalita=="slave")) and (not self.inRegistrazione)) or \
               (((self.trigger_lettore.is_pressed) and (self.modalita=="master")) and (not self.inRegistrazione)):
                # La cassa è stata riconosciuta dall'operazione di
                # riconoscimento cassa (ha letto e memorizzato il codice a
                # barre)
                ##### Ex Lettura codice
                sleep(ATTESA_CICLO_PRINCIPALE)

                if self.modalita == "master":
                    with self.lock_segnali_uscita:
                        if not self.coda_segnali_uscita.full():
                            self.coda_segnali_uscita.put_nowait(["invia","comunicazione_seriale"])
                    sleep(ATTESA_CICLO_PRINCIPALE)
                    with self.lock_segnali_uscita:
                        if not self.coda_segnali_uscita.full():
                            self.coda_segnali_uscita.put_nowait(["avvia acquisizione","comunicazione_seriale"])
                    tentata_lettura = False
                else:
                    with self.lock_segnali_uscita:
                        if not self.coda_segnali_uscita.full():
                            self.coda_segnali_uscita.put_nowait(["invia","comunicazione_seriale"])
                    sleep(ATTESA_CICLO_PRINCIPALE)
                    with self.lock_segnali_uscita:
                        if not self.coda_segnali_uscita.full():
                            self.coda_segnali_uscita.put_nowait(["ok","comunicazione_seriale"])
                sleep(ATTESA_CICLO_PRINCIPALE)
                if not os.path.exists(percorso_filmato):
                    os.system("mkdir " + percorso_filmato)
                if codice_cassa != "":
                    nome_filmato = "tmp/" + self.identificativo_shotstation + "_" + codice_cassa + "_" + strftime("%H-%M-%S",localtime()) + ".h264"
                    if self.modalita == "slave":
                        codice_cassa = ""
                else:
                    nome_filmato = "tmp/" + self.identificativo_shotstation + "_anonymous_" + strftime("%H-%M-%S",localtime()) + ".h264"
                try:
                    camera.start_preview()
                    sleep(ATTESA_CICLO_PRINCIPALE)
                    camera.start_recording(nome_filmato)
                except:
                    e = sys.exc_info()[0]
                    print(e)
                    logging.info(type(self).__name__ + str(e))
                    camera.stop_recording()
                    camera.stop_preview()
                    self.inRegistrazione = False
                    os.system("mv tmp/* " + percorso_filmato)
                    sleep(ATTESA_CICLO_PRINCIPALE)
                    camera.start_preview()
                    sleep(ATTESA_CICLO_PRINCIPALE)
                    camera.start_recording(nome_filmato)
                finally:
                    sleep(ATTESA_CICLO_PRINCIPALE)
                    logging.info(type(self).__name__ + " acquisizione avviata " + str(strftime("%H:%M:%S")))
                    self.inRegistrazione = True
                    codice_cassa = ""
            elif (((segnale == "avvia acquisizione") and (self.modalita == "slave")) and (self.inRegistrazione)):
                logging.info(type(self).__name__ + " riavvio acquisizione " + str(strftime("%H:%M:%S")))
                with self.lock_segnali_uscita:
                    if not self.coda_segnali_uscita.full():
                        self.coda_segnali_uscita.put_nowait(["invia","comunicazione_seriale"])
                sleep(ATTESA_CICLO_PRINCIPALE)
                with self.lock_segnali_uscita:
                    if not self.coda_segnali_uscita.full():
                        self.coda_segnali_uscita.put_nowait(["ok","comunicazione_seriale"])
                camera.stop_recording()
                camera.stop_preview()
                sleep(ATTESA_CICLO_PRINCIPALE)
                self.inRegistrazione = False
                os.system("mv tmp/* " + percorso_filmato)
                camera.start_preview()
                sleep(ATTESA_CICLO_PRINCIPALE)
                camera.start_recording(nome_filmato)
                sleep(ATTESA_CICLO_PRINCIPALE)
                logging.info(type(self).__name__ + " acquisizione riavviata " + str(strftime("%H:%M:%S")))
                self.inRegistrazione = True
                codice_cassa = ""

            #elif (((segnale == "ferma acquisizione") and (self.modalita == "slave")) and self.inRegistrazione) or \
            #     ((((not self.trigger_lettore.is_pressed) or (not self.trigger.is_pressed)) and (self.modalita=="master")) and self.inRegistrazione):
            elif (((segnale == "ferma acquisizione") and (self.modalita == "slave")) and self.inRegistrazione) or \
                 ((((not self.trigger_lettore.is_pressed)) and (self.modalita=="master")) and self.inRegistrazione):
                # La cassa è uscita (not self.trigger_lettore.is_pressed) e la camera è in registrazione (self.inRegistrazione)
                logging.info(str(type(self).__name__) + " stop acquisizione " + str(strftime("%H:%M:%S")))
                if self.modalita == "master":
                    with self.lock_segnali_uscita:
                        if not self.coda_segnali_uscita.full():
                            self.coda_segnali_uscita.put_nowait(["invia","comunicazione_seriale"])
                    sleep(ATTESA_CICLO_PRINCIPALE)
                    with self.lock_segnali_uscita:
                        if not self.coda_segnali_uscita.full():
                            self.coda_segnali_uscita.put_nowait(["ferma acquisizione","comunicazione_seriale"])
                    tentata_lettura = False
                else:
                    with self.lock_segnali_uscita:
                        if not self.coda_segnali_uscita.full():
                            self.coda_segnali_uscita.put_nowait(["invia","comunicazione_seriale"])
                    sleep(ATTESA_CICLO_PRINCIPALE)
                    with self.lock_segnali_uscita:
                        if not self.coda_segnali_uscita.full():
                            self.coda_segnali_uscita.put_nowait(["ok","comunicazione_seriale"])
                camera.stop_recording()
                camera.stop_preview()
                logging.info(str(type(self).__name__) + " Acquisizione stoppata " + str(strftime("%H:%M:%S")))
                self.inRegistrazione = False
                codice_cassa = ""
                os.system("mv tmp/* " + percorso_filmato)
            #elif (((self.trigger_lettore.is_pressed and not self.trigger.is_pressed) and (self.modalita=="master")) and self.inRegistrazione):
            #elif (((self.trigger_lettore.is_pressed) and (self.modalita=="master")) and self.inRegistrazione):
            #    logging.info(type(self).__name__ + " trigger rilasciato prima del lettore")
            #    with self.lock_segnali_uscita:
            #        if not self.coda_segnali_uscita.full():
            #            self.coda_segnali_uscita.put_nowait(["invia","comunicazione_seriale"])
            #    sleep(ATTESA_CICLO_PRINCIPALE)
            #    with self.lock_segnali_uscita:
            #        if not self.coda_segnali_uscita.full():
            #            self.coda_segnali_uscita.put_nowait(["ferma acquisizione","comunicazione_seriale"])
            #    tentata_lettura = False
            #    camera.stop_recording()
            #    camera.stop_preview()
            #    self.inRegistrazione = False
            #    codice_cassa = ""
            #    os.system("mv tmp/* " + percorso_filmato)
            elif segnale == "aggiorna":
                # È arrivata la richiesta di aggiornamendo delle impostazioni
                # per questa operazione
                self.impostazioni_in_aggiornamento = 1
                ## logging.info(str(type(self).__name__) + " in aggiornamento " + str(strftime("%H:%M:%S")))
                camera.start_preview()
                while True:
                    ########## Variabili d'appoggio per il segnale in ##########
                    ################## entrata/uscita ##########################
                    pacchetto_segnale[:] = []
                    segnale           = ""
                    mittente          = ""
                    destinatario      = ""
                    timestamp         = 0
                    ######## Fine variabili d'appoggio per il segnale in #######
                    ###################### entrata/uscita ######################
                    with self.lock_segnali_uscita:
                        self.coda_segnali_uscita.put_nowait(["pronto","lettore_codice_a_barre"])
                    ## logging.info(str(type(self).__name__) + "pronto per l'aggiornamento " + str(strftime("%H:%M:%S")))
                    while True:
                        #################### Lettura Segnale ###################
                        # Se la coda dei segnali in entrata non è vuota, quindi
                        # c'è almeno un segnale, leggi il primo segnale della
                        # coda
                        with self.lock_segnali_entrata:
                            if not self.coda_segnali_entrata.empty():
                                pacchetto_segnale[:] = \
                                          self.coda_segnali_entrata.get_nowait()
                        ################# Fine Lettura Segnale #################
                        ########### Controllo consistenza del segnale ##########
                        if len(pacchetto_segnale) == 4:
                            # La lista con quatto elementi significa che è un
                            # messaggio diretto
                            segnale,mittente,destinatario,timestamp = \
                                                               pacchetto_segnale
                            pacchetto_segnale[:] = []
                            sleep(ATTESA_CICLO_PRINCIPALE)
                            break
                        elif len(pacchetto_segnale) == 3:
                            # La lista con tre elementi significa che è un
                            # messaggio in broadcast
                            segnale,mittente,timestamp = pacchetto_segnale
                            pacchetto_segnale[:] = []
                            sleep(ATTESA_CICLO_PRINCIPALE)
                            break
                        elif len(pacchetto_segnale) == 0:
                            sleep(ATTESA_CICLO_PRINCIPALE)
                            continue
                        else:
                            with self.lock_segnali_uscita:
                                self.coda_segnali_uscita.put_nowait( \
                                                     ["segnale mal formato",""])
                            pacchetto_segnale[:] = []
                            sleep(ATTESA_CICLO_PRINCIPALE)
                            continue
                        
                        ######### Fine controllo consistenza del segnale #######
                    # Il segnale per l'aggiornamento è nella forma:
                    # nome_impostazione valore
                    logging.info(str(type(self).__name__) + " ricevuto: " + str(segnale) + " " + str(strftime("%H:%M:%S")))
                    if segnale == "fine aggiornamento":
                        logging.info(str(type(self).__name__) + ": Finalizzando l'aggiornamento " + str(strftime("%H:%M:%S")))
                        self.impostazioni_in_aggiornamento = 0
                        with self.lock_segnali_uscita:
                                self.coda_segnali_uscita.put_nowait( \
                                                          ["fine aggiornamento",
                                                      "lettore_codice_a_barre"])
                        while True:
                            ################## Lettura Segnale #################
                            # Se la coda dei segnali in entrata non è vuota,
                            # quindi c'è almeno un segnale, leggi il primo
                            # segnale della coda
                            with self.lock_segnali_entrata:
                                if not self.coda_segnali_entrata.empty():
                                    pacchetto_segnale[:] = \
                                          self.coda_segnali_entrata.get_nowait()
                            ############### Fine Lettura Segnale ###############
                            ######### Controllo consistenza del segnale ########
                            if len(pacchetto_segnale) == 4:
                                # La lista con quatto elementi significa che è un
                                # messaggio diretto
                                segnale,mittente,destinatario,timestamp = \
                                                               pacchetto_segnale
                                pacchetto_segnale[:] = []
                                sleep(ATTESA_CICLO_PRINCIPALE)
                                break
                            elif len(pacchetto_segnale) == 3:
                                # La lista con tre elementi significa che è un
                                # messaggio in broadcast
                                segnale,mittente,timestamp = pacchetto_segnale
                                pacchetto_segnale[:] = []
                                sleep(ATTESA_CICLO_PRINCIPALE)
                                break
                            elif len(pacchetto_segnale) == 0:
                                sleep(ATTESA_CICLO_PRINCIPALE)
                                continue
                            else:
                                with self.lock_segnali_uscita:
                                    self.coda_segnali_uscita.put_nowait( \
                                                     ["segnale mal formato",""])
                                pacchetto_segnale[:] = []
                                sleep(ATTESA_CICLO_PRINCIPALE)
                                continue
                            if segnale == "ok":
                                logging.info(type(self).__name__ + " ok ricevuto: fine aggiornamento " + str(strftime("%H:%M:%S")))
                                sleep(ATTESA_CICLO_PRINCIPALE)
                                break
                            sleep(ATTESA_CICLO_PRINCIPALE)
                        if self.impostazioni_in_aggiornamento == 0:
                            logging.info(type(self).__name__ + " aggiornamento terminato " + str(strftime("%H:%M:%S")))
                            sleep(ATTESA_CICLO_PRINCIPALE)
                            break
                    else:
                        segnale_spacchettato = segnale.split(" ")
                        nome,val = segnale_spacchettato
                        if val.find("_") == 0:
                            valore = val.replace("_","-")
                        else:
                            valore = val
                    if self.impostazioni_in_aggiornamento == 0:
                        logging.info(type(self).__name__ + " aggiornamento terminato " + str(strftime("%H:%M:%S")))
                        sleep(ATTESA_CICLO_PRINCIPALE)
                        break
                    if nome == "rotazione":
                        camera.rotation = valore
                        with fileinput.FileInput(self.file_configurazione,
                                                 inplace=True, backup='.bak') \
                                                 as configurazione:
                            for impostazione in configurazione:
                                if "rotazione" in impostazione:
                                    print("rotazione " + valore)
                                else:
                                    print(impostazione,end="")
                        logging.debug(camera.rotation)
                    elif nome == "risoluzione":
                        camera.resolution = valore
                        with fileinput.FileInput(self.file_configurazione,
                                                 inplace=True, backup='.bak') \
                                                 as configurazione:
                            for impostazione in configurazione:
                                if "risoluzione" in impostazione:
                                    print("risoluzione " + valore)
                                else:
                                    print(impostazione,end="")
                        logging.debug(camera.resolution)
                    elif nome == "auto_bilanciamento_bianco_modalita":
                        camera.awb_mode = valore
                        with fileinput.FileInput(self.file_configurazione,
                                                 inplace=True, backup='.bak') \
                                                 as configurazione:
                            for impostazione in configurazione:
                                if "auto_bilanciamento_bianco_modalita" in \
                                                                   impostazione:
                                    print("auto_bilanciamento_bianco_modalita "
                                                                       + valore)
                                else:
                                    print(impostazione,end="")
                        logging.debug(camera.awb_mode)
                    elif nome == "luminosita":
                        camera.brightness = int(valore)
                        with fileinput.FileInput(self.file_configurazione,
                                                 inplace=True, backup='.bak') \
                                                 as configurazione:
                            for impostazione in configurazione:
                                if "luminosita" in impostazione:
                                    print("luminosita " + valore)
                                else:
                                    print(impostazione,end="")
                        logging.debug(camera.brightness)
                    elif nome == "contrasto":
                        camera.contrast = int(valore)
                        with fileinput.FileInput(self.file_configurazione,
                                                 inplace=True, backup='.bak') \
                                                 as configurazione:
                            for impostazione in configurazione:
                                if "contrasto" in impostazione:
                                    print("contrasto " + valore)
                                else:
                                    print(impostazione,end="")
                        logging.debug(camera.contrast)
                    elif nome == "compensazione_esposizione":
                        camera.exposure_compensation = int(valore)
                        with fileinput.FileInput(self.file_configurazione,
                                                 inplace=True, backup='.bak') \
                                                 as configurazione:
                            for impostazione in configurazione:
                                if "compensazione_esposizione" in impostazione:
                                    print("compensazione-esposizione " + valore)
                                else:
                                    print(impostazione,end="")
                        logging.debug(camera.exposure_compensation)
                    elif nome == "modalita_esposizione":
                        camera.exposure_mode = valore
                        with fileinput.FileInput(self.file_configurazione,
                                                 inplace=True, backup='.bak') \
                                                 as configurazione:
                            for impostazione in configurazione:
                                if "modalita_esposizione" in impostazione:
                                    print("modalita-esposizione " + valore)
                                else:
                                    print(impostazione,end="")
                        logging.debug(camera.exposure_mode)
                    elif nome == "flash":
                        camera.flash_mode = valore
                        with fileinput.FileInput(self.file_configurazione,
                                                 inplace=True, backup='.bak') \
                                                 as configurazione:
                            for impostazione in configurazione:
                                if "flash" in impostazione:
                                    print("flash " + valore)
                                else:
                                    print(impostazione,end="")
                        logging.debug(camera.flash_mode)
                    elif nome == "hflip":
                        if valore.lower() == "true":
                            camera.hflip = True
                        elif valore.lower() == "false":
                            camera.hflip = False
                        with fileinput.FileInput(self.file_configurazione,
                                                 inplace=True, backup='.bak') \
                                                 as configurazione:
                            for impostazione in configurazione:
                                if "hflip" in impostazione:
                                    print("hflip " + valore)
                                else:
                                    print(impostazione,end="")
                        logging.debug(camera.hflip)
                    elif nome == "vflip":
                        if valore.lower() == "true":
                            camera.vflip = True
                        elif valore.lower() == "false":
                            camera.vflip = False
                        with fileinput.FileInput(self.file_configurazione,
                                                 inplace=True, backup='.bak') \
                                                 as configurazione:
                            for impostazione in configurazione:
                                if "vflip" in impostazione:
                                    print("vflip " + valore)
                                else:
                                    print(impostazione,end="")
                        logging.debug(camera.vflip)
                    elif nome == "effetto_immagine":
                        camera.image_effect = valore
                        with fileinput.FileInput(self.file_configurazione,
                                                 inplace=True, backup='.bak') \
                                                 as configurazione:
                            for impostazione in configurazione:
                                if "effetto_immagine" in impostazione:
                                    print("effetto_immagine " + valore)
                                else:
                                    print(impostazione,end="")
                        logging.debug(camera.image_effect)
                    elif nome == "iso":
                        camera.iso = int(valore)
                        with fileinput.FileInput(self.file_configurazione,
                                                 inplace=True, backup='.bak') \
                                                 as configurazione:
                            for impostazione in configurazione:
                                if "iso" in impostazione:
                                    print("iso " + valore)
                                else:
                                    print(impostazione,end="")
                        logging.debug(camera.iso)
                    elif nome == "saturazione":
                        camera.saturation = int(valore)
                        with fileinput.FileInput(self.file_configurazione,
                                                 inplace=True, backup='.bak') \
                                                 as configurazione:
                            for impostazione in configurazione:
                                if "saturazione" in impostazione:
                                    print("saturazione " + valore)
                                else:
                                    print(impostazione,end="")
                        logging.debug(camera.saturation)
                    elif nome == "nitidezza":
                        camera.sharpness = int(valore)
                        with fileinput.FileInput(self.file_configurazione,
                                                 inplace=True, backup='.bak') \
                                                 as configurazione:
                            for impostazione in configurazione:
                                if "nitidezza" in impostazione:
                                    print("nitidezza " + valore)
                                else:
                                    print(impostazione,end="")
                        logging.debug(camera.sharpness)
                    elif nome == "velocita_otturatore":
                        camera.shutter_speed = valore
                        with fileinput.FileInput(self.file_configurazione,
                                                 inplace=True, backup='.bak') \
                                                 as configurazione:
                            for impostazione in configurazione:
                                if "velocita_otturatore" in impostazione:
                                    print("velocita_otturatore " + valore)
                                else:
                                    print(impostazione,end="")
                        logging.debug(camera.shutter_speed)
                    else:
                        with self.lock_segnali_uscita:
                            self.coda_segnali_uscita.put_nowait( \
                                                     ["impostazione non valida",
                                                      "lettore_codice_a_barre"])
                    with self.lock_segnali_uscita:
                        self.coda_segnali_uscita.put_nowait(["pronto",
                                                  "lettore_codice_a_barre"])
                    sleep(ATTESA_CICLO_PRINCIPALE)
                camera.stop_preview()
            elif segnale == "stop":
                with self.lock_segnali_uscita:
                    self.coda_segnali_uscita.put_nowait(["stop",
                                                         "gestore_segnali"])
                return int(-1)
            elif segnale.find("CODICE_") >= 0:
                ## logging.info(str(type(self).__name__) + " codice ricevuto " + str(strftime("%H:%M:%S")))
                if self.modalita == "slave":
                    codice_cassa = segnale.replace("CODICE_","")
                    ## logging.info(type(self).__name__ + " Codice cassa " + codice_cassa + " " + str(strftime("%H:%M:%S")))
            sleep(ATTESA_CICLO_PRINCIPALE)
    def aggiornamento(self):
        pass
