from flask import Flask, render_template, request, redirect, url_for, session, flash,send_file, make_response
from sqlalchemy import func
from model import db, User, Book, Section, Borrowing,Completed # Database Information and importing Here
from datetime import datetime,timedelta

#Matplotlib related imports
import matplotlib
matplotlib.use('Agg')
from io import BytesIO
import base64
import matplotlib.pyplot as plt

#import upload
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] =  'static/uploads'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Laibrary_db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key_here'

with app.app_context():
    db.init_app(app)
    db.create_all()
'''======================================== This is a Index Route ================================================================'''
@app.route('/')
def index():
    return render_template('index.html')

'''======================================== This is a User Login  Route ================================================================'''
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if not user:
            flash('User does not exist')
            return redirect(url_for('login'))

        if not user.check_password(password):
            flash('Incorrect Password')
            return redirect(url_for('login'))
        session['user_id'] = user.id
        return redirect(url_for('user_dashboard'))
    return render_template('login.html')

'''======================================== This is a Admin Login Route ================================================================'''
@app.route('/admin_login', methods=['Get','Post'])
def admin_login():
    username = None
    password = None

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == 'admin' and password == 'admin':
            return redirect(url_for('admin'))
        else:
            flash('Invalid Laibrarian_id or Password')
            return redirect(url_for('admin_login'))

    return render_template('admin_login.html')

'''======================================== This is a New User Register Route ================================================================'''
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        name = request.form.get('name')
        occupation = request.form.get('occupation')
        if not all((username, password, name,occupation)):
            flash('Invalid form data. Please fill in all fields.')
            return redirect(url_for('register'))
        if User.query.filter_by(username=username).first():
            flash('Username already exists. Please choose a different username.')
            return redirect(url_for('register'))

        # Create a new user and add to the database
        user = User(username=username, password=password, name=name,occupation=occupation)
        db.session.add(user)
        db.session.commit()

        flash('User successfully registered. You can now log in.')
        return redirect(url_for('login'))

    # If the request method is GET, render the registration template
    return render_template('register.html')

'''======================================== This is a User Dashboard Route ================================================================'''
@app.route('/user', methods=['GET', 'POST'])
def user_dashboard():
    user_id = session.get('user_id')
    if 'user_id' not in session:
        return redirect(url_for('login'))
    search_query = request.form.get('search_querry', '')
    
    if request.method == 'POST':
        val = request.form.get('val')
        if not val:
            return render_template('/user/user_main.html', sections=Section.query.all(), user=User.query.get(user_id), books=Book.query.all(), search_query=search_query)
        
        if val == "b_section":
            new_sec = Section.query.filter(Section.name.ilike('%' + search_query + '%')).all()
            return render_template('/user/user_main.html', sections=new_sec, user=User.query.get(user_id), books=Book.query.all(), search_query=search_query)

        if val == "b_title":
            filtered_books = Book.query.filter(Book.name.ilike('%' + search_query + '%')).all()
            return render_template('/user/user_main.html', sections=Section.query.all(), user=User.query.get(user_id), books=filtered_books,  b_title=search_query)

        if val == "b_author":
            filtered_books = Book.query.filter(Book.author.ilike('%' + search_query + '%')).all()
            return render_template('/user/user_main.html', sections=Section.query.all(), user=User.query.get(user_id), books=filtered_books, b_author=search_query)
        if val == "b_isbn":
            filtered_books = Book.query.filter(Book.isbn.ilike('%' + search_query + '%')).all()
            print(filtered_books)
            return render_template('/user/user_main.html', sections=Section.query.all(), user=User.query.get(user_id), books=filtered_books, search_query=search_query, b_isbn=search_query)
    return render_template('/user/user_main.html', sections=Section.query.all(), user=User.query.get(user_id), books=Book.query.all())
