FROM mongo

COPY ./movies.json ./movies.json
COPY ./ratings.json ./ratings.json
COPY ./data.json ./data.json

CMD mongoimport --host mongo-app --db movies_database --collection movies --type json --file /movies.json --jsonArray && mongoimport --host mongo-app --db movies_database --collection ratings --type json --file /ratings.json --jsonArray && mongoimport --host mongo-app --db movies_database --collection links --type json --file /data.json --jsonArray


