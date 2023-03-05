let express = require('express');
let app = express();
let path = require('path');
let logger = require('morgan');
const dotenv = require('dotenv');
let indexRouter = require('./routes/index');
let imageRouter = require('./routes/image');
const socketIO = require('socket.io');
const http = require('http');
let server = http.createServer(app);
let io = socketIO(server);
// Set up Global configuration access
dotenv.config();
let port = 3356;

server.listen(port, () => {
    console.log(`Success! Your application is running on port ${port}.`);
});
io.on( 'connection', async function( socket ) {
    console.log( 'a user has connected!' );
    try {
        let data = {}
        socket.emit('update-event', data);
    } catch (err) {
        console.log(err);
    }
    socket.on( 'disconnect', function() {
    console.log( 'user disconnected' );
    });
});

app.use((req, res, next) => {
    req.io = io;
    return next();
  });

dotenv.config();
app.use(logger('dev'));
app.use(express.json({limit:'50mb'}));
app.use(express.urlencoded({ extended: false }));
app.use(express.static(path.join(__dirname, 'public')));

app.use('/', indexRouter);
app.use('/image', imageRouter);