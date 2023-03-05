const express = require('express');
const router = express.Router();
const fs = require('fs');

router.post("/", async (req, res, next) => {
    
    try {
        let base64image = req.body.image;
        base64Data = base64image.replace(/^data:image\/png;base64,/, "");
        fs.writeFile("image.png", base64Data, 'base64', function(err) {});
        req.io.emit('update-event', {image:base64image});
        res.send({ success: true });
    } catch (err) {
        res.status(500).send({ success: false, err: err });
        next(err);
    }
});

module.exports = router;
