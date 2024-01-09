from flask import Flask, render_template, request, redirect, session, flash
import pymongo
from passlib.hash import pbkdf2_sha256
from bson.objectid import ObjectId
import os
connectionstring = os.environ.get('MONGO_URI')
cluster = pymongo.MongoClient(connectionstring)
database = cluster['onestopshop']
accounts = database['accounts']
products = database['products']

app = Flask(__name__)
if os.environ.get('COMPUTER_NAME') != 'heroku':
    f = open('secret_key.txt')
    key = f.read().strip()
    f.close()
else:
    key = os.environ.get('SECRET_KEY')
app.secret_key = key

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        shops = []
        allaccounts = accounts.find()
        for i in allaccounts:
            shops.append(i)
        productstoshow = []
        allproducts = products.find()
        for i in allproducts:
            productstoshow.append(i)
        return render_template('index.html', allshops=shops, products=productstoshow)
    elif request.method == 'POST':
        shopname = request.form['shopname']
        name = request.form['ownername']
        email = request.form['email']
        password = request.form['password']
        hash_password = pbkdf2_sha256.hash(password)
        record = {'shopname':shopname, 'name':name, 'email':email, 'password':hash_password}
        accounts.insert_one(record)
        return redirect('/')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = accounts.find_one({'email':email})
        if user == None:
            flash('Account not found', 'danger')
            return redirect('/login')
        if pbkdf2_sha256.verify(password, user['password']):
            session['email'] = email
            session['shopname'] = user['shopname']
            return redirect('/shop_home')
        else:
            flash('Incorrect password', 'danger')
            return redirect('/login')


@app.route('/shop_home', methods=['GET', 'POST'])
def shop_home():
    if 'email' not in session:
        return redirect('/login')
    if request.method == 'GET':
        return render_template('shop_home.html')
    elif request.method == 'POST':
        name = request.form['productname']
        desc = request.form['desc']
        price = request.form['price']
        quantity = request.form['quantity']
        image_url = request.form['image']
        shop = session['shopname']
        record = {'name':name, 'description':desc, 'price':price, 'quantity':quantity, 'shop':shop, 'image_url':image_url}
        products.insert_one(record)
        flash('Successfully added', 'success')
        return redirect('/shop_home')

@app.route('/logout')
def logout():
    flash('Successfully logged out', 'success')
    del session['email']
    return redirect('/login')

@app.route('/shop')
def shop():
    shopid = request.args.get('shopid')
    shopdetails = accounts.find_one({'_id':ObjectId(shopid)})
    shopname = shopdetails['shopname']
    items = products.find({'shop':shopname})
    allitems = []
    for i in items:
        allitems.append(i)
    return render_template('shop.html', shopname=shopname, allitems=allitems)

@app.route('/addtocart', methods=['POST', 'GET'])
def addtocart():
    prodid = request.args.get('id')
    if 'cart' in session:
        currentcart = session['cart']            
        currentcart.append(prodid)
        session['cart'] = currentcart
    else:
        session['cart'] = [prodid]
    if request.args.get('from') == 'index':
        return redirect('/')
    elif request.args.get('from') == 'shop':
        return redirect('/shop')
    else:
        return redirect('/')

@app.route('/cart', methods=['GET'])
def cart():
    if 'cart' not in session:
        return 'nothing in cart'
    cart = session['cart']
    allitems = []
    cartitems = {}
    for item in cart:
        if item not in cartitems:
            cartitems[item] = 1
        else:
            cartitems[item] += 1
    grandtotal = 0
    for item in cartitems:
        prod = products.find_one({'_id':ObjectId(item)})
        prod['quantity'] = cartitems[item]
        prod['allprice'] = int(prod['price']) * cartitems[item]
        grandtotal += prod['allprice']
        allitems.append(prod)
    return render_template('cart.html', allitems=allitems, grandtotal=grandtotal)
