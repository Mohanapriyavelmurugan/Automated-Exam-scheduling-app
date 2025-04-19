import os

structure = {
    'exam_scheduler': {
        'database': ['init_db.py', 'exam_scheduler.db'],
        'csp': ['scheduler.py', 'constraints.py'],
        'interfaces': ['admin.py', 'invigilator.py', 'student.py'],
        '': ['main.py', 'requirements.txt']
    }
}

for root, folders in structure.items():
    for folder, files in folders.items():
        path = os.path.join(root, folder) if folder else root
        os.makedirs(path, exist_ok=True)
        for file in files:
            with open(os.path.join(path, file), 'w') as f:
                if file.endswith('.py'):
                    f.write('# ' + file + '\n\n')
                elif file == 'requirements.txt':
                    f.write('streamlit\npython-constraint\npandas\nsqlite3\n')