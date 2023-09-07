from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from run import db, login_manager

class User(UserMixin, db.Model):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(50), index=True, unique=True)
  name = db.Column(db.String(50), index=True)
  rut = db.Column(db.String(), index=True, unique=True)
  email = db.Column(db.String(150), unique = True, index = True)
  password_hash = db.Column(db.String(150))
  contacts = db.Column(db.String())

  def set_password(self, password):
     self.password_hash = generate_password_hash(password)

  def check_password(self,password):
     return check_password_hash(self.password_hash,password)
  
@login_manager.user_loader
def load_user(user_id):
   return User.get(user_id)