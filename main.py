#standard imports
import sys
import os
import json
from dataclasses import dataclass
#third-party imports
import openai
import streamlit as st

@dataclass
class ChatPersona():
    """Class to facilitate the creation of a chatbot persona with a name, age,
      gender, and personality"""

    name : str = "Agent"
    age : int = 25
    gender : str = "Male"
    personality : str = "Friendly and helpful"
    expertise : str = "General knowledge and assistance"
    backstory : str = ("Created by a team of AI engineers to assist with a variety of "   
                        "tasks and answer questions to the best of his ability.")
    def get_persona_string(self) -> str:
        """Returns a string representation of the persona"""
        return ("You are a chatbot with the following persona:\n"
                f"Name: {self.name}, Age: {self.age}, Gender: {self.gender}, "
                f"Personality: {self.personality}, Expertise: {self.expertise}, "
                f"Backstory: {self.backstory}"
                )

class ConversationManager():
    """Class to contain the logic of the chatbot's backend handling API tokens, token counting, 
    and containing conversation history
    """

    def __init__(self):
        """Initialization method for ConversationManager. Gets API keys config file and sets up
        openai client.
        """

        self.config : dict = {}
        self.config_path : str = "config.json"
        self.openai_client : openai.OpenAI = None
        self.conversation_history : list = []
        self.persona : ChatPersona = ChatPersona()
        self.system_message : str = "Respond to the user's input in a concise and professional manner."
        self.model : str = "gpt-4o-mini"
        self.max_tokens : int = 120
        self.temperature : float = 0.7
        self.top_p : float = 1.0
        self.frequency_penalty : float = 0.0
        self.presence_penalty : float = 0.0
        self.stop : list = None


        #check if config path sent as arguement
        if len(sys.argv) > 1:
            self.config_path = sys.argv[1]      
        #load config file
        try:
            self.config = json.load(open(self.config_path, "r", encoding="utf-8"))
        except FileNotFoundError:
            print(f"Config file not found at {self.config_path}")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"Config file at {self.config_path} is not a valid JSON file.")
            sys.exit(1)
        #set up openai client
        try:
            if os.path.exists(self.config['api-key']):
                with open(self.config['api-key'], 'r', encoding='utf-8') as f:
                    self.openai_client = openai.OpenAI(api_key=f.read().strip(), organization="org-R5XsfsexKwS6IQvpwxlSYDo8", project="proj_eZ8ukMbixEmLoL2SbqVicRr7")
            else:
                self.openai_client = openai.OpenAI(api_key=self.config['api-key'], organization="org-R5XsfsexKwS6IQvpwxlSYDo8", project="proj_eZ8ukMbixEmLoL2SbqVicRr7")
        except KeyError:
            print("api-key not found in config file.")
            sys.exit(1)
        return

    def set_persona(self, persona: ChatPersona = ChatPersona()) -> None:
        '''Function for establishing the personality of the AI Assistant'''
        self.persona = persona
    def set_custom_system_message(self, system_message: str = "You are a helpful Assistant"):
        '''Function that allows users to set their own system message'''
        self.system_message = system_message
    def chat_completion(self, user_input: str):
        '''Function for generating a response from the AI Assistant'''
        if not self.conversation_history:
            system_prompt : str = self.persona.get_persona_string() + "\n" + self.system_message
            self.conversation_history.append({"role": "system", "content": system_prompt})
        self.conversation_history.append({"role": "user", "content": user_input})
        try:
            chat_response = self.openai_client.chat.completions.create(
                model=self.model,
                messages= self.conversation_history,
                temperature=self.temperature,
                top_p=self.top_p,
                frequency_penalty=self.frequency_penalty,
                presence_penalty=self.presence_penalty,
                stop=self.stop
            )
        except openai.RateLimitError as e:
            print(f"Rate limit exceeded: {e}")
            return "I'm currently experiencing a high volume of requests. Please try again later."
        except openai.APIError as e:
            print(f"API error: {e}")
            return "I'm currently experiencing some technical difficulties. Please try again later."
        response_content = chat_response.choices[0].message.content
        self.conversation_history.append({"role": "assistant", "content": response_content})
        return response_content
    def reset_conversation_history(self):
        '''Function for resetting the conversation history'''
        self.conversation_history = []
if __name__ == "__main__":
    #Setup a default conversation manager
    cm = ConversationManager()
    #Setup the Streamlit UI
    st.title("Custom Chatbot")
    if "message_history" not in st.session_state:
        introduction : str = cm.chat_completion("Introduce yourself as if you are initiating the conversation.")
        st.session_state.message_history = [{"role": "assistant", "content": introduction}]
    #Display the chat history
    for message in st.session_state.message_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    #Accept user input
    prompt : str | None = st.chat_input("Enter your message here.")
    if prompt is not None:
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.message_history.append({"role": "user", "content": prompt})
        response : str = cm.chat_completion(prompt)
        with st.chat_message("assistant"):
            st.markdown(response)
        st.session_state.message_history.append({"role": "assistant", "content": response})
