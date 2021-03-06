from flask import Flask
from flask import request,jsonify
import os
import time
import gc
import argparse
import pickle
# data science imports
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.neighbors import NearestNeighbors
import imdb
import pymongo
# utils import
from fuzzywuzzy import fuzz



class KnnRecommender:
    def __init__(self, path_movies, path_ratings):
        self.path_movies = path_movies
        self.path_ratings = path_ratings
        self.movie_rating_thres = 0
        self.user_rating_thres = 0
        self.model = NearestNeighbors()

    def set_filter_params(self, movie_rating_thres, user_rating_thres):
        self.movie_rating_thres = movie_rating_thres
        self.user_rating_thres = user_rating_thres

    def _prep_data(self):
        myclient = pymongo.MongoClient("mongodb://mongo-app:27017/")
        # myclient = pymongo.MongoClient("mongodb://192.168.99.100:27017/")

        mydb = myclient["movies_database"]
        movies = mydb["movies"]
        ratings = mydb["ratings"]
        links = mydb["links"]

        myquery = { "movieId": { "$exists":True }}



        movie_cursor = movies.find(myquery)
        # print ("total docs in collection:", movies.count_documents( {} ))
        # print ("total docs returned by find():", len( list(movie_cursor) ))
        # for x in movie_cursor:
        #     print(x.title)
        movies_df = pd.DataFrame(list(movie_cursor))

        # print("printing movies_df",movies_df)
        del movies_df['_id']
        del movies_df['genres']
        movies_df["movieId"] = pd.to_numeric(movies_df["movieId"])
        # print("printing movies_df",movies_df)


        ratings_cursor = ratings.find(myquery)
        # print ("total docs in collection:", ratings.count_documents( {} ))
        # print ("total docs returned by find():", len( list(ratings_cursor) ))

        # ratings_df = pd.DataFrame(list(ratings_cursor))
        # print(list(ratings_cursor))
        # print("printing curser")
        # for x in ratings_cursor:
        #     print(x)
        ratings_df = pd.DataFrame(list(ratings_cursor))
        # print("printing ratings_df",ratings_df)
        del ratings_df['_id']
        del ratings_df['timestamp']
        ratings_df["userId"] = pd.to_numeric(ratings_df["userId"])
        ratings_df["movieId"] = pd.to_numeric(ratings_df["movieId"])
        ratings_df["rating"] = pd.to_numeric(ratings_df["rating"])
        # print(ratings_df)
        # read data
        # df_movies = pd.read_csv(os.path.join(self.path_movies),usecols=['movieId', 'title'],dtype={'movieId': 'int32', 'title': 'str'})

        # print(df_movies.dtypes)

        # #reading csv and passing data to use the coulmn
        # df_ratings = pd.read_csv(os.path.join(self.path_ratings),usecols=['userId', 'movieId', 'rating'],dtype={'userId': 'int32', 'movieId': 'int32', 'rating': 'float32'})

        # print(ratings_df)
        # filter data
        df_movies_cnt = pd.DataFrame(ratings_df.groupby('movieId').size(),columns=['count'])
        # df_movies_cnt = pd.DataFrame(df_ratings.groupby('movieId').size(),columns=['count'])


        print(df_movies_cnt)
        temp = df_movies_cnt.sort_values(by ='count',ascending=False )
        temp.to_csv('Top_Rated_movies.csv')
        

        
        popular_movies = list(set(df_movies_cnt.query('count >= @self.movie_rating_thres').index))  # noqa
        movies_filter = ratings_df.movieId.isin(popular_movies).values

        df_users_cnt = pd.DataFrame(ratings_df.groupby('userId').size(),columns=['count'])

        active_users = list(set(df_users_cnt.query('count >= @self.user_rating_thres').index))  # noqa
        users_filter = ratings_df.userId.isin(active_users).values

        df_ratings_filtered = ratings_df[movies_filter & users_filter]

        # pivot and create movie-user matrix
        movie_user_mat = df_ratings_filtered.pivot(index='movieId', columns='userId', values='rating').fillna(0)
        # create mapper from movie title to index
        hashmap = { movie: i for i, movie in
            enumerate(list(movies_df.set_index('movieId').loc[movie_user_mat.index].title)) # noqa
        }
        # transform matrix to scipy sparse matrix
        movie_user_mat_sparse = csr_matrix(movie_user_mat.values)

        # clean up
        # del df_movies, df_movies_cnt, df_users_cnt
        # del df_ratings, df_ratings_filtered, movie_user_mat
        # gc.collect()
        # print("Movie user sparse matrix \n",movie_user_mat_sparse)
        # print("Hashmap \n",hashmap)
        return movie_user_mat_sparse, hashmap

    def set_model_params(self, n_neighbors, algorithm, metric, n_jobs=None):
        if n_jobs and (n_jobs > 1 or n_jobs == -1):
            os.environ['JOBLIB_TEMP_FOLDER'] = '/tmp'
        self.model.set_params(**{
            'n_neighbors': n_neighbors,
            'algorithm': algorithm,
            'metric': metric,
            'n_jobs': n_jobs})

    def _fuzzy_matching(self, hashmap, fav_movie):
        match_tuple = []
        # get match
        for title, idx in hashmap.items():
            ratio = fuzz.ratio(title.lower(), fav_movie.lower())
            if ratio >= 60:
                match_tuple.append((title, idx, ratio))
        # sort
        match_tuple = sorted(match_tuple, key=lambda x: x[2])[::-1]
        if not match_tuple:
            print('Oops! No match is found')
        else:
            print('Found possible matches in our database: '
                  '{0}\n'.format([x[0] for x in match_tuple]))
            return match_tuple[0][1]

    def _inference(self, model, data, hashmap,
                   fav_movie, n_recommendations):
        # fit
        if(os.path.exists('knnpickle_file')):
            print("Model exist")
            model = pickle.load(open('knnpickle_file', 'rb'))
        else:
            print("Model doesn't exist")
            model.fit(data)
            knnPickle = open('knnpickle_file', 'wb') 
            # source, destination 
            pickle.dump(model, knnPickle)   
        
       
        # get input movie index
        print('You have input movie:', fav_movie)
        idx = self._fuzzy_matching(hashmap, fav_movie)
        # print(data[idx])
        # inference
        print('Recommendation system start to make inference')
        print('......\n')
        t0 = time.time()
        distances, indices = model.kneighbors(data[idx],n_neighbors=n_recommendations+1)
        # get list of raw idx of recommendations
        raw_recommends = \
            sorted(
                list(
                    zip(
                        indices.squeeze().tolist(),
                        distances.squeeze().tolist()
                    )
                ),
                key=lambda x: x[1]
            )[:0:-1]
        print('It took my system {:.2f}s to make inference \n\
              '.format(time.time() - t0))
        # return recommendation (movieId, distance)
        return raw_recommends

    def make_recommendations(self, fav_movie, n_recommendations):
        # get data
        movie_user_mat_sparse, hashmap = self._prep_data()
        # get recommendations
        raw_recommends = self._inference(self.model, movie_user_mat_sparse, hashmap,fav_movie, n_recommendations)
        # print(raw_recommends)
        # print results
        reverse_hashmap = {v: k for k, v in hashmap.items()}
        # print('Recommendations for {}:'.format(fav_movie))
        tempList = []
        for i, (idx, dist) in enumerate(raw_recommends):
            tempList.append(reverse_hashmap[idx])
            # print('{0}: {1}, with distance '
            #       'of {2}'.format(i+1, reverse_hashmap[idx], dist))

        return tempList

