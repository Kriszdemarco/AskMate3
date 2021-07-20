from typing import List, Dict
from flask.globals import session
import psycopg2
import psycopg2.extras
from psycopg2.extras import RealDictConnection, RealDictCursor 
import database_common
import os
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__)) # point to the root folder
UPLOADED_FOLDER = os.path.join(PROJECT_ROOT, 'static', 'images')


def user_datas():
    """Read the nessecery information from the user_file to
    connect to the database, such as dbname, username, password
    """
    with open('user.txt') as file:
        data = file.read()
        data = data.split(',')
        return data


def fetch_database(query, tuple_parameters=None):
    """Connects to the database to retrieve data, then
    returns it.
    """
    try:
        data = user_datas()
        connect_str = "dbname='askmate' user='postgres' host='localhost' password={0}".format(data[0])
        conn = psycopg2.connect(connect_str)
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute(query, tuple_parameters)
        rows = cursor.fetchall()
        return rows

    except psycopg2.DatabaseError as exception:
        print(exception)

    finally:
        if conn:
            conn.close()


def modify_database(query, tuple_parameters=None):
    """Connects to the database then modifies the data
    without fetching anything.
    """
    try:
        data = user_datas()
        connect_str = "dbname='askmate' user='postgres' host='localhost' password={0}".format(data[0])
        conn = psycopg2.connect(connect_str)
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute(query, tuple_parameters)

    except psycopg2.DatabaseError as exception:
        print(exception)


def check_users():
    connect_str = "dbname='askmate' user='postgres' host='localhost' password='derank123'"
    connection = psycopg2.connect(connect_str)
    cursor = connection.cursor()
    cursor.execute(""" SELECT username FROM users ORDER BY id DESC;""")
    db_users = cursor.fetchall()
    users = []

    for i in range(len(db_users)):
        person = db_users[i][0]
        users.append(person)

    connection.commit()
    cursor.close()
    connection.close()

    return users


def check_for_email():
    connect_str = "dbname='askmate' user='postgres' host='localhost' password='derank123'"
    connection = psycopg2.connect(connect_str)
    cursor = connection.cursor()
    cursor.execute(""" SELECT email FROM users ORDER BY id DESC;""")
    db_users = cursor.fetchall()
    email = []

    for i in range(len(db_users)):
        person = db_users[i][0]
        email.append(person)

    connection.commit()
    cursor.close()
    connection.close()

    return email



def add_new_answer(submission_time, vote_number, question_id, message, image, user_name):
    """Adds a new answer to a question"""
    modify_database("""INSERT INTO answer(submission_time, vote_number, question_id, message, image, user_name) VALUES
                    (%s, %s, %s, %s, %s, %s); """, (submission_time, vote_number, question_id, message, image, user_name))

def add_new_user(username:str, password:str,email:str, regdate:str):
    """Adding new users to our AskMate"""
    modify_database("""INSERT INTO users(username,password,email,regdate) VALUES (%s,%s,%s,%s); """, (username, password,email,regdate))

def edit_questions(image, submission_time, message, question_id, title):
    """Modify the questions"""
    modify_database("""UPDATE question SET image=%s, submission_time=%s, message=%s, title=%s WHERE id = %s; """, (image, submission_time, message, title, question_id))

def edit_profile_page(username:str, password:str, email:str, image:str, id:str)->list:
    modify_database("""UPDATE users SET username=%s, password=%s, email=%s, image=%s WHERE id= %s""",(username, password, email, image, id))

def answer_to_answer(answer_id,question_id, message, submission_time, user_name):
    """Write new answer to an existing answer"""
    modify_database("""INSERT INTO comment(answer_id, question_id, message, submission_time, user_name) VALUES (%s, %s, %s, %s, %s); """, (answer_id, question_id ,message,submission_time, user_name))


@database_common.connection_handler
def show_answer(cursor: RealDictCursor, question_id: str) -> list:
    query = f"""
        SELECT *
        FROM question
        WHERE id = '{question_id}'
    """
    cursor.execute(query)
    return cursor.fetchall()


@database_common.connection_handler
def show_usersname(cursor: RealDictCursor) -> list:
    query = f"""
        SELECT username
        FROM users
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    for row in rows:
        return row["username"]



@database_common.connection_handler
def mark_accepted(cursor: RealDictCursor, isAccepted: bool, question_id: str):
    if isAccepted:
        query = f"""
            UPDATE answer
            SET accepted = true
            WHERE question_id = '{question_id}'
        """
    else:
        query = f"""
            UPDATE answer
            SET accepted = false
            WHERE question_id = '{question_id}'
        """
    cursor.execute(query)

@database_common.connection_handler
def nested_comments(cursor: RealDictCursor, question_id: str) -> list:
    query = f"""
        SELECT *
        FROM comment
        WHERE question_id = '{question_id}'
    """
    cursor.execute(query)
    return cursor.fetchall()

@database_common.connection_handler
def show_message_only(cursor: RealDictCursor, question_id: str) -> list:
    query = f"""
        SELECT message
        FROM question
        WHERE id = '{question_id}'
    """
    cursor.execute(query)
    return cursor.fetchall()

@database_common.connection_handler
def show_answer_mgs_only(cursor: RealDictCursor, question_id: str, answer_id: str) -> list:
    query = f"""
        SELECT message
        FROM answer
        WHERE id = '{answer_id}' 
        AND question_id = '{question_id}'
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    for row in rows:
        return row["message"]

