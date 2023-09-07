import os
import psycopg2
import json
from werkzeug.security import generate_password_hash, check_password_hash

os.environ['DB_USERNAME'] = "admin_tt"
os.environ['DB_PASSWORD'] = "wertones1"

conn = psycopg2.connect(
        host="localhost",
        database="mydb_tt",
        user=os.environ['DB_USERNAME'],
        password=os.environ['DB_PASSWORD'])

# Open a cursor to perform database operations
cur = conn.cursor()

cur.execute('DROP TABLE IF EXISTS users;')
cur.execute('CREATE TABLE users (id serial PRIMARY KEY,'
                                 'name varchar (150) NOT NULL,'
                                 'rut varchar (12) NOT NULL,'
                                 'email varchar (50) NOT NULL,'
                                 'phone varchar (50) NOT NULL,'
                                 'password varchar (250),'
                                 'contacts text,'
                                 'isAdmin boolean NOT NULL);'
                                 )
thedictionary = {
    "rut": '19891823-7',
    "phones": ['+56961397981'],
    "mails": ['mrfernandez2@uc.cl']
}
cur.execute('INSERT INTO users (name, rut, email, phone, password, contacts, isAdmin)'
            'VALUES (%s, %s, %s, %s, %s, %s, %s)',
            ('Matías Fernández',
             '19891823-7',
             'mrfernandezb14@gmail.com',
             '+56961397981',
             generate_password_hash('wertones1'),
             json.dumps(thedictionary),
             False)
            )

cur.execute('INSERT INTO users (name, rut, email, phone, password, contacts, isAdmin)'
            'VALUES (%s, %s, %s, %s, %s, %s, %s)',
            ('Admin',
             '12345678-9',
             'admin@admin.com',
             '+56961397981',
             generate_password_hash('admin123'),
             json.dumps({}),
             True)
            )

conn.commit()

cur.close()
conn.close()