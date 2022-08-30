#importing needed libraries

from io import StringIO
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
import spacy
from spacy.matcher import Matcher
from spacy import displacy
from spacy.pipeline import EntityRuler
import re
import time



# loading the english model from spacy to provide some basic functionality
model = spacy.load("en_core_web_lg")

#prparing the pipe 
config = {"overwrite_ents": True}  # allowing the entity ruler to overwrite the built-in ner matching
rulerER = model.add_pipe("entity_ruler",config=config) # adding the entity ruler
rulerActions = model.add_pipe("entity_ruler","ruleActions",config=config) # adding ruleActions to the pipe for match overlapping issues


###################################################################


#Getting new label entities for specified patterns from files

#Job Patterns
rulerER.from_disk('jobs.jsonl')
rulerActions.from_disk('jobs.jsonl')

#Location Pattern
f_location = open("newGPE.jsonl",'r')
line = eval(f_location.readline().strip())
rulerER.add_patterns([line])
rulerActions.add_patterns([line])
f_location.close()

#Education Patterns
f_ed = open("education.jsonl","r")
patterns=[]
line = f_ed.readline().strip()
while line:
    patterns.append(eval(line))
    line = f_ed.readline().strip()
rulerER.add_patterns(patterns)
rulerActions.add_patterns(patterns)
f_ed.close()

#Skills Patterns
f_skills = open("skills.jsonl","r")
patterns=[]
line = f_skills.readline().strip()
while line:
    patterns.append(eval(line))
    line = f_skills.readline().strip()
rulerER.add_patterns(patterns)
rulerActions.add_patterns(patterns)
f_skills.close()


#University Name Patterns
f_uni = open("universities_pattern.jsonl","r")
patterns=[]
line = f_uni.readline().strip()
while line:
    patterns.append(eval(line))
    line = f_uni.readline().strip()
rulerER.add_patterns(patterns)
rulerActions.add_patterns(patterns)
f_uni.close()

###################################################################

#Defining the ResumeParser class

class ResumeParser:

    def __init__(self,model=model):
        
        self.nlp = model
        self.matcher = Matcher(self.nlp.vocab)
        self.doc = None
        self.summary = {}
        self.text = ""
        
        
        
    def parseResume(self, resume_file_path):
        ''' This function is used for collecting information from a resume and saving them in a dictionary
        
            The following are the collected information: Name, Email, Phone Nymber(s), Location, University Name(s), Education, Job Title(s), Skill(s)
            
            
            Parameters:
                resume_file_path (str): The path of the resume to be parsed
                
            Returns:
                dict: The dictionary containing the parsed data
        '''
        
        #Get text from pdf
        self.text = self.getTextFromDoc(resume_file_path)
        
        self.doc=self.nlp(self.text)   # I wasted 6 hrs of my life because of this single line :)
        
        emails = []
        jobs = []
        skills = []
        universities = []
        edu=[]
        name = None
        location = None
        
        for ent in self.doc.ents:
            if name == None and ent.label_ == "PERSON":
                name = ent.text
            if ent.label_ == "EDUCATION":
                edu.append(ent.text)
            if ent.text not in skills and ent.label_ == "SKILL":
                skills.append(ent.text)
            if ent.text.capitalize() not in jobs and ent.label_ == "JOB":
                jobs.append(ent.text.capitalize())
            if location == None and ent.label_ == "GPE":
                location = ent.text
            if ent.text.capitalize() not in universities and ent.label_ == "UNIVERSITY":
                universities.append(ent.text.capitalize())  
        
        self.summary["Name"] = 'No Name Found' if name == None else name
        self.summary["Email"] = self.parseEmailAddress()
        self.summary["Phone Numbers"] = self.parsePhoneNumbers()
        self.summary["Location"] = 'No Location Found' if location == None else location
        self.summary["Education"] = edu
        self.summary["Skills"] = skills
        self.summary["Job Titles"] = jobs
        self.summary["Universities"] = universities
        #self.displayEntities()    #use for debugging purposes
        return self.summary

    def getTextFromDoc(self,doc_path):
        output_string = StringIO()
        resume = open(doc_path, 'rb')
        parser = PDFParser(resume)
        doc = PDFDocument(parser)
        rsrcmgr = PDFResourceManager()
        device = TextConverter(rsrcmgr, output_string, laparams=LAParams())
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        for page in PDFPage.create_pages(doc):
            interpreter.process_page(page)
        resume.close()
        return output_string.getvalue()

   
    def parseEmailAddress(self):
        #use built in ner LIKE_EMAIL flag to get the name
        pattern=[{"LIKE_EMAIL":True}]
        self.matcher.add("Email",[pattern])
        matches=self.matcher(self.doc)
        if len(matches) > 0:
            first_match = matches[0]
            start = first_match[1]
            end = first_match[2]
            email = self.doc[start:end]
        else:
            email = 'Email Not Found'
        self.matcher.remove("Email")  
        return email.text

    def parsePhoneNumbers(self): 
        #use re to extract the phone number formats
        usPattern = r"((?:\+\d{2})?\d{3,4}\D?\d{3}\D?\d{3})"  #US
        lbnPattern = r"((\(?(961|00961|\+961\)?)?(\s?)(-?)(\/?)(\d{2}))\s?\/?\-?\s?\d{3}\s?\-?\/?\d{3})"  #LEBANON
        phone_numbers=[]
        lbnNbs = re.findall(lbnPattern,self.text)
        usNbs = re.findall(usPattern,self.text)
        for lnumber in lbnNbs:
            phone_numbers.append(lnumber[0]) #taking only group of index zero (first group) for each match returned by findall
        for unumber in usNbs:
            phone_numbers.append(unumber[0])
        return phone_numbers
    

    def parseEducation(self):
        
        #defining the pattern that will be labeled as EDUCATION by the matcher 
        pattern=[{"label":"EDUCATION", "pattern":[{"LOWER":{"IN":["associate","bachelor's","master's","doctoral","master","bachelor", "bachelors", "masters", "bs", "phd", "doctorate", "professor"]}}, {"LOWER":"degree","OP":"?"},{"LOWER":{"IN":["of","in"]},"OP":"?"},{"ENT_TYPE":"SKILL","OP":"+"}]}]
        self.matcher.add("EDUCATION",[pattern],greedy="LONGEST") 
        matches=self.matcher(self.doc)
        edu=[]
        for match_id,start,end in matches:       
            match=self.doc[start:end] 
            edu.append(match)
        self.matcher.remove("EDUCATION")
        return edu
    
    
    def displayEntities(self):
        if self.doc:
            displacy.render(self.doc, style='ent',jupyter=True)


#creating a single instance of the class 
rp=ResumeParser(model)


#function to print the summary
def displayInfo(infoDictionary):
    BOLD = '\033[1m'
    ENDBOLD = '\033[0m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    for key, value in infoDictionary.items():
        print(YELLOW+BOLD+key+":"+ENDBOLD+BLUE,end=' ')
        if type(value) == list:
            for i in range(len(value)):
                if i < len(value)-1:
                    print(value[i]+','+BLUE,end=' ')
                    continue
                print(value[i]+BLUE)
        else:
            print(value)
        print(".............................................................................................................")


#main function to parse the resume
def parseResume():
    print('\033[92mEnter the path of the resume to be parsed:')
    resume_path = input("")
    print('\nParsing Started',end='')
    time.sleep(0.6)
    print('.',end='')
    time.sleep(0.6)
    print('.',end='')
    time.sleep(0.6)
    print('.\n')
    info = rp.parseResume(resume_path)
    displayInfo(info)


parseResume()

















