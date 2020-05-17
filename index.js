const express = require('express');
const http = require("http");
const fetch = require("fetch").fetchUrl;
const mongoose = require('mongoose');
const bodyParser = require('body-parser');
const request = require('request');


var history = require('./schema/history');
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

app.post('/history',  (req,res) => {
    try {
                history.find().lean()
            .then(history_list => {
                console.log(JSON.stringify(history_list))

                // temp = JSON.stringify(history_list)

                // res.send(history);

                // console.log(history)
                
                // let history_list =  JSON.stringify(history)
                // let history_list = JSON.parse(history.toString())

                // history_list = JSON.stringify(history);
                res.render('history',{
                    history :  history_list
                });
                
               
               
            }).catch(err => {
                res.status(500).send({
                    message: err.message || "Some error occurred while retrieving notes."
                });
            });
            
            // history.find().lean().then(history => {
            //     console.log(JSON.stringify(history));
            // }
        
    } catch (error) {
        console.log(error);
    }
});

app.post('/submitMovieName',  (req,res) => {
   console.log(req.body.movieName);
   console.log(req.body.Comedy);
   console.log(req.body.Musical);

    let filter = [req.body.Comedy,req.body.Musical,req.body.Romance,req.body.Thriller,req.body.SciFi,req.body.Mystery,req.body.Crime,req.body.Action,req.body.Horror,req.body.Fantasy,req.body.Documentary,req.body.War,req.body.Animation,req.body.Children,req.body.Adventure];
    
    let filter_string = ""
    console.log(filter.length)

    for(let i=0;i<filter.length;i++){
        if(filter[i] === undefined){

        }else{
            filter_string += filter[i]+","
        }
    }

    console.log("filter string is: ", filter_string)


   fetch("http://predictor:5000/predict?movieName="+req.body.movieName+"&filter_list="+filter_string+"" , function(error, meta, body){
        //  fetch("http://127.0.0.1:5000/predict?movieName="+req.body.movieName+"&filter_list="+filter_string+"" , function(error, meta, body){
        try {
            console.error("ERROR in request: ", error);
                console.log(body.toString());
                let movieNames = JSON.parse(body.toString())

                res.render('home',{
                    movieList : movieNames
                });

                const newItem = new history({
                    //   name: "ketan"
                        name: req.body.movieName,
                        recommendation: body.toString()
                    });
                  
                    newItem.save().then();

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