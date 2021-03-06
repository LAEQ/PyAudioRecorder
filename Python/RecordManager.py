# -*- coding: utf-8 -*-
"""
Created on Fri Aug 27 15:40:49 2021

@author: GelbJ
"""

import threading
from path import Path # NOTE: installer la lib path.py
from datetime import date, datetime, timedelta
import time
import pause
import wave
import alsaaudio
import pyaudio
import json
from mylibs.Jhtml import Balise


"""
NOTES :

Le format 16 bits permet d'enregistrer les donnees son sur un range de 65535 valeurs (negatif a positif),
l'enjeu lors de l'analyse est de le convertir dans un array normalise allant de -1 a 1.
Pour cela on divise simplement la valeur brute par 32768.0

La structuration du dossier avec les donnees est la suivante :
- raw (les fichiers brutes)
- merged (les fichiers concatenes)
- log (pour les eventuels logs)
- 

"""


###################################################################################
##### Some global parameters ####
###################################################################################

TIME_FORMAT = "%Y-%m-%dT%H-%M-%S"


###################################################################################
##### Some helper functions ####
###################################################################################

def nice_duration(duration) :
    secs = int(duration.total_seconds())
    rem_secs = secs%60
    nb_min = (secs - rem_secs)/60
    rem_mins = nb_min%60
    nb_hours = (nb_min - rem_mins)/60
    h = str(int(nb_hours))
    if(len(h)) == 1 :
        h = "0"+h
    m = str(int(rem_mins))
    if(len(m)) == 1 :
        m = "0"+m
    s = str(int(rem_secs))
    if(len(s)) == 1 :
        s = "0"+s
    return(":".join([h,m,s]))


###################################################################################
##### THE WORKER FUNCTION RECORDING THE SOUND ####
###################################################################################

def mic_recorder(parameters, start_time, end_time, out_folder) :
    
    start_t = start_time.strftime(format = TIME_FORMAT)
    end_t = end_time.strftime(format = TIME_FORMAT)
    out_file = out_folder.joinpath(start_t+"__"+end_t+"_audio.wav")

    pause.until(start_time)
    
    # recuperation des parametres
    CHANNELS = parameters["channel"]
    INFORMAT = parameters["format"]
    RATE = parameters["rate"]
    FRAMESIZE = parameters["frame_size"]
    record_secs= parameters["duration"]

    # set up audio input
    recorder=alsaaudio.PCM(type=alsaaudio.PCM_CAPTURE)
    recorder.setchannels(CHANNELS)
    recorder.setrate(RATE)
    recorder.setformat(INFORMAT)
    recorder.setperiodsize(FRAMESIZE)


    frames = []
    for ii in range(0,int((RATE/FRAMESIZE)*record_secs)):
        frames.append(recorder.read()[1])


    # save the audio frames as .wav file
    wavefile = wave.open(out_file,'wb')
    wavefile.setnchannels(CHANNELS)
    # pour la selection du sample width, on va tricher et utiliser la valeur recommandee par pyaudio
    rec_width = pyaudio.get_sample_size(pyaudio.paInt16)
    wavefile.setsampwidth(rec_width)
    wavefile.setframerate(RATE)
    wavefile.writeframes(b''.join(frames))
    wavefile.close()
    
    # Ce serait aussi cool d'avoir un petit fichier de metadata pour se souvernir des parametres
    meta_data = {
        "SAMPLING_RATE" : RATE,
        "FRAMESIZE" : FRAMESIZE,
        "CHANNELS" : CHANNELS,
        "SAMPLE_WIDTH" : rec_width,
        "ALSAAUDIO_FORMAT" : INFORMAT,
        "DURATION" : record_secs,
        "START" : start_t,
        "END" : end_t
        }
    out_meta = out_folder.joinpath(start_t+"__"+end_t+"_meta.js")
    out_meta = open(out_meta, "w")
    json.dump(meta_data, out_meta)
    out_meta.close()


###################################################################################
##### THE FUNCTION TO CREATE A CALIBRATION FILE ####
###################################################################################

