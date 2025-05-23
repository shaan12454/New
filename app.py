from flask import Flask, render_template, request, redirect, session
import os
from datetime import datetime
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key'

students_db = {}
teachers_db = {}

students_file = 'students.txt'
teachers_file = 'teachers.txt'
results_file = 'results.txt'

# Load student data from file
def load_students():
    if os.path.exists(students_file):
        with open(students_file, 'r') as f:
            for line in f:
                student_id, password, name, dob = line.strip().split(',')
                students_db[student_id] = {'password': password, 'name': name, 'dob': dob}

# Load teacher data from file
def load_teachers():
    if os.path.exists(teachers_file):
        with open(teachers_file, 'r') as f:
            for line in f:
                teacher_id, password, name = line.strip().split(',')
                teachers_db[teacher_id] = {'password': password, 'name': name}

# Save student data to file
def save_students():
    with open(students_file, 'w') as f:
        for student_id, data in students_db.items():
            f.write(f"{student_id},{data['password']},{data['name']},{data['dob']}\n")

# Save teacher data to file
def save_teachers():
    with open(teachers_file, 'w') as f:
        for teacher_id, data in teachers_db.items():
            f.write(f"{teacher_id},{data['password']},{data['name']}\n")

# Load users on app start
load_students()
load_teachers()

@app.route('/')
def index():
    return render_template('index.html',
                           student_logged_in=session.get('is_student_logged_in', False),
                           teacher_logged_in=session.get('is_teacher_logged_in', False))

# ---------- Student Routes ----------

@app.route('/student_login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        student_id = request.form['student_id']
        password = request.form['password']
        student = students_db.get(student_id)
        if student and student['password'] == password:
            session['is_student_logged_in'] = True
            session['student_id'] = student_id
            return redirect('/result_view')
        return 'Invalid credentials.'
    return render_template('student_login.html')

@app.route('/student_register', methods=['GET', 'POST'])
def student_register():
    if request.method == 'POST':
        student_id = request.form['student_id']
        password = request.form['password']
        name = request.form['name']
        dob = request.form['dob']
        if student_id in students_db:
            return 'Student ID already registered.'
        students_db[student_id] = {'password': password, 'name': name, 'dob': dob}
        save_students()
        return redirect('/student_login')
    return render_template('student_register.html')

@app.route('/result_view', methods=['GET'])
def student_results():
    if not session.get('is_student_logged_in'):
        return redirect('/student_login')

    student_id = session['student_id']
    student = students_db.get(student_id)
    results = []
    total_max_marks = 0
    total_obtained_marks = 0

    # Fetch student data
    if student:
        dob = datetime.strptime(student['dob'], '%Y-%m-%d')
        age = (datetime.now() - dob).days // 365
        student_info = {
            'name': student['name'],
            'dob': student['dob'],
            'age': age
        }

        # Load the results file and filter by student ID
        if os.path.exists(results_file):
            with open(results_file, 'r') as f:
                for line in f:
                    parts = line.strip().split(',')
                    if len(parts) != 6:
                        continue  # Skip bad lines
                    sid, subject, marks, max_marks, teacher_name, date = parts
                    if sid == student_id:
                        marks = int(marks)
                        max_marks = int(max_marks)
                        results.append({'subject': subject, 'marks': marks, 'max_marks': max_marks,
                                        'teacher_name': teacher_name, 'date': date})
                        total_obtained_marks += marks
                        total_max_marks += max_marks

        # Calculate overall performance
        overall_performance = round((total_obtained_marks / total_max_marks) * 100, 2) if total_max_marks > 0 else 0

        if overall_performance >= 90:
            grade = "A+"
        elif overall_performance >= 75:
            grade = "A"
        elif overall_performance >= 60:
            grade = "B"
        elif overall_performance >= 50:
            grade = "C"
        else:
            grade = "D"

        performance_data = {
            'subjects': [r['subject'] for r in results],
            'marks': [r['marks'] for r in results],
            'max_marks': [r['max_marks'] for r in results]
        }

        return render_template('result_view.html',
                               results=results,
                               student_name=student_info['name'],
                               student_id=student_id,
                               student_dob=student_info['dob'],
                               student_age=student_info['age'],
                               performance_data=json.dumps(performance_data),
                               overall_performance=overall_performance,
                               grade=grade)

    return "Student not found."

# ---------- Teacher Routes ----------

@app.route('/teacher_register', methods=['GET', 'POST'])
def teacher_register():
    if request.method == 'POST':
        teacher_id = request.form.get('teacher_id')
        password = request.form.get('password')
        name = request.form.get('name')
        if teacher_id in teachers_db:
            return 'Teacher ID already exists.'
        teachers_db[teacher_id] = {'password': password, 'name': name}
        save_teachers()
        return redirect('/teacher_login')
    return render_template('teacher_register.html')

@app.route('/teacher_login', methods=['GET', 'POST'])
def teacher_login():
    if request.method == 'POST':
        teacher_id = request.form.get('teacher_id')
        password = request.form.get('password')
        teacher = teachers_db.get(teacher_id)
        if teacher and teacher['password'] == password:
            session['is_teacher_logged_in'] = True
            session['teacher_id'] = teacher_id  # Store teacher_id in session
            return redirect('/upload_result')
        return 'Invalid credentials.'
    return render_template('teacher_login.html')

@app.route('/upload_result', methods=['GET', 'POST'])
def upload_result():
    if not session.get('is_teacher_logged_in'):
        return redirect('/teacher_login')
    
    # Debugging: Check if the teacher ID is correctly stored in session
    teacher_id = session.get('teacher_id')
    print(f"Teacher ID in session: {teacher_id}")
    
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        subject = request.form.get('subject')
        marks = request.form.get('marks')
        max_marks = request.form.get('max_marks')
        
        # Ensure teacher_name is fetched correctly using teacher_id stored in session
        teacher_name = teachers_db.get(teacher_id, {}).get('name', 'Unknown Teacher')
        print(f"Teacher Name fetched: {teacher_name}")
        
        date = datetime.now().strftime('%Y-%m-%d')  # Get the current date
        
        with open(results_file, 'a') as f:
            f.write(f"{student_id},{subject},{marks},{max_marks},{teacher_name},{date}\n")
        return redirect('/')
    return render_template('upload_result.html')

if __name__ == '__main__':
    app.run(debug=True)
