from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from pymongo import MongoClient
import jwt
from dotenv import load_dotenv
import os

server = Flask(__name__)
CORS(server,resources={r"*": {"origins": "*"}})

load_dotenv()

uri = "mongodb+srv://admin:admin@cluster0.cbp8dvl.mongodb.net/?retryWrites=true&w=majority"

client = MongoClient(uri)
db = client.rewaCharts
collection = db.users

try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)


forAccessToken = 'https://www.linkedin.com/oauth/v2/accessToken'

ForEmail = 'https://api.linkedin.com/v2/clientAwareMemberHandles?q=members&projection=(elements*(primary,type,handle~))'

ForUserProfile = 'https://api.linkedin.com/v2/me?projection=(id,localizedFirstName,localizedLastName,profilePicture(displayImage~digitalmediaAsset:playableStreams))'

def getAccessToken(code):
    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')
    Headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    parameters = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': 'http://localhost:5173/',
        'client_id':client_id,
        'client_secret':client_secret
    }
    token = requests.post(forAccessToken,data=parameters,headers=Headers)
    return token.json().get('access_token')

def getUserProfile(accessToken):
    Headers = {
        "Authorization": "Bearer " + accessToken
    }
    response = requests.get(ForUserProfile,headers=Headers).json()
    profile = {
        "id":response.get('id'),
        "firstName":response.get('localizedFirstName'),
        "lastName":response.get('localizedLastName'),
        "profilePicture":response.get('profilePicture').get('displayImage~').get('elements')[0].get('identifiers')[0].get('identifier')
    }
    return profile

def getUserEmail(accessToken):
    Headers = {
        "Authorization": "Bearer " + accessToken
    }
    email = requests.get(ForEmail,headers=Headers).json().get('elements')[0].get('handle~').get('emailAddress')
    return email

def addDataInDB(userProfile,userEmail,jwtToken):
    data = {
        "userid":userProfile.get('id'),
        "firstName":userProfile.get('firstName'),
        "lastName":userProfile.get('lastName'),
        "email":userEmail,
        "jwtToken":jwtToken
    }
    if collection.find_one({"userid":userProfile.get('id')}):
        print("User already exists")
    else:
        collection.insert_one(data)

@server.route('/auth', methods=['GET'])
def auth():
    code = request.args.get('code')
    accessToken = getAccessToken(code)
    userProfile = getUserProfile(accessToken)
    userEmail = getUserEmail(accessToken)
    jwtToken = jwt.encode({
        'userid':userProfile.get('id'),
        'firstName':userProfile.get('firstName'),
        'lastName':userProfile.get('lastName'),
        'email':userEmail,
    },'secret',algorithm='HS256')
    addDataInDB(userProfile,userEmail,jwtToken)
    return jsonify({'token':jwtToken})

if __name__ == '__main__':
    server.run(debug=True)