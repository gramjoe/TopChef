#!/usr/bin/env python
"""
Very very very basic application
"""
from .config import SOURCE_REPOSITORY, VERSION, AUTHOR, AUTHOR_EMAIL
from flask import Flask, jsonify, request, url_for
from .database import SESSION_FACTORY, METADATA, ENGINE
from .models import User, Job, UnableToFindItemError
from .config import ROOT_EMAIL, ROOT_USERNAME
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)


@app.route('/')
def hello_world():
    return jsonify({
        'meta': {
            'source_repository': SOURCE_REPOSITORY,
            'version': VERSION,
            'author': AUTHOR,
            'email': AUTHOR_EMAIL
        }
    })


@app.route('/users', methods=["GET"])
def get_users():
    session = SESSION_FACTORY()

    user_list = session.query(User).all()

    return jsonify({
        'data': {
            'users': User.UserSchema(many=True).dump(user_list).data
        }
    })


@app.route('/users', methods=["POST"])
def make_user():
    session = SESSION_FACTORY()

    if not request.json:
        response = jsonify({'errors': 'The supplied data is not JSON'})
        response.status_code = 400
        return response

    user, errors = User.UserSchema().load(request.json)

    if errors:
        response = jsonify({'errors': errors})
        response.status_code = 400
        return response

    try:
        session.add(user)
        session.commit()
    except IntegrityError:
        session.rollback()
        response = jsonify(
            {
                'errors':
                    'A user with username %s already exists' % user.username
            }
        )
        response.status_code = 400
        return response

    response = jsonify(
        {'data': 'user %s successfully created' % user.username}
    )
    response.headers['Location'] = url_for(
        'get_user_info', username=user.username, _external=True
    )
    response.status_code = 201
    return response


@app.route('/users/<username>', methods=["GET"])
def get_user_info(username):
    session = SESSION_FACTORY()
    user = session.query(User).filter_by(username=username).first()

    if user is None:
        response = jsonify({
            'errors': 'Unable to find user with username %s' % username
        })
        response.status_code = 404
        return response

    response = jsonify({
        'data': User.DetailedUserSchema().dump(user).data
    })
    return response


@app.route('/users/<username>/jobs', methods=["GET"])
def get_jobs_for_user(username):
    session = SESSION_FACTORY()

    try:
        user = User.from_session(username, session)
    except UnableToFindItemError:
        response = jsonify({
            'errors': 'Unable to find user with username %s' % username
        })
        response.status_code = 404
        return response

    response = jsonify({'data': Job.JobSchema(many=True).dump(user.jobs).data})
    response.status_code = 200
    return response


@app.route('/users/<username>/jobs', methods=["POST"])
def make_job_for_user(username):
    session = SESSION_FACTORY()

    try:
        user = User.from_session(username, session)
    except User.UnableToFindItemError:
        response = jsonify({
            'errors': 'Unable to find user with username %s' % username
        })
        response.status_code = 404
        return response

    if not request.json:
        response = jsonify({'errors': 'The request is not JSON'})
        response.status_code = 400
        return response

    job, errors = Job.JobSchema().load(request.json)

    if errors:
        response = jsonify({'errors': errors})
        response.status_code = 400
        return response

    session.add(job)

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        response = jsonify(
            {'errors': 'A job with ID %d already exists' % job.id}
        )
        response.status_code = 400
        return response

    response = jsonify({'data': 'job %d created successfully' % job.id})
    response.headers['Location'] = url_for(
        'get_job_details', username=user.username, job_id=job.id,
        _external=True
    )
    response.status_code = 201
    return response


@app.route('/jobs', methods=["GET"])
def get_all_jobs():
    session = SESSION_FACTORY()
    job_list = session.query(Job).all()
    response = jsonify({'data': Job.JobSchema(many=True).dump(job_list).data})
    response.status_code = 200
    return response


@app.route('/jobs/<int:job_id>', methods=["GET"])
def get_job_details(job_id):
    session = SESSION_FACTORY()
    job = session.query(Job).filter_by(id=job_id).first()
    if not job:
        response = jsonify(
            {'errors': 'A job with id=%d could not be found' % job_id}
        )
        response.status_code = 404
        return response

    return jsonify({'data': job.DetailedJobSchema().dump(job).data})


@app.route('/users/<username>/jobs/<int:job_id>', methods=["GET"])
def get_job_details_for_user(username, job_id):
    session = SESSION_FACTORY()
    user = User.from_session(username, session)

    job = session.query(Job).filter_by(id=job_id, job_owner=user).first()

    if not job:
        response = jsonify(
            {'errors': 'A job with id=%d could not be found' % job_id}
        )
        response.status_code = 404
        return response

    response = jsonify({'data': job.DetailedJobSchema().dumps(job)})

    return response


@app.route('/users/<username>/jobs/next', methods=["GET"])
def get_next_job(username):
    return "The Job user with username %s will be redirected to the next job" % username


@app.route('/users/<username>/jobs/<int:job_id>', methods=["PATCH"])
def do_stuff_to_job(username, job_id):
    return "Post results, change state, for user %s and job %d" % (username, job_id)


@app.route('/programs', methods=["GET"])
def get_programs():
    return 'Here is a list of NMR programs'


@app.route('/programs/<int:program_id>', methods=["GET"])
def get_program_by_id(program_id):
    return 'Here is business logic to retrieve a program file with id %d' % program_id


def create_root_user():
    session = SESSION_FACTORY()
    root_user = User(ROOT_USERNAME, ROOT_EMAIL)

    if session.query(User).filter_by(username=ROOT_USERNAME).first() is None:
        session.add(root_user)

    session.commit()


def create_metadata():
    METADATA.create_all(bind=ENGINE)