def record_calibration_file(out_folder, parameters, duration = 10):
    
    # taking the datetime at the begining of the calibration
    start_time = datetime.now()
    out_file = out_folder.joinpath("calibration_"+start_time.strftime(format = TIME_FORMAT)+".wav")
    
    # recuperation des parametres
    CHANNELS = parameters["channel"]
    INFORMAT = parameters["format"]
    RATE = parameters["rate"]
    FRAMESIZE = parameters["frame_size"]
    record_secs= parameters["duration"]

    # set up audio input
    recorder=alsaaudio.PCM(type=alsaaudio.PCM_CAPTURE)
    recorder.setchannels(CHANNELS)
    recorder.setrate(RATE)
    recorder.setformat(INFORMAT)
    recorder.setperiodsize(FRAMESIZE)


    frames = []
    for ii in range(0,int((RATE/FRAMESIZE)*duration)):
        frames.append(recorder.read()[1])


    # save the audio frames as .wav file
    wavefile = wave.open(out_file,'wb')
    wavefile.setnchannels(CHANNELS)
    
    # pour la selection du sample width, on va tricher et utiliser la valeur recommandee par pyaudio
    rec_width = pyaudio.get_sample_size(pyaudio.paInt16)
    wavefile.setsampwidth(rec_width)
    wavefile.setframerate(RATE)
    wavefile.writeframes(b''.join(frames))
    wavefile.close()
    
        


###################################################################################
##### THE RECORD MANAGER FOR LONG TERM RECORDING ####
###################################################################################


