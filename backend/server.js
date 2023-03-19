let express = require('express');
let app = express();
let path = require('path');
let logger = require('morgan');
const dotenv = require('dotenv');
const fs = require('fs');

const http = require('http');
let server = http.createServer(app);
app.set("view engine", "ejs");

app.use(express.static(path.join(__dirname, 'public')));

app.use(function (req, res, next) {
    if (req.url.startsWith("css")) {
        req.url = "public/" + req.url;
    }

    if (req.url.startsWith("img")) {
        req.url = "public/" + req.url;
    }

    next();
});
// Set up Global configuration access
dotenv.config();
let port = 3356;

server.listen(port, () => {
    console.log(`Success! Your application is running on port ${port}.`);
});

dotenv.config();
app.use(logger('dev'));
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: false }));
app.use(express.static(path.join(__dirname, 'public')));

app.get("/", function (req, res,next) {
    try {
        let image = fs.readFileSync("image.png", 'base64');
        res.render("index", { image: image });
    } catch (err) {
        res.status(500).send({ success: false, err: err });
        next(err);
    }
});

app.post("/image", async (req, res, next) => {
    try {
        let base64image = req.body.image;
        
        fs.writeFile("image.png", base64image, 'base64', function(err) {});
        res.send({ success: true });
    } catch (err) {
        res.status(500).send({ success: false, err: err });
        next(err);
    }
});