Project Repository Link
https://github.com/zacharylevaton/CS467_CrowdSourcedTravelPlanner

Website Link
http://flip2.engr.oregonstate.edu:38017/

Note: You may need to be connected to the OSU VPN to access the site.

Local Hosting Instructions
If you would like to host the site locally, please enter the following commands at the command line from the main folder:

“pip install -r requirements.txt” to install all necessary Python packages
“python app.py” or “python3 app.py” to start the server

The default port number used by the local server is 5000.  To access the site using the default port please visit http://localhost:5000/.

You can specify a different port number in the “app.py” file by editing the “app.run” call (e.g. app.run(host="localhost", port=8000, debug=True)).  You may then browse the website at http://localhost:<port number>.