class RecordManager(object): 
    
    def __init__(self, parameters, tol, out_folder, stop_time) : 
        
        # chunk_duration doit etre specifiee en secondes
        # elle indique la duree d'un enregistrement
        self.parameters = parameters
        self.chunk_duration = parameters["duration"]
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
        
        ### Creating the working directory if required
        to_create = ["raw","merged","logs"]
        for fold in to_create : 
            new_folder = out_folder.joinpath(fold)
            if new_folder.isdir() == False : 
                new_folder.makedirs()
        
        self.rawfolder = out_folder.joinpath("raw") 
        self.mergedfolder = out_folder.joinpath("merged")
        self.logsfolder = out_folder.joinpath("logs")
        
        
    def StartRecording(self) : 
        """
        This method can be used to start a recording session with a connected microphone
        it used multithreading with two threads to ensure that when one is writing, the 
        second is recording
        """
        
        ## ouverture d'un fichier de log pour garder une trace des evenements
        start_session = datetime.now()
        log_name = start_session.strftime(format = "%Y/%m/%dT%H-%M-%S")+"_recordsession.txt"
        log_file = self.logsfolder.joinpath(log_name)

        
        ## definition d'une premi??re session d'enregistrement
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds = self.chunk_duration)
        print("launching the first Thread...")
        process1 = threading.Thread(target = mic_recorder, args = [self.parameters, start_time, end_time, self.rawfolder])
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
                    process2 = threading.Thread(target = mic_recorder, args = [self.parameters, start_time, end_time, self.rawfolder])
                    process2.start()
                    running = "p2"
                else : 
                    print("launching the Thread number 1...")
                    process1 = threading.Thread(target = mic_recorder, args = [self.parameters, start_time, end_time, self.rawfolder])
                    process1.start()
                    running = "p1"
                next_start = end_time
                print("the next thread is scheduled for "+next_start.strftime(format = "%Y/%m/%dT%H-%M-%S"))
                
                
                
    def create_data_collection_metadata(self) :
    
        """
        A meta_data file is a js file which contains many descriptors about a set of 
        records in a folder. It is used later to merge files or to generate reports
        A thing I want to implement is a calendar heatmap : https://cal-heatmap.com/v2/
        Things I want to save in a metadata js file
        - a dict with all the record wav files associated with their timestamps
        - a dict with all the calibration files
        - the total period covered by the files
        - ...
        """
        meta_data = {}
        
        # listing of all the wave files
        all_wav = self.rawfolder.files("*.wav")
        
        # separating calibration files and record files
        record_waves = []
        calbiration_waves = []
        
        # designating a lower time and a higher time
        higher_time = datetime(year = 1920, month = 1, day = 1, hour = 1)
        lower_time = datetime(year = 2220, month = 1, day = 1, hour = 1)
        
        for wav in all_wav :
            # this is not a calibration file
            if "calibration" not in wav :
                file_name = wav.split("/")[-1]
                date_extent = file_name[0:-10]
                start_dt, end_dt = date_extent.split("__")
                start_dt = datetime.strptime(start_dt, TIME_FORMAT)
                end_dt = datetime.strptime(end_dt, TIME_FORMAT)
                duration = end_dt - start_dt
                # checking the highest and lowest datetimes
                if lower_time > start_dt :
                    lower_time = start_dt
                if higher_time < end_dt :
                    higher_time = end_dt
                record_waves.append({
                    "start" : datetime.strftime(start_dt, TIME_FORMAT),
                    "end" : datetime.strftime(end_dt, TIME_FORMAT),
                    "duration" : nice_duration(duration),
                    "filename" : file_name,
                    "location" : str(wav)
                    })
            # this is a calibration file
            else :
                file_name = wav.split(".")[0]
                dt = file_name.split("_")[-1]
                dt = datetime.strptime(dt,TIME_FORMAT)
                calbiration_waves.append({
                    "datetime" : dt,
                    "filename" : file_name,
                    "location" : str(wav)
                    })
                
        # building the final dict
        meta_data = {
            "location" : self.rawfolder,
            "first_record" : datetime.strftime(lower_time, TIME_FORMAT),
            "last_record" : datetime.strftime(higher_time, TIME_FORMAT),
            "data_files" : record_waves,
            "calibration_files" : calbiration_waves
            }
        # writing it as json file
        out_file = self.rawfolder.joinpath("meta_data.json")
        out_file = open(out_file, "w")
        json.dump(meta_data,out_file)
        out_file.close()
        
        
    def create_data_report(self) : 
        """
        here, we want to create a report used to check what data were collected
        """
        ## reading the meta_data file
        meta_file = self.rawfolder.joinpath("meta_data.json")
        
        if meta_file.isfile() == False : 
            raise ValueError("There is currently no meta_data file for this folder, please create it before merging wav files")
        
        meta_data = json.load(open(meta_file,"r"))
        
        # preparing html
        root = Balise("html")
        head = Balise("head")
        # adding the styles and js scripts to the head
        d3_script = Balise("script", params = {"src" : "static/js/d3.v7.min.js"})
        calendar_script = Balise("script", params = {"src" : "static/js/cal-heatmap.min.js"})
        calendar_style = Balise("link", params = {"rel": "stylesheet",
                                                  "src" :"static/css/cal-heatmap.css"})
        head.children += [calendar_style,d3_script,calendar_script]
        root.children.append(head)
        
        # preparing the body
        body = Balise("body")
        calendar = Balise("div", {"id" : "cal-heatmap"})
        
        # preparing the json data
        js_data = []
        for element in meta_data["data_files"] : 
            start = datetime.strptime(element["start"], TIME_FORMAT)
            end = datetime.strptime(element["end"], TIME_FORMAT)
            vals = range(int(start.timestamp()), int(end.timestamp()),1)
            for stamp in vals : 
                js_data.append({str(stamp) : 1})
        js_data_string = json.dumps(js_data)
        js_code = Balise("script", {"type" : "text/javascript"})
        js_code.innerHTML = """data = """+js_data_string+""";
        var cal = new CalHeatMap();
        cal.init({
            data: data
            });
        """
            
            
        
        
            
            
            
        
### TESTING
                
if __name__ == "__main__" : 
    parameters = {
        "duration" : 10,
        "rate" : 48000, # rate par defaut du sonometre
        "format": alsaaudio.PCM_FORMAT_S16_LE, # format en 16 bit pour le moment
        "channel": 1, #on enregistre juste en mono
        "frame_size":4096, #recommande dans les tuto : 4096, recommande par Romain : 1024
        "duration" : 10 #petits enchantillons de 10sec
        }
    Recorder = RecordManager(parameters, tol = 5,
                             out_folder = Path("/home/pi/Desktop/Audio_processing/PyAudioRecorder/test_folder"),
                             stop_time = datetime.now() + timedelta(seconds = 30))
    Recorder.StartRecording()
#         
        
        
        
    