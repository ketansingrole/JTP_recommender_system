const express = require('express');
const mongoose = require('mongoose');

mongoose.connect('mongodb://mongo-app:27017', { useNewUrlParser: true})
.then(() => console.log('Mongodb connected'))
.catch(err => console.log(err));

const userSchema = mongoose.Schema({
    name:String,
    age:String,
    state:String,
    country:String
});

module.exports = mongoose.model('User',userSchema);