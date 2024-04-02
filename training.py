import random
import json
import pickle
import numpy as np
import nltk
from nltk.stem import WordNetLemmatizer
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Activation, Dropout
from tensorflow.keras.optimizers import SGD

nltk.download('punkt')
nltk.download('wordnet')

lemmatizer = WordNetLemmatizer()
intents = json.loads(open("intents.json").read())
words = []
classes = []
documents = []
ignore_letters = ['?', '.', '!', ',']

for intent in intents['intents']:
    for pattern in intent['patterns']:
        word_list = nltk.word_tokenize(pattern)
        words.extend(word_list)
        documents.append((word_list, intent['tag']))
        if intent['tag'] not in classes:
            classes.append(intent['tag'])

words = [lemmatizer.lemmatize(word.lower()) for word in words if word not in ignore_letters]
words = sorted(set(words))
classes = sorted(set(classes))

pickle.dump(words, open('words.pkl', 'wb'))
pickle.dump(classes, open('classes.pkl', 'wb'))

training_data = []
output_data = []

output_empty = [0] * len(classes)

def bag_of_words(sentence):
    sentence_words = nltk.word_tokenize(sentence)
    sentence_words = [lemmatizer.lemmatize(word.lower()) for word in sentence_words]
    bag = [0] * len(words)
    for s in sentence_words:
        if s in words:
            bag[words.index(s)] = 1

    return np.array(bag)

for document in documents:
    sentence = ' '.join(document[0])
    bag = bag_of_words(sentence)
    output_row = list(output_empty)
    output_row[classes.index(document[1])] = 1

    training_data.append(bag)
    output_data.append(output_row)

training_data = np.array(training_data)
output_data = np.array(output_data)

model = Sequential()

model.add(Dense(128, input_shape=(len(words),), activation='relu'))
model.add(Dropout(0.5))

model.add(Dense(64, activation='relu'))
model.add(Dropout(0.5))

model.add(Dense(len(classes), activation='softmax'))

sgd = SGD(learning_rate=0.01, momentum=0.9, nesterov=True)

model.compile(loss='categorical_crossentropy', optimizer=sgd, metrics=['accuracy'])
hist = model.fit(training_data, output_data, epochs=200, batch_size=5, verbose=1)

# Find the highest accuracy
highest_accuracy = max(hist.history['accuracy'])
print("Highest Accuracy Achieved:", highest_accuracy)

model.save('chatbot_model.h5', hist)

print('done')
