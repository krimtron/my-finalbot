#pip install peewee

# run this file before starting the bot


from peewee import *

db = SqliteDatabase('database.sqlite3')


class BaseModel(Model):
    class Meta:
        database = db
        

class User(BaseModel):
    id = BigAutoField(primary_key=True)
    balance = IntegerField(default=50)
    victory = IntegerField(default=0)
    defeat = IntegerField(default=0)
    word = CharField(default='')
    attempts = IntegerField(default=0)
    guessed_letters = CharField(default='')
    is_playing = BooleanField(default=False)
    bonus_multiplier = IntegerField(default=0)
    

def create_tables():
    with db:
        db.create_tables([User])
        

if __name__ == '__main__':
    create_tables()
