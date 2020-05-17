const express = require('express');
const mongoose = require('mongoose');

mongoose.connect('mongodb://mongo-app:27017', { useNewUrlParser: true})
.then(() => console.log('Mongodb connected'))
.catch(err => console.log(err));

const history = mongoose.Schema({
    name:String,
    recommendation:String,
});

module.exports = mongoose.model('history',history);