@database_common.connection_handler
def show_id(cursor: RealDictCursor) -> list:
    lst = []
    query = f"""
        SELECT id
        FROM question
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    for row in rows:
        lst.append(row["id"])
    return lst


@database_common.connection_handler
def show_title_only(cursor:RealDictCursor, question_id:str) -> list:
    query = f"""
        SELECT title
        FROM question
        WHERE id = '{question_id}'
    """
    cursor.execute(query)
    return cursor.fetchall()

@database_common.connection_handler
def show_primary_key(cursor:RealDictCursor):
    query = """
    SELECT NEXTVAL('question_id_seq'::regclass);
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    for row in rows:
        return row["nextval"]

@database_common.connection_handler
def list_users(cursor:RealDictCursor) -> list:
    query = f"""
        SELECT *
        FROM users
    """
    cursor.execute(query)
    return cursor.fetchall()


@database_common.connection_handler
def users_id(cursor:RealDictCursor) -> list:
    query = f"""
        SELECT id
        FROM users
        WHERE username = '{session["username"]}'
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    for row in rows:
        return row["id"]

@database_common.connection_handler
def find_user(cursor:RealDictCursor, name:list) -> list:
    query = f"""
        SELECT *
        FROM users
        WHERE username LIKE '{name}'
    """
    cursor.execute(query)
    return cursor.fetchall()


@database_common.connection_handler
def get_user_by_email_and_pass(cursor:RealDictCursor, email, password) -> list:

    #query = """ SELECT * FROM "users"
    #            WHERE email=%(email)s"""
    #params = {'email': email}

    query = f"""
            SELECT *
            FROM users
            WHERE email = '{email}' AND password = '{password}'
    """
    cursor.execute(query)
    return cursor.fetchall()



@database_common.connection_handler
def list_tags(cursor:RealDictCursor) -> list:
    query = f"""
        SELECT name, id
        FROM tag
    """
    cursor.execute(query)
    return cursor.fetchall()

@database_common.connection_handler
def load_tags(cursor: RealDictCursor, question_id: int) -> list:
    query = f"""
        SELECT *
        FROM tag
        JOIN question_tag ON (tag.id = question_tag.tag_id)
        WHERE question_id = '{question_id}'
    """
        
    cursor.execute(query)
    return cursor.fetchall()

@database_common.connection_handler
def search_tag(cursor: RealDictCursor, tag: int) -> list:
    query = f"""
        SELECT *
        FROM question
        JOIN question_tag ON (question.id = question_tag.question_id)
        WHERE question_tag.tag_id = '{tag}'
    """
    cursor.execute(query)
    return cursor.fetchall()

@database_common.connection_handler
def search_title(cursor: RealDictCursor, search: str) -> list:
    query = f"""
        SELECT *
        FROM question
        WHERE title ~* '(^|[^\w]){search}([^\w]|$)'
    """
    cursor.execute(query)
    return cursor.fetchall()

@database_common.connection_handler
def search_title_tag(cursor: RealDictCursor, search: str, tag: int) -> list:
    query = f"""
        SELECT *
        FROM question
        JOIN question_tag ON (question.id = question_tag.question_id)
        WHERE title ~* '(^|[^\w]){search}([^\w]|$)' AND question_tag.tag_id = '{tag}'
    """
    cursor.execute(query)
    return cursor.fetchall()

@database_common.connection_handler
def list_all_tags(cursor: RealDictCursor, question_id: list) -> list:
    lst = []
    for i in question_id:
        query = f"""
            SELECT *
            FROM tag
            JOIN question_tag ON (tag.id = question_tag.tag_id)
            WHERE question_id = '{i}'
        """
            
        cursor.execute(query)
        lst.append(cursor.fetchall())
    return lst

