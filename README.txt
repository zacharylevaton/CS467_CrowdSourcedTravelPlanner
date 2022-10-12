Implemented Login and Register pages using a temporary SQLite database.  I basically followed the process shown 
in videos 4-6 of the Flask Tutorial (https://www.youtube.com/playlist?list=PL-osiE80TeTs4UjLw5MM6OjgkjFeUxCYH).

To start the server, use the command "python3 app.py" in the main directory.

If you would like to test it out, you can start by creating a new account on the "Register" page.  The current 
input validation checks include username length, correct email address structure, and making sure the entered
passwords are the same.  A valid username is between 2 and 20 characters.  The page also prevents users from
registering if the entered username or email address are already found in the database.  Successful registration
redirects the user to the "Log In" page.

To test the "Log In" page, try entering credentials for both registered and unregistered users.  Different alert 
messages should be shown.  Users are redirected to the Landing page after successfully logging in, and some navbar
links change as well.  I still have to work on the "Remember Me" function.

NOTE: According to Video 4 of the Flask Tutorial (https://www.youtube.com/watch?v=cYWiDiIUxQc), the "site.db" 
database file should be created in the main "CrowdSourcedTravelPlanner" folder.  I use a virtual Python 
environment, and it creates the file in the "CrowdSourcedTravelPlanner/instance" folder.  I included the 
"site.db" file in both locations, as I'm not sure which one will be used when testing on other machines.