# -*- coding: utf-8 -*-
"""
Created on Fri Aug 27 15:40:49 2021

@author: GelbJ
"""

import threading
from path import Path # NOTE: installer la lib path.py
from datetime import date, datetime, timedelta
import time


def Recording(start_time, end_time, folder) : 
    out_file = folder.joinpath(start_time.strftime(format = "%Y-%m-%dT%H-%M-%S")+"__"+end_time.strftime(format = "%Y-%m-%dT%H-%M-%S")+"_somerecords.txt")
    out = open(out_file, "w")
    current = datetime.now()
    while current < end_time : 
        out.write(current.strftime(format = "%Y/%m/%dT%H-%M-%S")+"\n")
        time.sleep(1)
        current = datetime.now()
    out.close()


class RecordManager(object): 
    
    def __init__(self, chunk_duration, tol, out_folder, stop_time) : 
        
        # chunk_duration doit etre specifiee en secondes
        # elle indique la duree d'un enregistrement
        self.chunk_duration = chunk_duration
        # tol doit etre specifiee en seconde, elle indique combien de temps
        # avant la fin d'un record le prochain doit etre lance
        self.tol = tol
        # out_folder doit etre un chemin vers le dossier dans lequel
        # les fichiers sont enregistres
        self.out_folder = Path(out_folder)
        # stop_time doit etre une datetime indiquant quand les enregistrements 
        # doivent sesser
        self.stop_time = stop_time
        # TODO : proposer une facon de stopper l'enregistrement quand on 
        # enleve le micro
        
        # creer un dossier avec des logs
        logfolder = self.out_folder.joinpath("logs")
        if logfolder.isdir() == False : 
            logfolder.makedirs()
        
        
        
    def Start(self) : 
        
        ## ouverture d'un fichier de log pour garder une trace des evenements
        start_session = datetime.now()
        log_name = start_session.strftime(format = "%Y/%m/%dT%H-%M-%S")+"_recordsession.txt"
        log_file = self.out_folder.joinpath("logs/"+log_name)
        #log = open(log_file,"w")
        
        ## definition d'une première session d'enregistrement
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds = self.chunk_duration)
        print("launching the first Thread...")
        process1 = threading.Thread(target = Recording, args = [start_time, end_time, self.out_folder])
        process1.start()
        running = "p1"
        
        next_start = end_time
        print("the next thread is scheduled for "+next_start.strftime(format = "%Y/%m/%dT%H-%M-%S"))
        
        actual_time = datetime.now()
        while actual_time < self.stop_time : 
            # on attend un peu
            time.sleep(1)
            actual_time = datetime.now()
            print("it is : " + actual_time.strftime(format = "%Y/%m/%dT%H-%M-%S"))
            
            # si on de passe le moment du prochain declancheur
            if actual_time >= next_start - timedelta(seconds = self.tol):
                # on definit le nouveau temps de depart
                start_time = next_start
                # et le nouveau temps de fin
                end_time = start_time + timedelta(seconds = self.chunk_duration)
                # on choisit le bon process a lancer (1 sur 2 pour rappel)
                if running == "p1" : 
                    print("launching the Thread number 2...")
                    process2 = threading.Thread(target = Recording, args = [start_time, end_time, self.out_folder])
                    process2.start()
                    running = "p2"
                else : 
                    print("launching the Thread number 1...")
                    process1 = threading.Thread(target = Recording, args = [start_time, end_time, self.out_folder])
                    process1.start()
                    running = "p1"
                next_start = end_time
                print("the next thread is scheduled for "+next_start.strftime(format = "%Y/%m/%dT%H-%M-%S"))
                    
            
            
            
        
### TESTING
                
if __name__ == "__main__" : 
    
    current = datetime.now()
    stopTime = current + timedelta(minutes = 4)
    Recorder = RecordManager(30, 5, Path("C:/Users/GelbJ/Desktop/Projets/PyAudioRecorder/test_folder"),stopTime)
    Recorder.Start()
        
        
        
        
    