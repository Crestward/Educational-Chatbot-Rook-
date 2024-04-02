import chainlit as cl
import random
import json 
import pickle 
import numpy as np

import nltk 
from nltk.stem import WordNetLemmatizer

from tensorflow.keras.models import load_model

from litsolutions import TextbookInfoRetriever 

lemmatizer = WordNetLemmatizer()

intents = json.loads(open('intents.json').read())
words = pickle.load(open('words.pkl', 'rb')) 
classes = pickle.load(open('classes.pkl', 'rb'))

model = load_model('chatbot_model.h5')


def clean_up_sentence(sentence):
    sentence_words = nltk.word_tokenize(sentence)
    sentence_words = [lemmatizer.lemmatize(word) for word in sentence_words]
    return sentence_words

def bag_of_words(sentence):
    sentence_words = clean_up_sentence(sentence)

    bag = [0] * len(words)

    for w in sentence_words:
        for i, word in enumerate(words): 
            if word == w:
                bag[i] = 1

    return np.array(bag)

def predict_class(sentence):
    bow = bag_of_words(sentence)
    res = model.predict(np.array([bow]))[0]
    ERROR_THRESHOLD = 0.25
    results = [[i, r] for i, r in enumerate(res) if r > ERROR_THRESHOLD]

    results.sort(key=lambda x: x[1], reverse=True)
    return_list = []
    for r in results:
        return_list.append({'intent': classes[r[0]], 'probability': str(r[1])})

    return return_list

def get_response(intents_list, intents_json):
    tag = intents_list[0]['intent']
    list_of_intents = intents_json['intents']
    result = None  # Initialize with a default value
    
    for i in list_of_intents:
        if i['tag'] == tag:
            result = random.choice(i['responses'])
            break
            
    return result

def get_answer(user_msg):
    ints = predict_class(user_msg)
    res = get_response(ints, intents)
    return res

print("60! Bot is running!®")


@cl.on_message
async def main(message):
    if isinstance(message, cl.Message):
        message_content = message.content
        if isinstance(message_content, str):
            # Use predict_class to identify intents
            intent = predict_class(message_content)

            if intent and intent[0]['intent'] == "textbook_help" and float(intent[0]['probability']) > 0.5:
                
                # Send an AskUserMessage to gather user input
                response = await cl.AskUserMessage(
                    content="What is the name of the textbook?",
                    timeout=60  # Specify a timeout for user response
                ).send()
                print(response['output'])

                if response and 'output' in response:
                    textbook_name = response['output']

                    response = await cl.AskUserMessage(
                        content="Which chapter are you referring to?",
                        timeout=60
                    ).send()

                    if response and 'output' in response:
                        chapter = response['output']

                        response = await cl.AskUserMessage(
                            content="What is the specific question or problem you need help with?",
                            timeout=60
                        ).send()

                        if response and 'output' in response:
                            question = response['output']
                        
                            
                            response_text = await TextbookInfoRetriever().retrieve_textbook_info(textbook_name, chapter, question)

                            # Provide the response to the user if it's not None
                            if response_text:
                                await cl.Message(content=response_text).send()
                        else:
                            await cl.Message(content="Sorry, I 2 couldn't get your question.").send()
                    else:
                        await cl.Message(content="Sorry, I 3 couldn't get the chapter information.").send()
                else:
                    await cl.Message(content="Sorry, I 4 couldn't get the textbook name.").send()
            else:
                # Handle other intents
                await cl.Message(
                    content=f"{get_answer(message_content)}"
                ).send()
        else:
            # Handle the case where message content is not a string
            print("Invalid message content type:", type(message_content))
    else:
        # Handle the case where the message is not a Message object
        print("Invalid message type:", type(message))
