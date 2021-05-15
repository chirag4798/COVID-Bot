# This files contains your custom actions which can be used to run
# custom Python code.

# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions
import requests, re
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher

remove_new_line = lambda string: re.sub("\n", "", string)
TOP_N_RESULTS = 10

class ActionGetInformation(Action):

    def name(self) -> Text:
        return "action_get_information"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        """Uses various APIs to fetch city and service information and dispatches appropriate responses.

        Args:
            dispatcher (CollectingDispatcher)
            tracker (Tracker)
            domain (Dict[Text, Any])

        Returns:
            List[Dict[Text, Any]]
        """
        zipcode = tracker.get_slot('zipcode')
        service_type = tracker.get_slot('service_type')
        zipcode_data = requests.get(f"https://api.postalpincode.in/pincode/{zipcode}").json()
        if zipcode_data[0]['Status'] == 'Success':
            city = zipcode_data[0]['PostOffice'][0]['District']
        else:
            response = "Please enter a valid pincode."
            dispatcher.utter_message(text=response)
            return []
        try:
            data = requests.get(f"http://ec2-3-23-130-174.us-east-2.compute.amazonaws.com:8000/resource?city={city}&category={service_type}").json()['data'][:TOP_N_RESULTS]
        except Exception as e:
            response = f"Error: '{e}'. The requested service-type '{service_type}' not found or its taking longer than expected to fetch the information."
            dispatcher.utter_message(text=response)
            return []
        response = None
        for i, d in enumerate(data, 1):
            response = f"Organisation:\t{remove_new_line(d['organisation'])}\nContact:\t{remove_new_line(d['contact'])}\nPhone:\t\t{remove_new_line(d['phone'])}\n{'.'*60}\n\n"
            dispatcher.utter_message(text=response)
        if not response:
            response = "Sorry, no data found!"
            dispatcher.utter_message(text=response)
        return [SlotSet('zipcode', zipcode), SlotSet('service_type', service_type)]
