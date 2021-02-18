import flask
from flask import request, jsonify
import json
app = flask.Flask(__name__)
import string

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

from ast import literal_eval
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.stem.snowball import SnowballStemmer

from surprise import Reader, Dataset, SVD
from surprise.model_selection import cross_validate

import warnings; warnings.simplefilter('ignore')

credits = pd.read_csv('./input_data/movie_dataset/credits.csv')
keywords = pd.read_csv('./input_data/movie_dataset/keywords.csv')
links_small = pd.read_csv('./input_data/movie_dataset/links_small.csv')
md = pd.read_csv('./input_data/movie_dataset/movies_metadata.csv')
ratings = pd.read_csv('./input_data/movie_dataset/ratings_small.csv')

reader = Reader()
data = Dataset.load_from_df(ratings[['userId', 'movieId', 'rating']], reader)

svd = SVD()
cross_validate(svd, data, measures=['RMSE', 'MAE'], cv=5, verbose=False)

trainset = data.build_full_trainset()
svd.fit(trainset)

ratings[ratings['userId'] == 1]

def convert_int(x):
    try:
        return int(x)
    except:
        return np.nan

md['genres'] = md['genres'].fillna('[]').apply(literal_eval)
md['genres'] = md['genres'].apply(lambda x: [i['name'] for i in x] if isinstance(x, list) else [])

md['year'] = pd.to_datetime(md['release_date'], errors='coerce').apply(lambda x: str(x).split('-')[0] if x != np.nan else np.nan)
md['id'] = md['id'].apply(convert_int)
md = md.drop([19730, 29503, 35587])
md['id'] = md['id'].astype('int')
keywords['id'] = keywords['id'].astype('int')
credits['id'] = credits['id'].astype('int')
md['id'] = md['id'].astype('int')
md = md.merge(credits, on='id')
md = md.merge(keywords, on='id')
smd = md[md['id'].isin(links_small['tmdbId'])]

smd['cast'] = smd['cast'].apply(literal_eval)
smd['crew'] = smd['crew'].apply(literal_eval)
smd['keywords'] = smd['keywords'].apply(literal_eval)
smd['cast_size'] = smd['cast'].apply(lambda x: len(x))
smd['crew_size'] = smd['crew'].apply(lambda x: len(x))

def get_director(x):
    for i in x:
        if i['job'] == 'Director':
            return i['name']
    return np.nan

smd['director'] = smd['crew'].apply(get_director)
smd['director_not_soup'] = smd['director']
smd['director'] = smd['director'].astype('str').apply(lambda x: str.lower(x.replace(" ", "")))
smd['director'] = smd['director'].apply(lambda x: [x,x, x])

smd['cast'] = smd['cast'].apply(lambda x: [i['name'] for i in x] if isinstance(x, list) else [])
smd['cast'] = smd['cast'].apply(lambda x: x[:3] if len(x) >=3 else x)
smd['cast_not_soup'] = smd['cast']
smd['cast'] = smd['cast'].apply(lambda x: [str.lower(i.replace(" ", "")) for i in x])

smd['keywords'] = smd['keywords'].apply(lambda x: [i['name'] for i in x] if isinstance(x, list) else [])

###################################################
smd = smd[0:4850]
###################################################

s = smd.apply(lambda x: pd.Series(x['keywords']),axis=1).stack().reset_index(level=1, drop=True)
s.name = 'keyword'
s = s.value_counts()

s = s[s > 1]

stemmer = SnowballStemmer('english')

def filter_keywords(x):
    words = []
    for i in x:
        if i in s:
            words.append(i)
    return words

smd['keywords'] = smd['keywords'].apply(filter_keywords)
smd['keywords'] = smd['keywords'].apply(lambda x: [stemmer.stem(i) for i in x])
smd['keywords'] = smd['keywords'].apply(lambda x: [str.lower(i.replace(" ", "")) for i in x])
smd['soup'] = smd['keywords'] + smd['cast'] + smd['director'] + smd['genres']
smd['soup'] = smd['soup'].apply(lambda x: ' '.join(x))

