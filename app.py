#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors
import os
import time
import hashlib

SALT = 'cs3083'

#Initialize the app from Flask
app = Flask(__name__)

IMAGES_DIR = os.path.join(os.getcwd(), "images")

#Configure MySQL
conn = pymysql.connect(host='localhost',
                       port = 8889,
                       user='root',
                       password='root',
                       db='Finstagram',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

#Define a route to hello function
@app.route('/')
def hello():
    return render_template('index.html')

#Define route for login
@app.route('/login')
def login():
    return render_template('login.html')

#Define route for register
@app.route('/register')
def register():
    return render_template('register.html')

#Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    #grabs information from the forms
    username = request.form['username']
    password = request.form['password'] + SALT
    hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()

    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM Person WHERE username = %s and password = %s'
    cursor.execute(query, (username, hashed_password))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    cursor.close()
    error = None
    if(data):
        #creates a session for the the user
        #session is a built in
        session['username'] = username
        return redirect(url_for('home'))
    else:
        #returns an error message to the html page
        error = 'Invalid login or username'
        return render_template('login.html', error=error)

#Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    #grabs information from the forms
    username = request.form['username']
    password = request.form['password'] + SALT
    hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
    firstname = request.form['firstname']
    lastname = request.form['lastname']
    bio = request.form['bio']

    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM Person WHERE username = %s'
    cursor.execute(query, (username))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    error = None
    if(data):
        #If the previous query returns data, then user exists
        error = "This user already exists"
        return render_template('register.html', error = error)
    else:
        ins = 'INSERT INTO Person VALUES(%s, %s, %s, %s, %s)'
        cursor.execute(ins, (username, hashed_password, firstname, lastname, bio))
        conn.commit()
        cursor.close()
        return render_template('index.html')


@app.route('/home')
def home():
    #if login passed successfully, open homepage
    user = session['username']
    return render_template('home.html', username=user)


@app.route('/upload_photo', methods=['GET'])
def upload_photo():
    return render_template("uploadphotos.html")

# **FEATURE 3**
#route to upload image
#this function uploads an image
@app.route("/uploadImage", methods=["POST"])
def upload_image():
    if request.files:
        image_file = request.files.get("imageToUpload", "")
        image_name = image_file.filename
        filepath = os.path.join(IMAGES_DIR, image_name)
        if request.form:
            requestData = request.form
            caption = requestData["caption"]
            #needs to be changed after adding follow requests
            allFollowers = 1
            if requestData.getlist('allFollowers') != []:
                allFollowers = 1
            image_file.save(filepath)
            query1 = "INSERT INTO Photo (postingdate, filepath, caption, photoPoster, allFollowers) VALUES (%s, %s, %s, %s, %s)"
            query2 = "SELECT photoID FROM Photo WHERE filepath = %s AND postingdate = %s"
            with conn.cursor() as cursor:
                cursor.execute(query1, (time.strftime('%Y-%m-%d %H:%M:%S'), image_name, caption, session["username"], allFollowers))
                cursor.execute(query2, (image_name, time.strftime('%Y-%m-%d %H:%M:%S')))
                data = cursor.fetchall()
                conn.commit()
            message = "Image has been successfully uploaded."
            #this takes you to another page to tag users in the photo
            return render_template("tag.html", photo = data, message=message)
    else:
        message = "Failed to upload image."
        #else it just returns a error messgae
        return render_template("uploadphotos.html", message=message)

@app.route("/tag/<photoID>", methods=["GET", "POST"])
def tag(photoID):
    cursor = conn.cursor() 
    query = "INSERT INTO Tagged(username, photoID, tagstatus) VALUES(%s, %s, %s)"
    #add a check to see if username is valid and if the tag has been accepted
    username_str = request.form['username']
    username_lst = username_str.split(",")
    for username in username_lst:
        cursor.execute(query,(username, photoID, 1))
    conn.commit()
    cursor.close()
    return home()
    
# **FEATURE 1**
@app.route("/images", methods=["GET", "POST"])
def images():
    #for part 4, add group and follower checks
    cursor = conn.cursor()
    query = "SELECT photoID, photoPoster FROM Photo ORDER BY postingdate DESC"
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    return render_template("viewimages.html", photos=data)

# **FEATURE 2**
@app.route("/images/<photoID>", methods=["GET", "POST"])
def image(photoID):
    
    cursor = conn.cursor()
    query = "SELECT * FROM (Photo as photo) JOIN (Person as person) WHERE photo.photoID = %s AND photo.photoPoster = person.username"
    cursor.execute(query, photoID)
    data = cursor.fetchall()
    cursor.close()
    
    
    #retrieves all the usernames and ratings of the image
    cursor = conn.cursor()
    query = "SELECT * FROM Likes WHERE photoID = %s"
    cursor.execute(query, photoID)
    like = cursor.fetchall()
    
    #retrieves all the usernames, first names, and last names of people tagged in the photo
    cursor = conn.cursor()
    query = "SELECT Tagged.username, Person.firstName, Person.lastName FROM Tagged NATURAL JOIN Person WHERE photoID = %s  AND Tagged.tagstatus = 1"
    cursor.execute(query, photoID)
    tag = cursor.fetchall()
    
    return render_template("image.html", photo=data, likes = like, tags = tag)



#extra feature 4: like and rate (Simone Brown smb866)
@app.route("/likeandrate/<photoID>", methods=["GET", "POST"])
def likeandrate(photoID):
    
    username = session['username']
    cursor = conn.cursor();
    rating = request.form['rating']
    query = "INSERT INTO Likes (username, photoID, liketime, rating) VALUES(%s, %s, %s, %s)"
    cursor.execute(query, (username, photoID, time.strftime('%Y-%m-%d %H:%M:%S'), rating))
    conn.commit()
    cursor.close()
    return redirect(url_for("images"))

#extra feature 2: search by username (Divya Madala dm3980)
@app.route("/username", methods=["GET", "POST"])
def username():
    return render_template("findUsername.html")

#extra feature 2: search by username (Divya Madala dm3980)
@app.route("/findUsername", methods=["GET", "POST"])
def findUsername():
    poster = request.form['username']
    cursor = conn.cursor()
    query = "SELECT * FROM Photo WHERE photoPoster = %s"
    cursor.execute(query, poster)
    data = cursor.fetchall()
    cursor.close()
    if (data):
        return render_template("postByUsername.html", photos = data)
    else:
        return render_template("findUsername.html", message = "couldn't find username")
    

@app.route("/f", methods=["GET", "POST"])
def follow():
    return render_template("follow.html")

#to follow a user
@app.route("/follow", methods=["GET", "POST"])
def updateFollowTable():
    username_followed = request.form["username"]
    username_follower = session["username"]
    cursor = conn.cursor()
    
    query1 = "SELECT username_followed FROM Follow WHERE username_follower = %s"
    cursor.execute(query1, username_follower)
    data = cursor.fetchall()
    
    #this if statement checks if the user is following anyone
    if(data):
        #this for loop goes over the rows returned by query
        for dict in data:
            username = dict["username_followed"]
            # this checks if the user is already following the user
            if(username == username_followed):
                return render_template("follow.html", message="You are already following this user")

    # if the user hasn't followed then this code will execute
    query2 = "INSERT INTO Follow (username_followed, username_follower, followstatus) VALUES(%s, %s, %s)"
    cursor.execute(query2, (username_followed, username_follower, 0))
    conn.commit()
    cursor.close()
    return render_template("follow.html", message = "You have requested to follow " + username_followed + "\n")

#view all of the people you are following
@app.route("/following", methods=["GET", "POST"])
def following():
    my_username = session["username"]
    cursor = conn.cursor()
    query = "SELECT username_followed FROM Follow WHERE username_follower = %s AND followstatus = 1"
    cursor.execute(query, my_username)
    data = cursor.fetchall()
    cursor.close()
    return render_template("following.html", follow=data)

#Extra feature 3: unfollow (Simone Brown smb866)
# When you unfollow a user, the row in the Follow table that represented you following that user will be deleted. I can't just get set to 0 because that is how we track unaccepted follow requests. We also decided that when you unfollow a user, you don't want them tagged in any of your posts anymore. To do this, we update the Tagged table to change the tagstatus from 1 to 0 for any of your posts that the user you're unfollowing is tagged in. To know which tagged photo you posted, we have to join Tagged with Photo on the photoID. Then we know which photos you posted that the user is tagged in.
@app.route("/unfollow/<username>", methods=["GET", "POST"])
def unfollow(username):
    my_username = session["username"]
    cursor = conn.cursor()
    query = "DELETE FROM Follow WHERE username_followed = %s AND username_follower = %s"
    cursor.execute(query, (username, my_username))
    query2 = "UPDATE Tagged JOIN Photo ON Tagged.photoID = Photo.photoID SET tagstatus = 0 WHERE photoPoster = %s AND username = %s"
    cursor.execute(query2, (my_username, username))
    data = cursor.fetchall()
    print(data)
    conn.commit()
    cursor.close()
    return redirect("/following")

#manage follows
@app.route("/follow_requests", methods=["GET", "POST"])
def followRequests():
    my_username = session["username"]
    cursor = conn.cursor()
    query = "SELECT username_follower FROM Follow WHERE username_followed = %s AND followstatus = 0"
    cursor.execute(query, my_username)
    data = cursor.fetchall()
    cursor.close()
    return render_template("followRequests.html", follow = data)

@app.route("/follow_request_action/<username>/<status>", methods=["GET", "POST"])
def followRequestAction(username, status):
    my_username = session["username"]
    cursor = conn.cursor()
    if(status == "accept"):
        query = "UPDATE Follow SET followstatus = 1 WHERE username_followed = %s AND username_follower = %s"
    else:
        query = "DELETE FROM Follow WHERE username_followed = %s AND username_follower = %s"
    cursor.execute(query, (my_username, username))
    conn.commit()
    cursor.close()
    return redirect("/home")

#extra feature 1: search by tag (Divya Madala dm3980)
@app.route("/tagged", methods=["GET", "POST"])
def tagged():
    return render_template("findTag.html")

#extra feature 1: search by tag (Divya Madala dm3980)
@app.route("/findTag", methods=["GET", "POST"])
def findTag():
    tagged = request.form['username']
    cursor = conn.cursor()
    query = "SELECT photoID FROM Tagged WHERE username = %s  AND tagstatus = 1"
    cursor.execute(query, tagged)
    data = cursor.fetchall()
    cursor.close()
    if (data):
        return render_template("postByTag.html", photos = data)
    else:
        return render_template("findTag.html", message = "couldn't find username")
    

#log out of the session
@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')
        
app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)
