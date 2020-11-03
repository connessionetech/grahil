'''
Created on 28-Oct-2020

@author: rajdeeprath
'''

import re
#from sklearn.feature_extraction.text import TfidfVectorizer
#from sklearn.metrics.pairwise import cosine_similarity

import nltk

import warnings
import logging
import tornado
import random

import copy



class DefaultInterpreter(object):
    
    '''
    classdocs
    https://github.com/parulnith/Building-a-Simple-Chatbot-in-Python-using-NLTK/blob/master/chatbot.py
    https://blog.datasciencedojo.com/building-a-rule-based-chatbot-in-python/
    '''

    def __init__(self, filemanager=None, conf=None):
        '''
        Constructor
        '''
        warnings.filterwarnings('ignore')
        self.logger = logging.getLogger(self.__class__.__name__)
        self.__conf = conf
        self.__filemanager = filemanager
        self.__keywords = {}
        self.__responses = {}
        self.__actions = {}
        
        tornado.ioloop.IOLoop.current().spawn_callback(self.__download_corpus)
        pass
    
    
    async def __download_corpus(self):
        '''
        nltk.download('popular', quiet=True) # for downloading packages
        # uncomment the following only the first time
        nltk.download('punkt') # first-time use only       
        '''
        nltk.download('wordnet') # first-time use only
        await self.init_knowledgebase()
        pass
    
    
    def isReady(self):
        return True
    
    
    async def init_knowledgebase(self):
        
        try:
            vocabulary = self.__conf["vocabulary"]
            for item in vocabulary:
                intent = item["intent"]
                seed = item["seed"]
                keywords = item["keywords"]
                responses = item["responses"]
                action = item["action"]
                synonyms=[]
                for syn in nltk.corpus.wordnet.synsets(seed):
                    for lem in syn.lemmas():
                        # Remove any special characters from synonym strings
                        lem_name = re.sub('[^a-zA-Z0-9 \n\.]', ' ', lem.name())
                        synonyms.append('.*\\b'+lem_name+'\\b.*')
                
                for k in keywords:
                    synonyms.append('.*\\b'+k+'\\b.*') 
                
                self.__keywords[intent] = synonyms
                self.__responses[intent] = responses
                self.__actions[intent] = action
            
            tmp = {}    
            for intent, keys in self.__keywords.items():
                # Joining the values in the keywords dictionary with the OR (|) operator updating them in keywords_dict dictionary
                tmp[intent]=re.compile('|'.join(keys))
            self.__keywords = tmp
            
        except Exception as e:
            err = "Unable to load primary configuration " + str(e)
            self.logger.error(err)
        
        
        
    def LemTokens(self, tokens):
        return [self.lemmer.lemmatize(token) for token in tokens]
    
        
    def LemNormalize(self, text):
        return self.LemTokens(nltk.word_tokenize(text.lower().translate(self.remove_punct_dict)))
    
    
    # Generating response
    '''
    def response(self, user_response):
        robo_response=''
        self.sent_tokens.append(user_response)
        TfidfVec = TfidfVectorizer(tokenizer=self.LemNormalize, stop_words='english')
        tfidf = TfidfVec.fit_transform(self.sent_tokens)
        vals = cosine_similarity(tfidf[-1], tfidf)
        idx=vals.argsort()[0][-2]
        flat = vals.flatten()
        flat.sort()
        req_tfidf = flat[-2]
        if(req_tfidf==0):
            robo_response=robo_response+"I am sorry! I don't understand you"
            return robo_response
        else:
            robo_response = robo_response+self.sent_tokens[idx]
            return robo_response
    '''
        
    
    
    
    def actionable_response(self, user_input):
        matched_intent = None
        user_input = user_input.lower()
        for intent,pattern in self.__keywords.items():
            # Using the regular expression search function to look for keywords in user input
            if re.search(pattern, user_input): 
                # if a keyword matches, select the corresponding intent from the keywords_dict dictionary
                matched_intent=intent
        # The fallback intent is selected by default
        key=None 
        if matched_intent in self.__keywords:
            # If a keyword matches, the fallback intent is replaced by the matched intent as the key for the responses dictionary
            key = matched_intent
            
        # The chatbot prints the response that matches the selected intent
        if key != None:
            response_text = random.choice(self.__responses[key])
            action = self.__actions[key]
        else:
            response_text = "I am sorry! I don't understand you"
            action = None
            
        return {"text": response_text, "action" : copy.deepcopy(action)}
    