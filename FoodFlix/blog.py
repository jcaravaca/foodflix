from flask import (
        Blueprint, flash, g, redirect, render_template, request, url_for, session
    )
from werkzeug.exceptions import abort, BadRequestKeyError

from FoodFlix.auth import login_required
from FoodFlix.db import get_db

bp = Blueprint('blog', __name__)

@bp.route('/', methods=('GET','POST'))
def browse():
    db = get_db()
    recipes = db.execute(
        'SELECT * '
        'FROM recipes '
        'WHERE review_count > "1 reviews" '
        'ORDER BY overall_rating DESC '
    ).fetchall()
    liked_query = db.execute(
        'SELECT liked '
        'FROM user '
    ).fetchone()
    try:
        liked_str = liked_query['liked']
        liked = liked_str.split(',')
    except:
        liked = []
    keywords =[]
    if request.method == 'POST':
        try:
            recipe_id = request.form['recipe_id']
            if str(recipe_id) in liked:
                liked.remove( str(recipe_id) )
            else:
                liked.append( str(recipe_id) )
            db.execute(
                'UPDATE user '
                'SET liked=?',
                (','.join(liked),)
            )
            db.commit()
            return redirect(url_for('blog.browse',_anchor=recipe_id))
        except BadRequestKeyError:
            print('No recipe_id key')
        try:
            keywords = request.form['ingredients'].split(' ')
            query = '''
            SELECT * 
            FROM recipes 
            WHERE review_count > "1 reviews" 
            '''
            query_like = "AND ingredients LIKE '%%%s%%' "
            query += ''.join([query_like%keyword for keyword in keywords])
            query += "ORDER BY overall_rating DESC "
            recipes = db.execute(query).fetchall()
        except BadRequestKeyError:
            print('No Ingredients key')

    return render_template('browse.html', recipes=recipes, liked=liked, keywords=keywords)


@bp.route('/favs', methods=('GET','POST'))
def favs():
    db = get_db()
    liked_query = db.execute(
        'SELECT liked '
        'FROM user '
    ).fetchone()
    try:
        liked_str = liked_query['liked']
        liked = liked_str.split(',')
    except:
        liked = []
    try:
        liked_str = liked_query['liked']
        liked = liked_str.split(',')
    except:
        liked_str = ''
        liked = []
    query = '''SELECT * 
    FROM recipes
    WHERE review_count > "1 reviews"
    AND recipe_id IN (%s)
    ORDER BY overall_rating DESC
    ''' %liked_str
    recipes = db.execute(query).fetchall()
    if request.method == 'POST':
        recipe_id = request.form['recipe_id']
        if str(recipe_id) in liked:
            liked.remove( str(recipe_id) )
        else:
            liked.append( str(recipe_id) )
        db.execute(
            'UPDATE user '
            'SET liked=?',
            (','.join(liked),)
        )
        db.commit()
        return redirect(url_for('blog.favs',_anchor=recipe_id))
    return render_template('browse.html', recipes=recipes, liked=liked)


@bp.route('/profile', methods=('GET', 'POST'))
@login_required
def profile():
    db = get_db()
    if request.method == 'POST':
        db.execute(
            'UPDATE user '
            'SET fullname=?, '
            'gender=?, '
            'weight=?, '
            'height=?, '
            'restrictions=?, '
            'is_config=?',
            (request.form['fullname'],
             request.form['gender'],
             request.form['weight'],
             request.form['height'],
             request.form['restrictions'],
             1)
            )
        db.commit()
        flash('Saved!','success')
        return redirect(url_for('blog.profile'))
    else:
        user_info = db.execute(
            'SELECT * '
            'FROM user '
            'WHERE id = ?',
            (session.get('user_id'),)
        ).fetchone()
        return render_template('profile.html', user=user_info)

@bp.route('/recommender', methods=('GET', 'POST'))
@login_required
def recommender():
    recipes = []
    return render_template("browse.html",recipes=recipes)
    
@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'
            
        if error is not None:
            flash(error,'danger')
        else:
            db = get_db()
            db.execute(
                'INSERT INTO post (title, body, author_id)'
                ' VALUES (?, ?, ?)',
                (title, body, g.user['id'])
            )
            db.commit()
        return redirect(url_for('blog.browse'))

    return render_template('blog/create.html')


def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()
    
    if post is None:
        abort(404, "Post id {0} doesn't exist.".format(id))
        
    if check_author and post['author_id'] != g.user['id']:
        abort(403)
            
    return post


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)
    
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None
        
        if not title:
            error = 'Title is required.'
        
        if error is not None:
            flash(error,'danger')
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ?'
                ' WHERE id = ?',
                (title, body, id)
            )
            db.commit()
        return redirect(url_for('blog.browse'))

    return render_template('blog/update.html', post=post)
    


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.browse'))
