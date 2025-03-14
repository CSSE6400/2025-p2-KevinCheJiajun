from flask import Blueprint, jsonify, request
from todo.models import db
from todo.models.todo import Todo
from datetime import datetime, timedelta
 
api = Blueprint('api', __name__, url_prefix='/api/v1') 

# define the command that approve
allowed_fields = {"title", "description", "completed", "deadline_at"}

TEST_ITEM = {
    "id": 1,
    "title": "Watch CSSE6400 Lecture",
    "description": "Watch the CSSE6400 lecture on ECHO360 for week 1",
    "completed": True,
    "deadline_at": "2023-02-27T00:00:00",
    "created_at": "2023-02-20T00:00:00",
    "updated_at": "2023-02-20T00:00:00"
}
 
@api.route('/health') 
def health():
    """Return a status of 'ok' if the server is running and listening to request"""
    return jsonify({"status": "ok"})


@api.route('/todos', methods=['GET'])
def get_todos():
    """Return the list of todo items, optionally filtering by completed status"""
    query = Todo.query

    # completed filter
    completed_filter = request.args.get('completed')
    if completed_filter is not None:
        if completed_filter.lower() == 'true':
            query = query.filter_by(completed=True)
        elif completed_filter.lower() == 'false':
            query = query.filter_by(completed=False)

    # window filter
    window_filter = request.args.get('window')
    if window_filter is not None:
        try:
            days = int(window_filter)
            if days > 0:
                window_end_date = datetime.utcnow() + timedelta(days=days)
                query = query.filter(Todo.deadline_at <= window_end_date)
        except ValueError:
            return jsonify({"error": "Invalid window value"}), 400

    todos = query.all()
    return jsonify([todo.to_dict() for todo in todos])


@api.route('/todos/<int:todo_id>', methods=['GET'])
def get_todo(todo_id):
    """Return the details of a todo item"""
    todo = Todo.query.get(todo_id)
    if todo is None:
        return jsonify({'error': 'Todo not found'}), 404
    return jsonify(todo.to_dict())

@api.route('/todos', methods=['POST'])
def create_todo():
    """Create a new todo item and return the created item"""
    # get JSON request
    todo_data = request.json
    
    # check is title exit.
    if "title" not in todo_data or not todo_data["title"].strip():
        return jsonify({"error": "Title is required"}), 400

    # check is the command alolowed
    extra_fields = set(todo_data.keys()) - allowed_fields
    if extra_fields:
        return jsonify({"error": f"Invalid fields: {', '.join(extra_fields)}"}), 400
    
    todo = Todo(
        title=request.json.get('title'),
        description=request.json.get('description'),
        completed=request.json.get('completed', False),
    )
    if 'deadline_at' in request.json:
        todo.deadline_at = datetime.fromisoformat(request.json.get('deadline_at'))
    
    #Adds anew record tothedatabaseor willupdatean existing record.
    db.session.add(todo)
    #Commits thechangestothe database.
    #This mustbecalled for thechangesto besaved.
    db.session.commit()
    return jsonify(todo.to_dict()), 201

@api.route('/todos/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id):
    todo = Todo.query.get(todo_id)
    if todo is None:
        return jsonify({'error': 'Todo not found'}), 404
    
    # get JSON data
    todo_data = request.json
    
    # check is the command alolowed
    extra_fields = set(todo_data.keys()) - allowed_fields
    if extra_fields:
        return jsonify({"error": f"Invalid fields: {', '.join(extra_fields)}"}), 400
    
    # check and block the id changing
    if "id" in todo_data and todo_data["id"] != todo_id:
        return jsonify({"error": "Modifying ID is not allowed"}), 400

    todo.title = request.json.get('title', todo.title)
    todo.description = request.json.get('description', todo.description)
    todo.completed = request.json.get('completed', todo.completed)
    todo.deadline_at = request.json.get('deadline_at', todo.deadline_at)
    
    db.session.commit()
    return jsonify(todo.to_dict())


@api.route('/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    todo = Todo.query.get(todo_id)
    if todo is None:
        return jsonify({}), 200

    db.session.delete(todo)
    db.session.commit()
    return jsonify(todo.to_dict()), 200

 