#============================== This is a want to read Routes ================>
@app.route('/want_to_read/<int:book_id>',methods=['GET', 'POST'])
def want_to_read(book_id):
    user_id = session.get('user_id')
    if 'user_id' not in session:
        return redirect(url_for('login'))
    existing_borrowing = Borrowing.query.filter_by(user_id=user_id, book_id=book_id).first()
    if existing_borrowing:
        flash('You have already borrowed this book.')
        return redirect(url_for('user_dashboard'))
    current_borrowed_books = Borrowing.query.filter_by(user_id=user_id).count()
    if current_borrowed_books >= 5:
        flash('You can take 5 books only.')
        return redirect(url_for('user_dashboard'))
    return_date = datetime.utcnow() + timedelta(days=7)
    return_date = return_date

    new_borrowing = Borrowing(user_id=user_id, book_id=book_id, return_date=return_date)
    db.session.add(new_borrowing)
    db.session.commit()
    flash('Book borrowed successfully.')
    return redirect(url_for('current_reads'))
#============================== This is a Pdf view Routes ================>
@app.route('/user/myBook/<int:id>/Reads Laibrary')
def view_book(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    book = Book.query.get(id)
    if not book:
        flash('Book not found')
        return redirect(url_for('current_reads'))
    if not book.file_path:
        flash(f'Wait till the book get released in Laibrary.')
        return redirect(url_for('current_reads'))
    else:
        return send_file(book.file_path, as_attachment=False)   

#============================== This is a View1 Routes ================>
@app.route('/user/myBook/<int:id>/view')
def view1(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    book = Book.query.get(id)
    if book:
        flash(f'Book Description: {book.description}')
    return redirect(url_for('current_reads'))

#============================== This is a User Mybook Main Routes ================>
@app.route('/user/myBook')
def mybook_main():
    user_id = session.get('user_id')
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('/user/user_mybook_main.html', user=User.query.get(user_id))

#============================== This is a User Current Reads Routes ================>
@app.route('/user/myBook/current_read')
def current_reads():
    user_id = session.get('user_id')
    if 'user_id' not in session:
        return redirect(url_for('login'))
    borrow = Borrowing.query.filter_by(user_id=user_id).all()
    return render_template('/user/user_book_current.html', user=User.query.get(user_id), borrows=borrow)
#============================== This is a User Completed Reads Routes ================>
@app.route('/user/myBook/completed_read')
def completed_reads():
    user_id = session.get('user_id')
    if 'user_id' not in session:
        return redirect(url_for('login'))
    complete = Completed.query.filter_by(user_id=user_id).all()
    return render_template('/user/user_book_completed.html', user=User.query.get(user_id), completed = complete)

#============================== This is a return book routes Routes ================>
@app.route('/user/myBook/return_book/<int:borrow_id>')
def return_book(borrow_id):
    user_id = session.get('user_id')
    if 'user_id' not in session:
        return redirect(url_for('login'))
    borrow = Borrowing.query.filter_by(book_id=borrow_id)
    for borrowing in borrow:
        complete_book = Completed(user_id=user_id, book_id=borrowing.book_id)
        db.session.add(complete_book)
        db.session.delete(borrowing)
        db.session.commit()
    flash('Book returned successfully.')
    return redirect(url_for('completed_reads'))
#============================== This is a User Feedback Routes ================>
@app.route('/submit-feedback', methods=['POST'])
def submit_feedback():
    user_id = session.get('user_id')
    if 'user_id' not in session:
        return redirect(url_for('login'))
    book_id = request.form['book_id']
    feedback_type = request.form['feedback_type']

    existing_feedback = Completed.query.filter_by(user_id=user_id, book_id=book_id).first()
    if existing_feedback and existing_feedback.feedback == 'submitted':
        flash('Feedback already submitted for this book')
        return redirect(url_for('completed_reads'))
    
    if feedback_type == 'good' or feedback_type == 'bad':
        book = Book.query.get(book_id)
        if book:
            if feedback_type == 'good':
                book.good_count += 1
                flash('Great you like the book !!')
            else:
                book.bad_count += 1
                flash('Check for other book as well !!')
            db.session.commit()
            if existing_feedback:
                existing_feedback.feedback = 'submitted'
            else:
                completed_feedback = Completed(user_id=user_id, book_id=book_id, datetime=datetime.utcnow(), feedback='submitted')
                db.session.add(completed_feedback)
                flash('Feedback submitted successfully', 'success')
            db.session.commit()
    return redirect(url_for('completed_reads'))

#============================== This is a User Current Reads Routes ================>
@app.route('/user/myBook/user_stats')
def user_stat():
    user_id = session.get('user_id')
    if 'user_id' not in session:
        return redirect(url_for('login'))
    #return render_template('/user/user_stats.html', user=User.query.get(user_id))

    user = User.query.get(user_id)
    borrow_books = Borrowing.query.filter_by(user=user).all()
    completed_books = Completed.query.filter_by(user=user).all()

    # Count the number of borrowed books
    num_borrowed_books = len(borrow_books)
    num_completed_books = len(completed_books)
    book_status = ['Borrowed', 'Completed']
    book_counts = [num_borrowed_books, num_completed_books]
    plt.bar(book_status, book_counts,width=0.5)
    plt.xlabel('Book Status')
    plt.ylabel('Number of Books')
    plt.title('Book Borrowing and Completion Status')
    plt.yticks(range(0, max(book_counts) + 1, 1))
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plot_data = base64.b64encode(buffer.read()).decode('utf-8')
    return render_template('user/user_stats.html', user=user, plot_data=plot_data)

#============================== This is a User Log out Routes ================>
@app.route('/loginfirst')
def logout():
    session.clear()
    return redirect(url_for('login'))

'''======================================== This is a Admin Dashboard Route ================================================================'''
#============================== This is a Admin Dashboard Routes ================>
@app.route('/admin')
def admin():
    return render_template('/admin/admin_main.html')
#============================== This is a User info. Routes ===================>
@app.route('/admin/record')
def record():
    books = Book.query.all()
    count_occup = db.session.query(User.occupation, func.count(User.id)).group_by(User.occupation).all()
    count_book_section = db.session.query(Section.name, func.count(Book.id)).outerjoin(Book).group_by(Section.name).all()
    section_count = Section.query.count()
    return render_template('/admin/admin_record.html',count_occup = count_occup,section_count=section_count,count_book_section=count_book_section,books=books)
#============================== This is a Admin-Section Routes ===================>
@app.route('/admin/section')
def section():
    sections = Section.query.all()
    return render_template('/admin/admin_section.html', Sections=sections)
#======================== Add Section Routes ================>
@app.route('/section/add-section', methods=['GET', 'POST'])
def add_section():
    if request.method == 'POST':
        sect_name = request.form.get('section_name')
        sect_desc = request.form.get('section_desc')
        if sect_name=='' or sect_desc=='':
            flash('Section does not exist.')
        elif Section.query.filter_by(name=sect_name).first():
            flash('Section name already exists. Please choose a different name.')
        else:
            # Create a new section with the current date and time
            section = Section(name=sect_name, description=sect_desc, date_created=datetime.now())
            db.session.add(section)
            db.session.commit()
            flash('Section added successfully.', 'success')
            return redirect(url_for('section'))
    return render_template('/admin/add_section.html')

#======================== Edit Section Routes ================>
@app.route('/section/<int:id>/edit_section',methods=['GET','POST'])
def edit_section(id):
    section = Section.query.get(id)
    if request.method == 'POST':
        new_name = request.form.get('section_name')
        new_description = request.form.get('section_desc')
        section.name = new_name
        section.description = new_description
        db.session.commit()
        flash('Section updated successfully.')
        return redirect(url_for('section'))
    return render_template('/admin/edit_section.html',section=section)
#======================== Delete Section Routes ================>
@app.route('/section/<int:id>/delete_section')
def delete_section(id):
    section = Section.query.get(id)
    if not section:
        flash('Section does not exist.')
        return redirect(url_for('section'))
    # Delete associated books
    books = Book.query.filter_by(section_id=id).all()
    for book in books:
        db.session.delete(book)
    db.session.delete(section)
    db.session.commit()
    flash('Section and associated books deleted successfully.')
    return redirect(url_for('section'))
#=========================== This is a Admin-Section Books Routes ================>
@app.route('/section/<int:id>/books')
def books(id):
    section = Section.query.get(id)
    books = Book.query.filter_by(section_id=id).all()
    return render_template('/admin/admin_books.html', section=section, books=books)
#=========================== This is a Admin-add Books Routes ================>
@app.route('/section/<int:id>/books/add_book', methods=['GET', 'POST'])
def add_book(id):
    section = Section.query.get(id)  # Fetch the section based on the provided id 
    if request.method == 'POST':
        book_name = request.form.get('book_name')
        book_author = request.form.get('book_author')
        book_isbn = request.form.get('book_isbn')
        book_desc = request.form.get('book_desc')
        book_upload = request.files['book_upload']

        if book_name == '' or book_desc == '' or book_author == '' or book_isbn == '':
            flash('Book information incomplete.')
            return redirect(url_for('add_book', id=id))
        if book_upload.filename == '':
            flash('No selected file.')
            return redirect(url_for('add_book', id=id))
        if Book.query.filter_by(name=book_name).first():
            flash('Book already exists.')
            return redirect(url_for('add_book', id=id))

        filename = secure_filename(book_upload.filename)
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        upload_path = upload_path.replace('/', '\\')
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        book_upload.save(upload_path)
        new_book = Book(name=book_name, author=book_author, isbn=book_isbn, description=book_desc, section=section, file_path=upload_path)
        db.session.add(new_book)
        db.session.commit()

        flash('Book added successfully.')
        return redirect(url_for('books', id=id))

    return render_template('/admin/add_books.html', section=section)
#======================== Edit book Routes ================>
@app.route('/section/<int:section_id>/books/<int:book_id>/edit_book', methods=['GET', 'POST'])
def edit_book(section_id, book_id):
    section = Section.query.get(section_id)
    book = Book.query.get(book_id)

    if request.method == 'POST':
        book.name = request.form.get('book_name')
        book.author = request.form.get('book_author')
        book.isbn = request.form.get('book_isbn')
        book.description = request.form.get('book_desc')
        new_upload = request.files.get('book_upload')
        if new_upload and new_upload.filename != '':
            if os.path.exists(book.file_path):
                os.remove(book.file_path)
            filename = secure_filename(new_upload.filename)
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            new_upload.save(upload_path)
            book.file_path = upload_path
        db.session.commit()

        flash('Book updated successfully.') 
        return redirect(url_for('books', id=section_id))

    return render_template('/admin/edit_book.html', section=section, book=book)
#======================== Edit Section Routes ================>
@app.route('/section/<int:section_id>/books/<int:book_id>/delete_book')
def delete_book(section_id,book_id):
    book = Book.query.filter_by(id=book_id, section_id=section_id).first()
    if book.id:
        file_path = book.file_path
        if os.path.exists(str(file_path)):
            os.remove(file_path)
            print("Book PDF file deleted successfully.")
        else:
            print("Book PDF file not found.")
        completed_records = Completed.query.filter_by(book_id=book_id).all()
        for completed_record in completed_records:
            db.session.delete(completed_record)
        db.session.delete(book)
        db.session.commit()
        flash('Book deleted successfully.')
    else:
        flash('Book not found.')
    return redirect(url_for('books', id=section_id))

#=========================== This is a Admin-Reader Routes =======================>
@app.route('/admin/reader')
def reader():
    user = User.query.all()
    borrow = Borrowing.query.all()
    return render_template('/admin/admin_user_info.html', borrows=borrow)
#=========================== This is a Reject reader Routes =======================>
@app.route('/admin/reader/<int:id>/remove')
def reject_book(id):
    borrow = Borrowing.query.get(id)
    if borrow:
        db.session.delete(borrow)
        db.session.commit()
        flash('Book rejected successfully.')
    else:
        flash('Book not found.')
    return redirect(url_for('reader'))

'''======================================== This is a Debug statement ================================================================'''

if __name__ == '__main__':
    app.run(debug=True)
