from flask import Flask, request, jsonify, abort
from sqlalchemy.exc import IntegrityError
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

# @TODO uncomment the following line to initialize the database
# !! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
# !! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
# !! Running this function will add one
with app.app_context():
    db_drop_and_create_all()


# ROUTES
# @TODO implement endpoint
#     GET /drinks
#         it should be a public endpoint
#         it should contain only the drink.short() data representation
#     returns status code 200 and json {"success": True, "drinks": drinks}
#         where drinks is the list of drinks
#         or appropriate status code indicating reason for failure
@app.route('/drinks', methods=['GET'])
def get_drinks():
    recs = Drink.query.order_by(Drink.id).all()
    drinks = [drink.short() for drink in recs]

    if len(drinks) == 0:
        abort(404)

    return jsonify({
        'success': True,
        'drinks': drinks
    })


# @TODO implement endpoint
#     GET /drinks-detail
#         it should require the 'get:drinks-detail' permission
#         it should contain the drink.long() data representation
#     returns status code 200 and json {"success": True, "drinks": drinks}
#         where drinks is the list of drinks
#         or appropriate status code indicating reason for failure
@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drinks_detail(payload):
    recs = Drink.query.order_by(Drink.id).all()
    drinks = [drink.long() for drink in recs]

    if len(drinks) == 0:
        abort(404)

    return jsonify({
        'success': True,
        'drinks': drinks
    })


# @TODO implement endpoint
#     POST /drinks
#         it should create a new row in the drinks table
#         it should require the 'post:drinks' permission
#         it should contain the drink.long() data representation
#     returns status code 200 and json {"success": True, "drinks": drink}
#         where drink is an array containing only the newly created drink
#         or appropriate status code indicating reason for failure
@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drink(payload):
    body = request.get_json()
    new_data = {}
    # Check for required fields.
    for field in ['title', 'recipe']:
        new_data[field] = body.get(field)
        if not new_data[field]:
            abort(400, f'Missing required field: {field}')
    # Check for the long format.
    required_recipe_fields = {'name', 'color', 'parts'}
    missing_recipe_fields = required_recipe_fields.difference(new_data['recipe'])
    if missing_recipe_fields:
        abort(400, f'Missing required recipe field(s): {", ".join(missing_recipe_fields)}')
    for k, v in new_data['recipe'].items():
        if not v:
            abort(400, f'Missing required recipe field: {k}')

    try:
        drink = Drink(
            title=new_data['title'],
            recipe=json.dumps([new_data['recipe']])
        )
        drink.insert()
        return jsonify({
            'success': True,
            'drinks': [drink.long()]
        })
    except IntegrityError:
        abort(400, f'Drink may already exist')
    except Exception:
        abort(422)


# @TODO implement endpoint
#     PATCH /drinks/<id>
#         where <id> is the existing model id
#         it should respond with a 404 error if <id> is not found
#         it should update the corresponding row for <id>
#         it should require the 'patch:drinks' permission
#         it should contain the drink.long() data representation
#     returns status code 200 and json {"success": True, "drinks": drink}
#         where drink is an array containing only the updated drink
#         or appropriate status code indicating reason for failure
@app.route('/drinks/<int:drink_id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(payload, drink_id):
    body = request.get_json()

    # Check for valid inputs.
    for field in ['title', 'recipe']:
        if field in body and not body.get(field):
            abort(400, f'A value is required for field: {field}')
    # Check for the long format.
    if 'recipe' in body:
        required_recipe_fields = {'name', 'color', 'parts'}
        missing_recipe_fields = required_recipe_fields.difference(body['recipe'])
        if missing_recipe_fields:
            abort(400, f'Missing required recipe field(s): {", ".join(missing_recipe_fields)}')
        for k, v in body['recipe'].items():
            if not v:
                abort(400, f'Missing required recipe field: {k}')

    try:
        drink = Drink.query.filter(Drink.id == drink_id).one_or_none()

        if drink is None:
            abort(404)

        if 'title' in body:
            drink.title = body['title']

        if 'recipe' in body:
            drink.recipe = json.dumps(body['recipe'])
        drink.update()

        return jsonify({
            'success': True,
            'drinks': [drink.long()]
        })
    except Exception:
        abort(422)


# @TODO implement endpoint
#     DELETE /drinks/<id>
#         where <id> is the existing model id
#         it should respond with a 404 error if <id> is not found
#         it should delete the corresponding row for <id>
#         it should require the 'delete:drinks' permission
#     returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
#         or appropriate status code indicating reason for failure
@app.route('/drinks/<int:drink_id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(payload, drink_id):
    drink = Drink.query.filter(Drink.id == drink_id).one_or_none()

    if drink is None:
        abort(404)

    try:
        drink.delete()
        return jsonify({
            'success': True,
            'delete': drink_id
        })
    except Exception:
        abort(422)


# Error Handling
# Example error handling for unprocessable entity
@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        'success': False,
        'error': 422,
        'message': 'unprocessable'
    }), 422


# @TODO implement error handlers using the @app.errorhandler(error) decorator
#     each error handler should return (with approprate messages):
#              jsonify({
#                     "success": False,
#                     "error": 404,
#                     "message": "resource not found"
#                     }), 404
# @TODO implement error handler for 404
#     error handler should conform to general task above
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 404,
        'message': 'resource not found'
    }), 404


# @TODO implement error handler for AuthError
#     error handler should conform to general task above
@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error': 400,
        'message': error.description or 'bad request'
    }), 400


@app.errorhandler(403)
def forbidden(error):
    return jsonify({
        'success': False,
        'error': 403,
        'message': error.description or 'forbidden'
    }), 403


@app.errorhandler(401)
def unauthorized(error):
    return jsonify({
        'success': False,
        'error': 401,
        'message': error.description or 'unauthorized'
    }), 401


@app.errorhandler(500)
def server_error(error):
    return jsonify({
        'success': False,
        'error': 500,
        'message': 'internal server error'
    }), 500
