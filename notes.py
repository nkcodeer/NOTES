from flask import Flask, render_template, request, redirect, url_for, session, flash
import firebase_admin
from firebase_admin import credentials, firestore, auth

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a strong secret key

# Initialize Firebase Admin SDK
cred = credentials.Certificate('config/serviceAccountKey.json')  # Update with your path
firebase_admin.initialize_app(cred)

# Initialize Firestore
db = firestore.client()

@app.route('/')
def index():
    if 'user' in session:
        return render_template('index.html', user=session['user'])
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        try:
            user = auth.get_user_by_email(email)
            session['user'] = user.email
            return redirect(url_for('index'))
        except Exception as e:
            flash('Login failed. Please check your email and password.', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        try:
            user = auth.create_user(email=email, password=password)
            flash('User created successfully! You can now log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash('Sign up failed. Please try again.', 'danger')
            return redirect(url_for('signup'))
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/add_note', methods=['POST'])
def add_note():
    note_content = request.form.get('note')
    category = request.form.get('category')  # Get the category from the form
    if note_content and category:
        # Add a new note to Firestore with category
        db.collection('notes').add({'content': note_content, 'category': category})
    return redirect(url_for('index'))

@app.route('/category/<category_name>')
def category_notes(category_name):
    if 'user' in session:
        # Fetch notes from Firestore by category
        notes_ref = db.collection('notes').where('category', '==', category_name)
        notes = notes_ref.stream()
        notes_list = [{"id": note.id, "content": note.to_dict().get('content')} for note in notes]
        return render_template('category.html', notes=notes_list, user=session['user'], category=category_name)
    return redirect(url_for('login'))

@app.route('/edit/<note_id>', methods=['GET', 'POST'])
def edit_note(note_id):
    if request.method == 'POST':
        updated_note = request.form.get('note')
        category = request.form.get('category')  # Get the updated category
        if updated_note and category:
            # Update the note in Firestore
            db.collection('notes').document(note_id).update({'content': updated_note, 'category': category})
        return redirect(url_for('index'))
    
    # Fetch the note to edit
    note_ref = db.collection('notes').document(note_id)
    note = note_ref.get()
    return render_template('edit.html', note=note.to_dict(), note_id=note_id)

@app.route('/delete/<note_id>')
def delete_note(note_id):
    # Delete the note from Firestore
    db.collection('notes').document(note_id).delete()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)