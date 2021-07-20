from re import sub
from typing import NamedTuple
from flask import Flask, render_template, redirect, request, url_for, flash, session
from flask.helpers import get_flashed_messages
import database_common
import psycopg2
import psycopg2.extras
from psycopg2.extras import DictConnection, DictCursor, NamedTupleCursor, RealDictCursor
import data_manager
from werkzeug.utils import secure_filename
import os
import datetime
import password_crypt

UPLOAD_FOLDER = 'static/images/'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = "test"

@app.route('/login', methods=['POST'])
def login():
    session.pop('id',None)
    session.pop('username',None)
    session.pop('email',None)
    session.pop("password", None)
    user = data_manager.get_user_by_email_and_pass(request.form['email'],request.form["password"])
    password = ''
    for _ in user:
        password = _["password"]

    if user and password_crypt.verify_password(request.form['password'],password):
        for _ in user:
            session['id'] = _['id']
            session['password'] = _['password']
            session['username'] = _['username']
            session["email"] = _["email"]
        return redirect(url_for("list_the_questions"))
    else:
        flash("Log in failed","red") # somehow this message doesn't even show ://///
        return redirect(request.referrer)

@app.route('/logout', methods=["GET","POST"])
def logout():
    session.pop('id',None)
    session.pop('username',None)
    session.pop('email',None)
    session.pop("password", None)
    flash("You have been successfully logged out!","green") # somehow this message doesn't even show ://///
    return redirect(url_for("list_the_questions"))


@app.route("/", methods=["GET", "POST"])
def list_the_questions():
    today = datetime.datetime.now()
    current_date = today.strftime("%Y-%m-%d")

    emails = data_manager.check_for_email()
    user = data_manager.check_users()
    list_questions = data_manager.show_answers()

    if request.method == "POST":
        username = request.form.get("username") # need to add the HTML side FORM NAME/ID
        password = request.form.get("password")
        email = request.form.get("email")
        regdate = datetime.datetime.today()
        if username in user:
            flash("Username already exist!")
            return redirect("/")
        elif email in emails:
            flash("Email already exist!")
            return redirect("/")
        else:
            flash("Registration completed! You can log in now!")
            data_manager.add_new_user(username, password, email, regdate.strftime("%d-%B-%Y %H:%M:%S"))
            return redirect("/")

    list_id = data_manager.show_id()
    list_tags = data_manager.list_all_tags(list_id)
    all_tag = data_manager.list_tags()

    city = request.args.get('sort-option')
    tags = request.args.get('search-tag')
    search_opt = request.args.get('search')

    if city:
        list_questions = data_manager.show_answers(city)
    elif tags and not search_opt:
        list_questions = data_manager.search_tag(tags)
    elif search_opt and not tags:
        list_questions = data_manager.search_title(search_opt)
    elif tags and search_opt:
        list_questions = data_manager.search_title_tag(search_opt,tags)
    else:
        list_questions = data_manager.show_answers()

    return render_template("index.html" ,list_tags=list_tags , list_questions=list_questions, all_tag=all_tag, session=session, current_date=current_date)


@database_common.connection_handler
def create_question(cursor: RealDictCursor, primary_key:str , title: str, message: str, submission_time: str, vote_number: int, view_number: int, image:str, username:str) -> list:
    cursor.execute("INSERT INTO question (id, title, message, submission_time, vote_number, view_number, image, username) VALUES (%s,%s,%s,%s, %s, %s, %s, %s)", (primary_key, title, message, submission_time, vote_number, view_number, image, username))

@database_common.connection_handler
def add_tag(cursor: RealDictCursor, question_id: str, tag_id: str) -> list:
    cursor.execute("INSERT INTO question_tag (question_id,tag_id) VALUES (%s,%s)", (question_id,tag_id))

@database_common.connection_handler
def update_tag(cursor: RealDictCursor, question_id: str, tag_id: str) -> list:
    cursor.execute("""UPDATE question_tag SET question_id = %s, tag_id = %s WHERE question_id = %s""", (question_id,tag_id,question_id))

@app.route("/users")
def list_users():
    list_questions = data_manager.show_answers()
    list_users = data_manager.list_users()
    return render_template("users.html", list_users=list_users, list_questions=list_questions)

