# -*- coding: utf-8 -*-
"""2_TCS_NN.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1btZuf4Cby7_nqKDNxk5TkxCjSGZ0ipJc

## A Deep Learning Model for accurately predicting the overall emotion of the paragraph.
"""

from google.colab import drive
drive.mount('/content/drive')

cd /content/drive/MyDrive/Resources

"""### Importing libraries"""

import pandas as pd
import numpy as np
import seaborn as sns                           
import matplotlib.pyplot as plt   
from tqdm._tqdm_notebook import tqdm_notebook
tqdm_notebook.pandas()
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

from gensim.models import fasttext
from contractions import contraction_map
import string,re

# Libraries for Deep Learning

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer
import tensorflow as tf
from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences
from keras.layers import Dense, Embedding, Bidirectional, SpatialDropout1D, Input, TimeDistributed, Flatten, LSTM, GRU, Dropout
from keras.models import Sequential, save_model, Model
from keras.utils.np_utils import to_categorical
from keras.callbacks import EarlyStopping,ModelCheckpoint

"""

### Data Preprocessing"""

data = pd.read_csv('/content/drive/MyDrive/Resources/text_emotion.csv')

data.head()

data.sentiment.value_counts()

plt.figure(figsize=(12,5))
sns.countplot(x='sentiment', data = data)
plt.show()

df_temp = data.copy()

df_temp.dtypes

# Dropping rows with irrelevant emotion labels
df_temp = df_temp.drop(df_temp[df_temp.sentiment == 'boredom'].index)
df_temp = df_temp.drop(df_temp[df_temp.sentiment == 'enthusiasm'].index)
df_temp = df_temp.drop(df_temp[df_temp.sentiment == 'empty'].index)
df_temp = df_temp.drop(df_temp[df_temp.sentiment == 'fun'].index)
df_temp = df_temp.drop(df_temp[df_temp.sentiment == 'relief'].index)
df_temp = df_temp.drop(df_temp[df_temp.sentiment == 'surprise'].index)
df_temp = df_temp.drop(df_temp[df_temp.sentiment == 'love'].index)
df_temp = df_temp.drop(df_temp[df_temp.sentiment == 'hate'].index)

df_temp.sentiment.value_counts()

df_temp

df_temp = df_temp.drop('author',axis=1)
df_temp

df_temp.reset_index(drop=True,inplace=True)

df_temp.drop('tweet_id',axis=1,inplace=True)

df_temp.shape

df_temp.columns = ['sentiment','text']

df_temp.sentiment.value_counts()

df_temp

"""### SMOTE For handling class imbalance"""

class_count_0, class_count_1, class_count_2, class_count_3, class_count_4 = df_temp.sentiment.value_counts()
class_count_anger_updated = df_temp[df_temp['sentiment'] == 'anger'].sample(class_count_3,replace=True)
class_count_anger_updated.reset_index(drop=True,inplace=True)

class_count_neutral = df_temp[df_temp['sentiment'] == 'neutral']
class_count_worry = df_temp[df_temp['sentiment'] == 'worry']
class_count_happiness = df_temp[df_temp['sentiment'] == 'happiness']
class_count_sadness= df_temp[df_temp['sentiment'] == 'sadness']

df = pd.concat([class_count_neutral,class_count_worry,class_count_happiness,class_count_sadness,class_count_anger_updated],axis=0)

df.sentiment.value_counts()

df

df.reset_index(drop = True, inplace= True)

df

#Using Sentiment lexicons to be excluded from stopwords
df_pos = pd.read_csv('/content/drive/MyDrive/Resources/lexicons/negative.csv')
df_neg = pd.read_csv('/content/drive/MyDrive/Resources/lexicons/positive.csv')

"""### Data Cleaning"""

def expand_text(text):
    text = text.lower()
    text = text.replace("`","'")
    
    #Expand Contractions
    contraction_dict = contraction_map
    contraction_keys = list(contraction_dict.keys())
    
    for word in text.split():
        if word in contraction_keys:
            text = text.replace(word, contraction_dict[word])
        else:
            continue
    
    return text

def clean_text(text):
    text = text.translate(string.punctuation)
    text = text.lower().split()
    
    df_pos_words = list(df_pos.words)
    df_neg_words = list(df_neg.words)
    
    positive = []
    for i in range(0,len(df_pos_words)):
        positive.append(df_pos_words[i].lower().replace(" ",""))
        
    negative = []
    for i in range(0,len(df_neg_words)):
        negative.append(df_neg_words[i].lower().replace(" ",""))
        
    pos_set = set(positive)
    neg_set = set(negative)
    
    keywords = set(["above","and","below","not"])
    
    keywords.update(pos_set)
    keywords.update(neg_set)
    
    stopwords_set = set(stopwords.words('english'))
    stops = stopwords_set - keywords
    
    
    text = [w for w in text if not w in stops]
    text = " ".join(text)
    
    text = re.sub(r"[^A-Za-z0-9^,!./\'+-=]"," ",text)
    text = re.sub(r"what's","what is",text)
    text = re.sub(r"\'s"," ",text)
    text = re.sub(r"\'ve"," have ",text)
    text = re.sub(r"n't"," not ",text)
    text = re.sub(r"i'm"," i am ",text)
    text = re.sub(r"\'re"," are ",text)
    text = re.sub(r"\'d", " would ",text)
    text = re.sub(r"\'ll", " will ",text)
    text = re.sub(r","," ",text)
    text = re.sub(r"\."," ",text)
    text = re.sub(r"!"," ! ",text)
    text = re.sub(r"\/"," ",text)
    text = re.sub(r"\^"," ^ ",text)
    text = re.sub(r"\+"," + ",text)
    text = re.sub(r"\-"," - ",text)
    text = re.sub(r"\="," = ",text)
    text = re.sub(r"'"," ",text)
    text = re.sub(r"(\d+)(k)",r"\g<1>000",text)
    text = re.sub(r":", " : ",text)
    text = re.sub(r" e g "," eg ",text)
    text = re.sub(r"b g "," bg ",text)
    text = re.sub(r" u s "," american ",text)
    text = re.sub(r"\0s","0",text)
    text = re.sub(r"e - mail","email",text)
    text = re.sub(r"\s{2,}"," ",text)
    
    text = text.split()
    lemmatizer = WordNetLemmatizer()
    lemmatized_words = [lemmatizer.lemmatize(word) for word in text]
    text = " ".join(lemmatized_words)
    
    return text

