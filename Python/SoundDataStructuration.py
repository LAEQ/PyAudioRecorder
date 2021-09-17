import threading
from path import Path # NOTE: installer la lib path.py
from datetime import date, datetime, timedelta
import time
import pause
import wave
import alsaaudio
import pyaudio
import json

TIME_FORMAT = "%Y-%m-%dT%H-%M-%S"


###################################################################################
##### THE FUNCTION TO CREATE A GLOBAL META_DATA FILE FOR A FOLDER ####
###################################################################################
def create_data_collection_metadata(folder) :
    
    """
    Things I want to save in a metadata js file
    - a dict with all the record wav files associated with their timestamps
    - a dict with all the calibration files
    - the total period covered by the files
    - ...
    """
    meta_data = {}
    
    # listing of all the wave files
    all_wav = folder.files("*.wav")
    
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
        "location" : folder,
        "first_record" : datetime.strftime(lower_time, TIME_FORMAT),
        "last_record" : datetime.strftime(higher_time, TIME_FORMAT),
        "data_files" : record_waves,
        "calibration_files" : calbiration_waves
        }
    # writing it as json file
    out_file = folder.joinpath("meta_data.json")
    out_file = open(out_file, "w")
    json.dump(meta_data,out_file)
    out_file.close()
    
    
    
###################################################################################
##### THE FUNCTION TO CONCATENATE MULTIPLE WAVE FILES ####
###################################################################################
    
def merge_wav_files(folder, max_duration) :
    
    meta_file = folder.joinpath("meta_data.json")
    merged_folder = folder.joinpath("merged")
    
    if meta_file.isfile() == False : 
        raise ValueError("There is currently no meta_data file for this folder, please create it before merging wav files")
    
    meta_data = json.load(open(meta_file,"r"))
    ## here I want to order the wav files with their dates
    
    record_files = [(
        datetime.strptime(el["start"], TIME_FORMAT),
        datetime.strptime(el["end"], TIME_FORMAT),
        el["location"]) for el in meta_data["data_files"]]
    
    #
    
    