@app.route("/add_questions/", methods=["GET", "POST"])
def add_questions():
    list_tag = data_manager.list_tags()
    prima_key = data_manager.show_primary_key()
    if request.method == "POST":
        tit = request.form.get("title")
        mess = request.form.get("message")
        sub_time = datetime.datetime.now().strftime("%d-%B-%Y %H:%M:%S")
        file_name = "default.png"
        username = session["username"]
        data_manager.increment_questions(username, False)
        uploaded_image = request.files['image']
        if uploaded_image.filename != "":
            uploaded_image.save(os.path.join(app.config['UPLOAD_FOLDER'], uploaded_image.filename))
            file_name = uploaded_image.filename
        tags = request.form["tags"]    
        vot_num = 0
        view_num = 0
        create_question(prima_key , tit, mess, sub_time, vot_num, view_num, file_name, username)
        add_tag(prima_key, tags)

        return redirect("/")
    return render_template("add_questions.html", prima_key=prima_key, list_tag=list_tag)


@app.route("/edit_questions/<question_id>", methods=["GET", "POST"])
def edit_questions(question_id=None):
    list_question = data_manager.show_answer(question_id)
    list_title = data_manager.show_title_only(question_id)
    list_msg = data_manager.show_message_only(question_id)
    list_tags = data_manager.list_tags()

    if request.method == "POST":
        submission_time = request.form["submission_time"]
        message = request.form["message"] 
        title = request.form["title"]
        tag = request.form["tags"]
        uploaded_image = request.files['image']
        file_name = uploaded_image.filename
        if uploaded_image.filename != "":
            uploaded_image.save(os.path.join(app.config['UPLOAD_FOLDER'], uploaded_image.filename))
        data_manager.edit_questions(file_name,submission_time, message, question_id, title)
        update_tag(question_id, tag)
        return redirect("/")
    return render_template('edit_questions.html', question_id=question_id,list_tags=list_tags , list_question=list_question, list_title=list_title, list_msg=list_msg)


@app.route("/edit_profile/", methods=["GET", "POST"])
def edit_profiles():
    list_the_users = data_manager.list_users()
    if request.method == "POST":
        user_id = session["id"]
        username = request.form["username"]
        password = request.form["password"] 
        email = request.form["email"]
        uploaded_image = request.files['image']
        file_name = uploaded_image.filename
        if uploaded_image.filename != "":
            uploaded_image.save(os.path.join(app.config['UPLOAD_FOLDER'], uploaded_image.filename))
        data_manager.edit_profile_page(username, password, email, file_name, user_id)
        session.pop('id',None)
        session.pop('username',None)
        session.pop('email',None)
        session.pop("password", None)
        flash("You have changed your login info Please login again with your new data!","green") # somehow this message doesn't even show ://///
        return redirect("/")
    return render_template('edit_profile.html',list_the_users=list_the_users)


@app.route("/display/<question_id>/vote_up/", methods=["GET", "POST"])
def vote_up(question_id=None):
    if request.method == "GET":
        data_manager.update_question_vote(question_id, True)
        data_manager.update_rep_vote(question_id, True)
        return redirect(request.referrer)
    return render_template("display.html",question_id=question_id, add_questions=add_questions)

@app.route("/display/<question_id>/mark_answer/", methods=["GET"])
def mark_answer(question_id=None):

    if request.method == "GET":
        data_manager.mark_accepted(True, question_id)
        return redirect(request.referrer)
    return render_template("display.html", question_id=question_id, add_questions=add_questions, add_comment=add_comment)


@app.route("/display/<question_id>/disable_mark_answer/", methods=["GET"])
def disable_mark_asnwer(question_id=None):

    if request.method == "GET":
        data_manager.mark_accepted(False, question_id)
        return redirect(request.referrer)
    return render_template("display.html", question_id=question_id, add_questions=add_questions, add_comment=add_comment)

@app.route("/display/<question_id>/vote_down/", methods=["GET", "POST"])
def vote_down(question_id=None):

    if request.method == "GET":
        data_manager.update_question_vote(question_id,False)
        data_manager.update_rep_vote(question_id, False)
        return redirect(request.referrer)

    return render_template("display.html", question_id=question_id, add_questions=add_questions, add_comment=add_comment)