df

df['text'] = df['text'].progress_apply(lambda x : expand_text(x))

nltk.download('wordnet')
nltk.download('stopwords')

df['text'] = df['text'].progress_apply(lambda x: clean_text(x))

df

df = df.sample(frac=1)

df.reset_index(drop=True,inplace=True)

df

"""### Create Tokenizer"""

tokenizer = Tokenizer()
tokenizer.fit_on_texts(df['text'])
vocab_size = len(tokenizer.word_index)+1
print(vocab_size)

sequences = tokenizer.texts_to_sequences(df['text'])
data = pad_sequences(sequences,maxlen=50)

"""### Word Embeddings Fasttext"""

!wget https://dl.fbaipublicfiles.com/fasttext/vectors-english/wiki-news-300d-1M-subword.vec.zip

!unzip wiki-news-300d-1M-subword.vec.zip

embeddings_index = {}
f = open('wiki-news-300d-1M-subword.vec',encoding='utf-8')
for line in f:
    values = line.split()
    word = values[0]
    coefs = np.asarray(values[1:],dtype="float32")
    embeddings_index[word] = coefs
f.close()

"""### Create a weight matrix """

embedding_matrix = np.zeros((vocab_size,300))
for word,index in tokenizer.word_index.items():
    if index > vocab_size -1:
        break
    else:
        embedding_vector = embeddings_index.get(word)
        if embedding_vector is not None:
            embedding_matrix[index] = embedding_vector

"""### Model Building"""

max_len = 50

es = EarlyStopping(monitor='val_loss',verbose=1,patience=10)
mc = ModelCheckpoint('./saved_models/best_model.h5',save_best_only=True,verbose=1)

df['sentiment'].value_counts()

"""### Test layers"""

model_lstm = Sequential()
model_lstm.add(Embedding(vocab_size,300,weights=[embedding_matrix],input_length=max_len,trainable=False))
model_lstm.add(LSTM(128,dropout=0.5))
model_lstm.add(Dense(100,activation='relu'))
model_lstm.add(Dense(100,activation='relu'))
model_lstm.add(Dense(5,activation='softmax'))
model_lstm.compile(loss='categorical_crossentropy',optimizer='rmsprop',metrics=['accuracy'])

model_lstm.summary()

from sklearn.preprocessing import LabelEncoder
encoder = LabelEncoder()
labels = encoder.fit_transform(df['sentiment'])
labels = to_categorical(labels)

model_lstm.fit(data,labels,validation_split=0.1,epochs=20)

txt = ["India Overtakes Russia As Third Worst-Hit Nation In COVID-19 Tally "]
seq = tokenizer.texts_to_sequences(txt)
padded = pad_sequences(seq, maxlen=max_len)
pred = model_lstm.predict(padded)
labels = ['anger',' happiness','neutral',' sadness','worry']
print(pred, labels[np.argmax(pred)])

txt = ["Won the lottery! yay!"]
seq = tokenizer.texts_to_sequences(txt)
padded = pad_sequences(seq, maxlen=max_len)
pred = model_lstm.predict(padded)
labels = ['anger',' happiness','neutral',' sadness','worry']
print(pred, labels[np.argmax(pred)])

fp = './saved_models/best_model.h5'
save_model(model_lstm,fp,include_optimizer=True)

from keras.utils.vis_utils import plot_model
plot_model(model_lstm, to_file='model_plot.jpeg', show_shapes=True, show_layer_names=True)

def create_nn():
  model = Sequential()
  model.add(Embedding(vocab_size,300,weights=[embedding_matrix],input_length=max_len,trainable=False))
  model.add(LSTM(128,dropout=0.5))
  model.add(Dense(100,activation='relu'))
  model.add(Dense(100,activation='relu'))
  model.add(Dense(5,activation='softmax'))
  model.compile(loss='categorical_crossentropy',optimizer='rmsprop',metrics=['accuracy'])

  return model

from sklearn.preprocessing import LabelEncoder
encoder = LabelEncoder()
labels = encoder.fit_transform(df['sentiment'])
labels = to_categorical(labels)

"""### Evaluating neural network using three-fold cross-validation"""

from sklearn.model_selection import cross_val_score
from keras.wrappers.scikit_learn import KerasClassifier


neural_network = KerasClassifier(build_fn=create_nn, 
                                 epochs=20,  
                                 verbose=0)

cross_val_score(neural_network,data, labels, cv=3)