const express = require('express');
const http = require("http");
const fetch = require("fetch").fetchUrl;
const mongoose = require('mongoose');
const bodyParser = require('body-parser');
const request = require('request');


// var User = require('./schema/user');
var exphbs  = require('express-handlebars');



const app = express();

app.engine('handlebars', exphbs());
app.set('view engine', 'handlebars');
app.use(bodyParser.urlencoded({ extended: false }));


app.get('/',(req,res) => {
    // res.send("hello world 3");
    // console.log(User.find({}))
    // res.render('home',{
    //     title: User.find({})
    // });
    res.render('home');
    // User.find()
    // .then(User => res.render('home', { title: User }))
    // .catch(err => res.status(404).json({ msg: 'No items found' }));
});

app.post('/submitMovieName',  (req,res) => {
   console.log(req.body.movieName);
   console.log(req.body.Comedy);
   console.log(req.body.Musical);


   fetch("http://predictor:5000/predict?movieName="+req.body.movieName+"&filter_list=" , function(error, meta, body){
        //  fetch("http://127.0.0.1:5000/predict?movieName="+req.body.movieName+"&filter_list=" , function(error, meta, body){
        try {
            console.error("ERROR in request: ", error);
                console.log(body.toString());
                let movieNames = JSON.parse(body.toString())
                // res.status(200).json({"response": "ok", "data": JSON.parse(body.toString())})
                // web scrapping url example https://www.imdb.com/find?q=Iron+Man
                // let results = [];

                //   async.mapLimit(movieNames, 1, function(movie, callback) {

                //     google.scrape(movie, 1).then((result) => {
                //         console.log("Result: ", result)
                //         callback();
                //     }).catch((error) => {
                //         console.error("Inside ERROR: ", error)
                //         callback();
                //     });

                //   }, function(error, result)  {
                //       console.log(error, result)
                //       if (error) {
                //           console.error("Outside ERROR: ", error)
                //       } else {
                //           console.log(result);
                //       }
                //   })
                    // const results = await google.scrape("Django Unchained", 1);
                    // console.log('results', results);
                  
                //   console

                // for (let i = 0; i < movieNames.length; i++) {
                //     console.log(movieNames[i]);
                //     //Do something
                //    (async () => {
                //     results.push(google.scrape(movieNames[i], 1));
                //     })();
                // }
                // Promise.all(results).then((response)=>{
                //     console.log(response);
                // })
                // console.log('results', results);
                // for await (movie of movieNames) {
                //     (async () => {
                //             const results = await google.scrape("Django Unchained (2012)", 1);
                //             console.log('results', results);
                //             })();
                //   }
                    


                res.render('home',{
                    movieList : movieNames
                });
        } catch (error) {
            console.log(error)
            let movieNames =  [{"name":"This movie is not in database try another movie","url":""}]
                res.render('home',{
                    movieList : movieNames
          })
            
        }

    })
});

app.post('/item/add', (req, res) => {
    const newItem = new User({
    //   name: "ketan"
        name: req.body.name
    });
  
    newItem.save().then(User => res.redirect('/'));
  });

app.listen(8080,()=>{
    console.log('Listening on port 8080');
})