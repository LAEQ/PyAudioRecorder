# -*- coding: utf-8 -*-
"""
Created on Tue Apr 05 10:18:18 2016
@author: GelbJ
"""
from json2html import json2html
from bs4 import BeautifulSoup


def JsonToTable(Dico) : 
    Txt = json2html.convert(Dico)
    return TxtToBalise(Txt)
    

#####################################################
#####################################################
# MODULE D'ASSISTANCE A L'ECRITURE DE FICHIER HTML
    

def TxtToBalise(Txt):
    HTML = BeautifulSoup(Txt,'html.parser')
    Table = HTML.children.next()
    return RecursiveSoupe(Table)
    
    
def RecursiveSoupe(Soupe) : 
    try : 
        ThisBalise = Balise(Soupe.name,Soupe.attrs)
        for Child in Soupe.children :
            if Child.name is not None :
                ThisBalise.Children.append(RecursiveSoupe(Child))
            else : 
                ThisBalise.innerHTML = Child
        return ThisBalise
    except : 
        print(Soupe)
        print(Soupe.name)
        raise ValueError("Strange Error")
    

class Balise() :
    def __init__(self,Type,Params={}) :
        self.Type = Type
        self.Children=[]
        self.Params=Params
        self.innerHTML=""
        if Type in ["img","br","input","area","meta","link"] :
            self.Orpheline=True
        else :
            self.Orpheline=False
            
    def __repr__(self) :
        return "Balise "+self.Type
        
    #fonction pour obtenir en string le contenu de la balise
    def ToString(self,Sortie="",indent=0) :
        for e in range(indent):
            Sortie+="    "
        Iindent=indent
        Sortie+="<"+self.Type
        for key,value in self.Params.items() :
            Sortie+=" "+key+"="
            if type(value)==str :
                Sortie+="'"+value+"'"
            else :
                Sortie+=str(value)
        if self.Orpheline==True :
            Sortie+="/>"
        else :
            Sortie+=">"

        Sortie+=self.innerHTML
        indent+=1
        for element in self.Children :
            Sortie+="\n"
            Sortie=element.ToString(Sortie=Sortie,indent=indent)
        if self.Orpheline==False :
            if len(self.Children)>0 :
                Sortie+="\n"
                for e in range(Iindent):
                    Sortie+="    "
            Sortie+="</"+self.Type+">"
        return Sortie
            
    def Write(self,Destination) :
        File = open(Destination,"w")
        File.write(self.ToString())
        File.close()
        
if __name__=="__main__" :
    Dico = {'J1': [{'Letter': 'A', 'Number': 1},
      {'Letter': 'B', 'Number': 2},
      {'Letter': 'C', 'Number': 3}],
     'J2': [{'Letter': 'A', 'Number': 1},
      {'Letter': 'B', 'Number': 2},
      {'Letter': 'C', 'Number': 3}]}
    Titi = JsonToTable(Dico)

