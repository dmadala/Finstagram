#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect, send_file
import pymysql.cursors
import os
import time


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
    password = request.form['password']

    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM Person WHERE username = %s and password = %s'
    cursor.execute(query, (username, password))
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
    password = request.form['password']
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
        cursor.execute(ins, (username, password, firstname, lastname, bio))
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
    query = "INSERT INTO Tagged(username, photoID) VALUES(%s, %s)"
    #add a check to see if username is valid and if the tag has been accepted
    username = request.form['username']
    cursor.execute(query,(username, photoID))
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
    
    #retrieves all the usernames tagged in the photo
    cursor = conn.cursor()
    query = "SELECT * FROM Tagged WHERE photoID = %s"
    cursor.execute(query, photoID)
    tag = cursor.fetchall()
    
    return render_template("image.html", photo=data, likes = like, tags = tag)




@app.route("/likeandrate/<photoID>", methods=["GET", "POST"])
def likeandrate(photoID):
    username = session['username']
    cursor = conn.cursor();
    rating = request.form['rating']
    query = 'INSERT INTO Likes (username, photoID, rating) VALUES(%s, %s, %s)'
    cursor.execute(query, (username, photoID, rating))
    conn.commit()
    cursor.close()
    
    return render_template("home.html")
    #return redirect(url_for('/images'))
    

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
