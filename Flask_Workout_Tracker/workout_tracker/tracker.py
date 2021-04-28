from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from workout_tracker.auth import login_required
from workout_tracker.db import get_db

import random

bp = Blueprint('tracker', __name__)

quotes = ['"Of course it’s hard. It’s supposed to be hard. If it were easy, everybody would do it. Hard is what makes it great."',
           '"No pain, no gain. Shut up and train."',
            '"Your body can stand almost anything. It’s your mind that you have to convince."',
            '"Success isn’t always about greatness. It’s about consistency. Consistent hard work gains success. Greatness will come."']

@bp.route('/')
@login_required
def index():
    db = get_db()
    posts = []
    
    return render_template('tracker/index.html', posts=posts, quote = random.choice(quotes))

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        muscleGroup = request.form['muscle-groups']
        name = request.form['exercise_name']
        sets = request.form['num_of_sets']
        reps = request.form['num_of_reps']
        weight = request.form['amt_weight']
        error = None

        if not muscleGroup:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO post (muscle_group, exercise_name, set_count, reps, amt_weight, author_id)'
                ' VALUES (?, ?, ?, ?, ?, ?)',
                (muscleGroup, name, sets, reps, weight, g.user['id'])
            )
            db.commit()
            return redirect(url_for('tracker.index', posts=[], quote = random.choice(quotes)))

    return render_template('tracker/create.html')

@bp.route('/searchByName', methods=('GET', 'POST'))
@login_required
def searchByName():
    if request.method == 'POST':
        name = request.form['exercise_name']
        error = None

        if error is not None:
            flash(error)
        else:
            db = get_db()
            posts = db.execute(
            'SELECT muscle_group, exercise_name, set_count, reps, amt_weight, created, p.id'
            ' FROM post p JOIN user u ON p.author_id = u.id'
            ' WHERE exercise_name = ? AND u.id = ?'
            'ORDER BY created DESC', (name, g.user['id'])
            ).fetchall()
            return render_template('tracker/index.html', posts=posts, quote = random.choice(quotes))

    return render_template('tracker/searchByName.html')

@bp.route('/searchByMuscleGroup', methods=('GET', 'POST'))
@login_required
def searchByMuscleGroup():
    if request.method == 'POST':
        muscleGroup = request.form['muscle-groups']
        error = None

        if error is not None:
            flash(error)
        else:
            db = get_db()
            posts = db.execute(
            'SELECT muscle_group, exercise_name, set_count, reps, amt_weight, created, p.id'
            ' FROM post p JOIN user u ON p.author_id = u.id'
            ' WHERE muscle_group = ? AND u.id = ?'
            'ORDER BY created DESC', (muscleGroup,  g.user['id'])
            ).fetchall()
            return render_template('tracker/index.html', posts=posts, quote = random.choice(quotes))

    return render_template('tracker/searchByMuscleGroup.html')

def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.id, muscle_group, exercise_name, set_count, reps, amt_weight'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, "Post id {0} doesn't exist.".format(id))

    return post

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        muscleGroup = request.form['muscle-groups']
        name = request.form['exercise_name']
        sets = request.form['num_of_sets']
        reps = request.form['num_of_reps']
        weight = request.form['amt_weight']
        error = None

        if not muscleGroup:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET muscle_group = ?, exercise_name = ?, set_count = ?, reps =?, amt_weight = ?'
                ' WHERE id = ?',
                (muscleGroup, name, sets, reps, weight, id)
            )
            db.commit()
            return redirect(url_for('tracker.index'))

    return render_template('tracker/update.html', post=post)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('tracker.index'))