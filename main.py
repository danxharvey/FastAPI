# Import libraries
from fastapi import FastAPI, HTTPException
from uuid import UUID
from models import User, Gender, Role, UpdateUser
from typing import List


# Set up user list instead of active db with 2 default users
db: List[User] = [
                User(id = 'd41f332e-6ca4-4ab5-9727-3a7b706331b8', # uuid4()
                    first_name = 'Joe',
                    last_name = 'Bloggs',
                    gender = Gender.male,
                    roles = [Role.user]
                ),
                User(id = '0a14c21c-819f-4fb7-b5ab-18e1a0e70cef', # uuid4()
                    first_name = 'Henrietta',
                    last_name = 'de Glanville',
                    gender = Gender.female,
                    roles = [Role.admin, Role.power]
                )]

# Instantiate API
app = FastAPI()

# Define root endpoint
@app.get('/')
async def root():
    return {'FastAPI Root': 'Neuron 5 Dev Environment', 'Documentation': 'http://localhost:8000/docs'}

# Get user list
@app.get('/api/v1/users')
async def get_users():
    return db

# Add new user (test with VS ThunderClient extension or swagger)
@app.post('/api/v1/users')
async def add_user(user: User):
    db.append(user)
    return {'User added successfully with id': user.id}

# Delete a user and raise error if not found
@app.delete('/api/v1/users/{user_id}')
async def delete_user(user_id: UUID):
    for user in db:
        if user.id == user_id:
            db.remove(user) 
            return f'User successfully deleted'
    raise HTTPException(
            status_code = 404,
            detail = f'User with id: {user_id} does not exist')

# Update a user
@app.put('/api/v1/users/{user_id}')
async def update_user(user_update: UpdateUser, user_id: UUID):
    for user in db:
        if user.id == user_id:
            if user_update.first_name is not None:
                user.first_name = user_update.first_name
            if user_update.last_name is not None:
                user.last_name = user_update.last_name
            if user_update.gender is not None:
                user.gender = user_update.gender
            if user_update.first_name is not None:
                user.roles = user_update.roles
            return f'User successfully updated'
    raise HTTPException(
            status_code = 404,
            detail = f'User with id: {user_id} does not exist')