count = CountVectorizer(analyzer='word',ngram_range=(1, 2),min_df=0, stop_words='english')
count_matrix = count.fit_transform(smd['soup'])
count_matrix = count_matrix
cosine_sim = cosine_similarity(count_matrix, count_matrix)
print(cosine_sim.nbytes/1000000,"Mib")

smd = smd.reset_index()
indices = pd.Series(smd.index, index=smd['title'])

id_map = pd.read_csv('./input_data/movie_dataset/links_small.csv')[['movieId', 'tmdbId']]
id_map['tmdbId'] = id_map['tmdbId'].apply(convert_int)
id_map.columns = ['movieId', 'id']
id_map = id_map.merge(smd[['title', 'id']], on='id').set_index('title')

indices_map = id_map.set_index('id')

@app.route('/', methods=['GET'])
def home():
    return '<h1>HOME</h1>'

@app.route('/data',methods=['GET'])
def get_recommendations():
    userId = int(request.args['u'])
    arg = request.args['a']
    arg = arg.title()
    type = request.args['t']
    
    if (type == "title"):
        try:
            idx = indices[arg]
            tmdbId = id_map.loc[arg]['id']
        except KeyError:
            # print("Please try another one....")
            # return "KE: Data not available for that movie, try another"
            error_data = '[{"status": 501,"problem": "no data avail"}]'
            return jsonify(error_data)
        movie_id = id_map.loc[arg]['movieId']

        sim_arg = list(enumerate(cosine_sim[int(idx)]))
        sim_arg = sorted(sim_arg, key=lambda x: x[1], reverse=True)
        sim_arg = sim_arg[1:26]
        sim_arg = [i[0] for i in sim_arg]

    elif (type == "genre"):
        try:
            sim_arg = smd[smd["genres"].apply(lambda x: arg in x)]
            sim_arg = sim_arg.sort_values(by='vote_average', ascending=False)
            sim_arg = sim_arg.index[:25]
        except KeyError:
            error_data = '[{"status": 501,"problem": "no data avail"}]'
            return jsonify(error_data)

    elif (type == "cast"):
        try:
            sim_arg = smd[smd["cast_not_soup"].apply(lambda x: arg in x)].index[:]
        except KeyError:
            error_data = '[{"status": 501,"problem": "no data avail"}]'
            return jsonify(error_data)
    elif (type == "director"):
        try:
            sim_arg = smd[smd["director_not_soup"] == arg].index[:]
        except KeyError:
            error_data = '[{"status": 501,"problem": "no data avail"}]'
            return jsonify(error_data)
###############################################
    movie_indices = [i for i in sim_arg]
    movies = smd.iloc[movie_indices][['title', 'id', 'genres', 'cast_not_soup', 'director_not_soup']]
    # movies = smd.iloc[movie_indices][['title', 'id','genres','cast_not_soup','director_not_soup','vote_average']]


    try:
        # use of svd to predict estimated rating(from previous section)
        movies['est'] = movies['id'].apply(lambda x: svd.predict(userId, indices_map.loc[x]['movieId']).est)
    except TypeError:
        # print("Please try another one....")
        # return "TE: Data not available for that movie, try another"
        error_data = '[{"status": 502,"problem": "Unknown prob"}]'
        return jsonify(error_data)

    # sorting using estimated rating
    movies = movies.sort_values('est', ascending=False)
    movies.rename(columns={"cast_not_soup": "cast","director_not_soup": "director"}, inplace = True)
    # movies.rename(columns={"cast_not_soup": "cast","director_not_soup": "director","vote_average":"Vote Average"}, inplace = True)


    
    result = movies.head(15)
    result = result.to_json(orient='records')
    # print(result)
    return jsonify(result)

# print(get_recommendations())
# x=0
# while(True):
#     title = input("Enter a title: ")
#     print(get_recommendations(title))
#     x = int(input("Do u wnt to cnt? 1 for cnt, else 0....."))
#     if x==0:
#         break