app = Flask(__name__)

@app.route('/')
def hello_world():
    return "hello world how are you hey"

@app.route('/predict',methods=['GET', 'POST'])
def predict():
    try:
        myclient = pymongo.MongoClient("mongodb://mongo-app:27017/")
        # myclient = pymongo.MongoClient("mongodb://192.168.99.100:27017/")
        mydb = myclient["movies_database"]
        links = mydb["links"]

        filter_list = []
        movieName = request.args.get('movieName')
        filter_list = request.args.get('filter_list').split(",")
        print(movieName)
        print(filter_list)
        # pred_count = 5
        recomendations_list = []
        finalList = []
        recommender = KnnRecommender(
            os.path.join("ml-latest-small", "movies.csv"),
            os.path.join("ml-latest-small", "ratings.csv"))
        recommender.set_filter_params(50,50)
        recommender.set_model_params(20, 'brute', 'cosine', -1)
                # make recommendations
        recomendations_list = recommender.make_recommendations(movieName, 449) #The Dark Knight Rises

        finalString = []
        filter_recommendations = []
        if(len(filter_list) == 0):

            print("filter list is empty")
            finalString = []
            for i in recomendations_list[-5:]:
                tempQuery = { "name": i}
                links_cursor = links.find(tempQuery)
                print ("total docs in collection:", links.count_documents( {} ))
                print ("total docs returned by find():", len( list(links_cursor) ))
                print(links_cursor)
                x = links.find_one(tempQuery)
                print(x['name'])
                tempQuery = { "name": i}
                links_cursor = links.find(myquery)
                imageUrls = {}
                # access = imdb.IMDb()
                # search_results = access.search_movie(i)
                # movieID = search_results[0].movieID
                # movie = access.get_movie(movieID)

                # print (movie['title'], movie['year'])
                # print (movie['cover url'])
                imageUrls["name"] = i

                # for x in links_cursor:
                #     print(x.name)
                # for x in links_cursor:
                #     imageUrls["url"] = x['url']
                imageUrls["url"] = x['url']
                print(x['url'])
                # imageUrls["url"] = (movie['cover url'])
                finalString.append(imageUrls)
        else:
            print("filter list is not empty")
            for i in recomendations_list:
                # filter_list = ['Action','Comedy']
                filter_list = request.args.get('filter_list').split(",")
                filter_list.append(i)
                with open('ml-latest-small/movies.csv',encoding='UTF-8') as f:
                    for line in f:
                        # print(line)
                        if all(x in line for x in filter_list):
                            filter_recommendations.append(i)
            print("filtered recommendation")
            # print(filter_recommendations)
            print(filter_recommendations[-5:])
            for i in filter_recommendations[-5:]:
                try:
                    tempQuery = { "name": i}
                    links_cursor = links.find(tempQuery)
                    print ("total docs in collection:", links.count_documents( {} ))
                    print ("total docs returned by find():", len( list(links_cursor) ))
                    print(links_cursor)
                    x = links.find_one(tempQuery)
                    print(x['name'])

                    imageUrls = {}
                    # access = imdb.IMDb()
                    # search_results = access.search_movie(i)
                    # movieID = search_results[0].movieID
                    # movie = access.get_movie(movieID)

                    # print (movie['title'], movie['year'])
                    # print (movie['cover url'])
                    for x in links_cursor:
                        print(x.name)
                    print("debug")
                    imageUrls["name"] = i
                    # imageUrls["url"] = (movie['cover url'])
                    # print(links_cursor.url)
                    # for x in links_cursor:
                    #     imageUrls["url"] = x['url']
                    imageUrls["url"] = x['url']
                    print(x['url'])
                    # imageUrls["url"] = (movie['cover url'])
                    finalString.append(imageUrls)
                except Exception as e:
                    print(e)

        # filter_list = ['Action','Comedy']
        # with open('ml-latest-small/movies.csv',encoding='UTF-8') as f:
        #     for line in f:
        #         # if 'Action' in line:
        #         #     print(line)
        #         if all(x in line for x in filter_list):
        #             print(line)
        # for i in range(pred_count):
        # finalList.append(recomendations_list[i])

        # return jsonify(dict)
        return jsonify(finalString)
        
    except Exception as e:
        print(e)
        return "No Match found"

if __name__ == '__main__':
    app.run(host='0.0.0.0')