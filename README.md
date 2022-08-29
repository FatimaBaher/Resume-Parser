
# Resume Parser 

## What is it  ❓

Resume Parsing is conversion of a free-form resume document into a structured set of information suitable for storage, reporting, and manipulation by software. Resume parsing helps recruiters to efficiently manage electronic resume documents sent electronically.

This project is a resume parser written in Python. It uses Machine Learning technologies (mainly NLP) to parse the content of the uploaded resume.

## Install it on your machine 📥

In order to try the resume parser on your machine, make sure you:

- Download the repo as a zip file and extract it to a certain directory on your machine.
- Have [Python 3](https://www.python.org/downloads/) installed on your system.
- Have [Spacy](https://spacy.io/usage) installed on you local machine (latest version).
- Run the following command in cmd inside the directory of the project `python -m spacy download "en_core_web_lg"` .

## Usage 💻

Once you have everything set up and run the script file, it will prompt you to enter to path to a resume (PDF). Make sure you enter the full absolute path of the PDF. 
> If you don't have one, you can download the test resume in the test folder.

## Limitations ⚠️

This project was developed quickly and with little prior knowledge to the techniques used. So it has some limitations like:

- Does not extract the years of work experience.
- Only supports the English language.
- Does not support all phone number formats (all countries).

## Conclusion & Future Plans 💭

I hope you find this project fun to play around with. This is the first product and will be optimized and extended. This service will be turned into an API with a web interface to make it accessible.
> Happy Coding :)