@app.route("/display/<question_id>", methods=["POST", "GET"])
def display_list(question_id=None, comment_id=None):
    list_usr = data_manager.list_users()
    list_nested_comments = data_manager.nested_comments(question_id)
    list_tags = data_manager.load_tags(question_id)
    list_comment = data_manager.show_comment(question_id)
    list_questions = data_manager.show_answer(question_id)
    data_manager.update_view(question_id)
  
    return render_template("display.html",list_usr=list_usr, list_tags=list_tags, question_id=question_id, comment_id=comment_id, list_comments=list_comment, list_questions=list_questions, nested_comment=list_nested_comments)


@app.route("/display/<comment_id>/delete", methods=["POST", "GET"])
def delete_answer(comment_id=None):
    if request.method == "GET":
        data_manager.delete_comment(comment_id)
        user_name = session["username"]
        data_manager.increment_answers(user_name, True)
        return redirect(request.referrer)
    return render_template("display.html", comment_id=comment_id)


@app.route("/delete/<question_id>", methods=["GET", "POST"])
def delete(question_id=None):

    if request.method == "GET":
        user_name = session["username"]
        data_manager.delete_question(question_id)
        data_manager.increment_questions(user_name, True)
        return redirect("/")
    return render_template("index.html", question_id=question_id)


@app.route("/comments/", methods=["POST", "GET"])
def show_comments():
    list_comments = data_manager.show_answers("answer")
    com_table_header = ['id', 'submission_time', 'vote_number', 'question_id', 'message', 'image']
    return render_template("comments.html", list_comments=list_comments, com_table_header=com_table_header)



@app.route("/comments/add/<question_id>", methods=["GET", "POST"])
def add_comments(question_id=None):
    list_questions = data_manager.show_message_only(question_id)
    if request.method == "POST":
        message = request.form["message"]
        submission_time = datetime.datetime.today()
        vote_number = 0
        file_name = "default.png"
        user_name = session["username"]
        uploaded_image = request.files['image']
        data_manager.increment_answers(user_name,False)
        if uploaded_image.filename != "":
            uploaded_image.save(os.path.join(app.config['UPLOAD_FOLDER'], uploaded_image.filename))
            file_name = uploaded_image.filename
        data_manager.add_new_answer(submission_time.strftime("%d-%B-%Y %H:%M:%S"), vote_number, question_id, message, file_name, user_name)
        return redirect("/display/" + question_id)
    return render_template("add_comment.html", question_id=question_id, list_questions=list_questions)


@app.route("/comments/<question_id>/<comment_id>/vote_up", methods=["GET", "POST"])
def vote_comment_up(comment_id=None, question_id=None):
    if request.method == "GET":
        data_manager.update_comment_vote(comment_id,True) 
        return redirect("/display/" + question_id)
    return render_template("display.html", question_id=question_id)


@app.route("/comments/<answer_id>/<question_id>/add/", methods=["GET", "POST"])
def add_answer_to_answer(answer_id=None, question_id=None):
    list_comments = data_manager.show_comment(question_id)
    show_mess_only = data_manager.show_answer_mgs_only(question_id, answer_id)
    if request.method == "POST":
        message = request.form["message"]
        user_name = session["username"]
        submission_time = datetime.datetime.today()
        data_manager.increment_comments(user_name, False)
        data_manager.answer_to_answer(answer_id, question_id, message, submission_time.strftime("%d-%B-%Y %H:%M:%S"), user_name)
        return redirect("/display/" + question_id)
    return render_template("add_answer_comment.html", question_id=question_id, answer_id=answer_id,list_comments=list_comments, show_mess_only=show_mess_only)



@app.route("/comments/<question_id>/<comment_id>/vote_down", methods=["GET", "POST"])
def vote_comment_down(comment_id=None, question_id=None):

    if request.method == "GET":
        data_manager.update_comment_vote(comment_id,False)
        return redirect("/display/ " + question_id)
    return render_template("display.html", question_id=question_id)


if __name__ == "__main__":
    app.run(debug=True, port=4987)