@database_common.connection_handler
def show_answers(cursor: RealDictCursor, order: str=None) -> list:
    if order == 'most-view':
        query = f"""
            SELECT *
            FROM question
            ORDER BY view_number DESC
        """
    elif order == 'least-view':
        query = f"""
            SELECT *
            FROM question
            ORDER BY view_number ASC
        """
    elif order == 'least-upvote':
        query = f"""
            SELECT *
            FROM question
            ORDER BY vote_number ASC
        """
    elif order == 'most-upvote':
        query = f"""
            SELECT *
            FROM question
            ORDER BY vote_number DESC
        """
    elif order == 'most-recent':
        query = f"""
            SELECT *
            FROM question
            ORDER BY submission_time DESC
        """
    else:
        query = f"""
            SELECT *
            FROM question
            ORDER BY title DESC
        """
    cursor.execute(query)
    return cursor.fetchall()

@database_common.connection_handler
def show_comment(cursor: RealDictCursor, question_id: int) -> list:
    query = f"""
        SELECT *
        FROM answer
        WHERE question_id = '{question_id}'
        ORDER BY vote_number DESC
    """
    cursor.execute(query)
    return cursor.fetchall()

@database_common.connection_handler
def increment_questions(cursor: RealDictCursor, username: str, isDelete: bool):
    if isDelete:
        query = f"""
            UPDATE users 
            SET question = question - 1
            WHERE username = '{username}'
            """
    else:
        query = f"""
            UPDATE users 
            SET question = question + 1
            WHERE username = '{username}'
        """

    cursor.execute(query)

@database_common.connection_handler
def increment_answers(cursor: RealDictCursor, username: str, isDelete: bool):
    if isDelete:
        query = f"""
            UPDATE users 
            SET answers = answers - 1
            WHERE username = '{username}'
            """
    else:
        query = f"""
            UPDATE users 
            SET answers = answers + 1
            WHERE username = '{username}'
        """

    cursor.execute(query)

@database_common.connection_handler
def increment_comments(cursor: RealDictCursor, username: str, isDelete: bool):
    if isDelete:
        query = f"""
            UPDATE users 
            SET comments = comments - 1
            WHERE username = '{username}'
            """
    else:
        query = f"""
            UPDATE users 
            SET comments = comments + 1
            WHERE username = '{username}'
        """

    cursor.execute(query)

@database_common.connection_handler
def update_view(cursor: RealDictCursor, question_id: str) -> list:
    query = f"""
        UPDATE question
        SET view_number = view_number + 1
        WHERE id = {question_id}
    """
    cursor.execute(query)

@database_common.connection_handler
def update_question_vote(cursor: RealDictCursor, question_id: str, vote: bool) -> list:
    if vote == True:
        query = f"""
            UPDATE question
            SET vote_number = vote_number + 1
            WHERE id = {question_id}
        """
        cursor.execute(query)
    else:
        query = f"""
            UPDATE question
            SET vote_number = vote_number - 1
            WHERE id = {question_id}
        """
        cursor.execute(query)


@database_common.connection_handler
def update_rep_vote(cursor: RealDictCursor, question_id: str, vote: bool) -> list:
    if vote == True:
        query = f"""
            UPDATE question
            SET rep = rep + 1
            WHERE id = {question_id}
        """
        cursor.execute(query)
    else:
        query = f"""
            UPDATE question
            SET rep = rep - 1
            WHERE id = {question_id}
        """
        cursor.execute(query)



@database_common.connection_handler
def delete_question(cursor: RealDictCursor, question_id: str) -> list:
    query = f"""
        DELETE FROM question
        WHERE id = {question_id};

        DELETE FROM answer
        WHERE id = {question_id};
    """
    cursor.execute(query)

@database_common.connection_handler
def delete_comment(cursor: RealDictCursor, comment_id: str) -> list:
    query = f"""
        DELETE FROM answer
        WHERE id = {comment_id};
    """
    cursor.execute(query)

@database_common.connection_handler
def update_comment_vote(cursor: RealDictCursor, question_id: str, vote: bool) -> list:
    if vote == True:
        query = f"""
            UPDATE answer
            SET vote_number = vote_number + 1
            WHERE id = {question_id}
        """
        cursor.execute(query)
    else:
        query = f"""
            UPDATE answer
            SET vote_number = vote_number - 1
            WHERE id = {question_id}
        """
        cursor.execute(query)


@database_common.connection_handler
def reputation_incr(cursor: RealDictCursor, user_id:str):
        query = f"""
            UPDATE users
            SET rep = rep + 1
            WHERE id = {user_id}
        """
        cursor.execute(query)


@database_common.connection_handler
def user_ids(cursor: RealDictCursor, username:str):
        query = f"""
            SELECT id
            FROM users
            WHERE username = '{username}' 
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        for row in rows:
            return row["id"]
          




#DATA_HEADER = ['id', 'submission_time', 'vote_number', 'question_id', 'message', 'image']
#DATA_HEADER_2 = ['id', 'submission_time', 'view_number', 'vote_number', 'title', 'message', 'image']

def path_to_image(file_name):
    return "/static/images/"(file_name)