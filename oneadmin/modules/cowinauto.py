'''
Created on 05-Mar-2021

@author: root
'''
from oneadmin.core.action import ACTION_PREFIX, Action, ActionResponse
from oneadmin.core.intent import INTENT_PREFIX
from oneadmin.core.event import DataEvent
from oneadmin.core.abstracts import IModule, IntentProvider, ServiceBot
from oneadmin.core import grahil_types

from concurrent.futures.thread import ThreadPoolExecutor
from tornado import ioloop

import tornado
import time
import logging
import datetime
from typing import List, Text
import json

from selenium import webdriver
from time import process_time_ns, sleep

import smtplib
import time
import imaplib
import email
import traceback
import json
import os
from pathlib import Path


from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC




class CowinAutomation(IModule):
    '''
    classdocs
    '''
    
    NAME = "cowin_automation"
    
    thread_pool = ThreadPoolExecutor(5)



    def __init__(self, conf):
        '''
        Constructor
        '''
        self.logger = logging.getLogger(self.__class__.__name__)
        self.__conf = conf
    
    
    
        
    def getname(self) ->Text:
        return CowinAutomation.NAME    
        

    
    def initialize(self) ->None:
        self.logger.info("Module init")
        tornado.ioloop.IOLoop.current().spawn_callback(self.check_available_schedules)
    


    def get_url_patterns(self)->List:
        return []
    
    
    
    '''
        Returns a list of supported actions
    '''
    def supported_actions(self) -> List[object]:
        return [ActionCoWinScheduleNotify()]


    '''
        Returns a list supported of action names
    '''
    def supported_action_names(self) -> List[Text]:
        return [ACTION_COWIN_SCHEULE_NOTIFY]
    
    
    
    '''
        Returns a list supported of intents
    '''
    def supported_intents(self) -> List[Text]:
        return [INTENT_COWIN_SCHEULE_NOTIFY]




    async def check_available_schedules(self):
        url = self.__conf["site_url"]
        phonenumber = self.__conf["phone_number"]
        pincode = self.__conf["pincode"]
        email_address = self.__conf["otp_mail_server_user"]
        email_password = self.__conf["otp_mail_server_password"]
        schedule_image_name = self.__conf["schedule_image_name"]
        schedule_image_path = await tornado.ioloop.IOLoop.current().run_in_executor(CowinAutomation.thread_pool, self.find_schedule, url, phonenumber, pincode, email_address, email_password, schedule_image_name)
        await self.dispatchevent(DataEvent(topic="/cowin/shedule/snapshot",data = {"image": schedule_image_path}))
        pass

    

    def read_email_from_gmail(self, email_user:str, email_password:str)->str:

        SMTP_SERVER = "imap.gmail.com" 
        SMTP_PORT = 993

        OTP = None

        try:
            mail = imaplib.IMAP4_SSL(SMTP_SERVER)
            mail.login(email_user,email_password)
            mail.select('inbox')

            data = mail.search(None, 'ALL')
            mail_ids = data[1]
            id_list = mail_ids[0].split()   
            first_email_id = int(id_list[0])
            latest_email_id = int(id_list[-1])

            try:

                for i in range(latest_email_id,first_email_id, -1):
                    data = mail.fetch(str(i), '(RFC822)' )
                    for response_part in data:
                        arr = response_part[0]
                        if isinstance(arr, tuple):
                            msg = email.message_from_string(str(arr[1],'utf-8'))
                            email_subject = msg['subject']
                            email_from = msg['from']
                            if "CoWIN" in email_from:
                                email_payload:str = msg.get_payload(decode=True).decode('UTF-8')
                                end = email_payload.rfind('}')
                                content = email_payload[0:end+1]
                                obj= json.loads(content)
                                OTP = obj["otp"]
                                mail.store(str(i), '+FLAGS', '\\Deleted') 
                                return OTP
            
            except Exception as e:
                self.logger.error(str(e))
            finally:
                if mail != None:
                    mail.expunge()      


        except Exception as e:
            traceback.print_exc() 
            self.logger.error(str(e))     
    

    def find_schedule(self, url, phonenumber, pincode, email_server_username, email_server_password, snapshot_name:str):

        try:
            driver = None

            options = webdriver.ChromeOptions()
            options.add_argument("no-sandbox")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--start-maximized")
            options.add_argument("--headless")
            options.add_argument("window-size=1024,900")


            self.logger.info("Starting headless chrome...")

            driver = webdriver.Chrome(options=options, executable_path="/home/rajdeeprath/chromedriver_linux64/chromedriver");
            driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36'})
            
            self.logger.info("Loading CoWIN website...")
            driver.implicitly_wait(15)

            driver.get(url)


            self.logger.info("Entering phone number to request OTP...")
            mobinput = driver.find_element_by_xpath('//*[@id="mat-input-0"]')
            mobinput.send_keys(phonenumber)
            getotpbtn = driver.find_element_by_xpath('/html/body/app-root/ion-app/ion-router-outlet/app-login/ion-content/div/ion-grid/ion-row/ion-col/ion-grid/ion-row/ion-col[1]/ion-grid/form/ion-row/ion-col[2]/div/ion-button')
            getotpbtn.click()

            sleep(15)
            self.logger.info("Check for OTP on handset...")
            otp = self.read_email_from_gmail(email_server_username, email_server_password)

            if otp == None:
                raise Exception("Could not get OTP :(")

            self.logger.info("OTP received! Entering OTP...")            
            otp_input = driver.find_element_by_xpath('/html/body/app-root/ion-app/ion-router-outlet/app-login/ion-content/div/ion-grid/ion-row/ion-col/ion-grid/ion-row/ion-col/ion-grid/form/ion-row/ion-col[2]/ion-item/mat-form-field/div/div[1]/div/input')
            otp_input.send_keys(otp)
            otp_submit_btn = driver.find_element_by_xpath('/html/body/app-root/ion-app/ion-router-outlet/app-login/ion-content/div/ion-grid/ion-row/ion-col/ion-grid/ion-row/ion-col/ion-grid/form/ion-row/ion-col[3]/div/ion-button')
            otp_submit_btn.click()

            sleep(5)
            self.logger.info("Preparing to look for available schedules")
            
            schedule_button=driver.find_element_by_xpath('/html/body/app-root/ion-app/ion-router-outlet/app-beneficiary-dashboard/ion-content/div/div/ion-grid/ion-row/ion-col/ion-grid[1]/ion-row[4]/ion-col/ion-grid/ion-row[4]/ion-col[2]/ul/li')
            hov = ActionChains(driver).move_to_element(schedule_button)
            hov.perform()
            sleep(2)  
            schedule_button.click()

            sleep(5)
            self.logger.info("Entering desired pincode " + pincode + " to look for specific centers")            
            driver.get_screenshot_as_file("/home/rajdeeprath/screenshot.png")
            search_pincode_input = driver.find_element_by_xpath('/html/body/app-root/ion-app/ion-router-outlet/app-appointment-table/ion-content/div/div/ion-grid/ion-row/ion-grid/ion-row/ion-col/ion-grid/ion-row/ion-col[2]/form/ion-grid[1]/ion-row[1]/ion-col[3]/mat-form-field/div/div[1]/div/input')
            search_pincode_input.send_keys(pincode)
            search_button = driver.find_element_by_xpath('/html/body/app-root/ion-app/ion-router-outlet/app-appointment-table/ion-content/div/div/ion-grid/ion-row/ion-grid/ion-row/ion-col/ion-grid/ion-row/ion-col[2]/form/ion-grid[1]/ion-row[1]/ion-col[4]/ion-button')
            sleep(2)  
            search_button.click()

            sleep(5)
            age_filter_btn = driver.find_element_by_xpath('/html/body/app-root/ion-app/ion-router-outlet/app-appointment-table/ion-content/div/div/ion-grid/ion-row/ion-grid/ion-row/ion-col/ion-grid/ion-row/ion-col[2]/form/ion-grid[1]/ion-row[2]/ion-col[1]/div/div[1]/label')
            age_filter_btn.click()
            
            
            self.logger.info("Capturing available appointment schedule")
            sleep(5)
            
            home_dir = Path.home()
            image = os.path.join(home_dir, snapshot_name)

            if os.path.exists(image) and os.path.isfile(image):
                os.remove(image)
            
            driver.get_screenshot_as_file(image)
            return image
            

        except Exception as e:
            self.logger.error(str(e))
            return None

        finally:
            if driver != None:
                driver.quit()



# custom intents
INTENT_COWIN_SCHEULE_NOTIFY = INTENT_PREFIX + "cowin_schedule_notify"


# custom actions
ACTION_COWIN_SCHEULE_NOTIFY = ACTION_PREFIX + "cowin_schedule_notify"


'''
Module action demo
'''
class ActionCoWinScheduleNotify(Action):


    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    
    '''
    Abstract method, must be defined in concrete implementation. action names must be unique
    '''
    def name(self) -> Text:
        return ACTION_COWIN_SCHEULE_NOTIFY
    
    
    
    
    
    '''
    async method that executes the actual logic
    '''
    async def execute(self, requester:IntentProvider, modules:grahil_types.Modules, params:dict=None) -> ActionResponse:
        service_bot = None
        
        if modules.hasModule("service_bot"):
            service_bot:ServiceBot = modules.getModule("service_bot")
            image_path:Text = params["__event__"]["data"]["image"]
            self.logger.info("Sending appointment schedule snapshot to phone")
            await service_bot.sendImage(image_path, "Schedule")
            return ActionResponse(data = None, events=[])
        else:
            raise ModuleNotFoundError("`service_bot` module does not exist")
        pass


        