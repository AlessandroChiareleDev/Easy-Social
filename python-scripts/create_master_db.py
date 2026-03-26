import psycopg2

# First, connect as postgres superuser to create the DB
# Try common passwords for local postgres
passwords = ['postgres', '', 'admin', 'sua_senha_segura']

for pw in passwords:
    try:
        conn = psycopg2.connect(host='localhost', port=5432, dbname='postgres', user='postgres', password=pw)
        conn.autocommit = True
        cur = conn.cursor()
        
        cur.execute("SELECT 1 FROM pg_database WHERE datname = 'easy_social_master'")
        if cur.fetchone():
            print('easy_social_master already exists')
        else:
            cur.execute('CREATE DATABASE easy_social_master OWNER easy_social_user')
            print('easy_social_master CREATED')
        
        # Also ensure easy_social_user has CREATEDB privilege for future
        cur.execute('ALTER USER easy_social_user CREATEDB')
        print('Granted CREATEDB to easy_social_user')
        
        cur.close()
        conn.close()
        print(f'Connected with postgres password: {"(empty)" if pw == "" else pw}')
        break
    except Exception as e:
        print(f'Failed with password "{pw}": {e}')
        continue
else:
    print('\nCould not connect as postgres superuser.')
    print('Please run manually:')
    print('  CREATE DATABASE easy_social_master OWNER easy_social_user;')
    exit(1)
