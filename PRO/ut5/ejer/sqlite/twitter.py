from __future__ import annotations

import sqlite3

DB_PATH = 'twitter.db'

TWEET_EMOJI = '🐦'
RETWEET_EMOJI = '🔁'
MAX_TWEET_LENGTH = 280


def create_db(db_path: str = DB_PATH) -> None:
    """Crea la base de datos y las siguientes tablas:
    - user (id, username, password, bio)
    - tweet (id, content, user_id, retweet_from)
        └ user_id es clave ajena de user(id)
        └ retweet_from es clave ajena de tweet(id)"""
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    create_tables = """
    CREATE TABLE user(
    id INTEGER PRIMARY KEY,
    username TEXT,
    password TEXT,
    bio TEXT
    );
    CREATE TABLE tweet(
    id INTEGER PRIMARY KEY,
    content TEXT,
    user_id INTEGER REFERENCES user(id),
    retweet_from INTEGER REFERENCES tweet(id)
    );
"""
    cur.executescript(create_tables)
    con.commit()
    con.close()


class User:
    def __init__(self, username: str, password: str, bio: str = '', user_id: int = 0):
        """Constructor de la clase User.
        - Crea los atributos con y cur para la conexión a la base de datos (con factoría Row).
        - Crea los atributos username, password, bio, id y logged.
        """
        self.con = sqlite3.connect('twitter.db')
        self.con.row_factory = sqlite3.Row
        self.cur = self.con.cursor()

        self.username = username
        self.password = password
        self.bio = bio
        self.user_id = user_id
        self.logged = False
        pass

    def save(self) -> None:
        """Guarda en la base de datos un objeto de tipo User.
        Además actualiza el atributo "id" del objeto a partir de lo que devuelve la inserción."""
        sql = 'INSERT INTO user(username, password, bio) VALUES(:username, :password, :bio)'
        self.cur.execute(sql)
        self.con.commit()
        self.user_id = self.cur.lastrowid
        pass

    def login(self, password: str) -> None:
        """Realiza el login del usuario.
        Comprueba si existe este usuario con el password pasado por parámetro en la BBDD
        y actualiza los atributos correspondientes."""
        sql = 'SELECT FROM user WHERE username=:username AND password=:password)'
        self.logged = self.cur.execute(sql, dict(username=self.username, password=self.password)).fetchone() in not None

        pass

    def tweet(self, content: str) -> Tweet:
        """Crea un tweet con el contenido indicado y lo almacena en la base de datos.
        - Utiliza el método save propio de la clase Tweet.
        - Hay que retornar el tweet creado.
        - Si el usuario no está logeado hay que lanzar una excepción de tipo TwitterError
        con el mensaje: User <usuario> is not logged in!
        - Si el tweet supera el límite de caracteres hay que lanzar una excepción de tipo
        TwitterError con el mensaje: Tweet hasta more than 280 chars!"""
        if not self.logged :
            raise TwitterError(f'User {self.username} is not logged in!')
        if len(self.content) > 280:
            raise TwitterError('Tweet has more than 280 chars!')
        tweet = Tweet(content)
        tweet.save(self)
        return tweet

    def retweet(self, tweet_id: int) -> Tweet:
        """Crea un retweet con el contenido indicado y lo almacena en la base de datos.
        - Utiliza el método save propio de la clase Tweet.
        - Hay que retornar el tweet creado.
        - Si el usuario no está logeado hay que lanzar una excepción de tipo TwitterError
        con el mensaje: User <usuario> is not logged in!
        - Si tweet_id no existe en la base de datos hay que lanzar una excepción de tipo
        TwitterError con el mensaje: Tweet with id <id> does not exist!"""
        sql = cur.execute('SELECT id FROM tweet WHERE id=:id', dict(id=tweet_id))
        if not self.logged :
            raise TwitterError(f'User {self.username} is not logged in!')
        if sql.fetchone() is None:
            raise TwitterError('Tweet with id {tweet_id} does not exist!')
        tweet_content = cur.execute('SELECT content FROM tweet WHERE id=:tweet_id', dict(id=tweet_id)).fecthone()
        retweet = Tweet(tweet_content, tweet_id)
        retweet.save(self)
        return retweet

    @property
    def tweets(self):
        """Función generadora que devuelve todos los tweets propios del usuario.
        - Lo que se devuelven son objetos de tipo Tweet (usar el método from_db_row)."""
        for row in self.cur.execute('SELECT * FROM tweet WHERE user_id = :user_id', dict(user_id=self.id)):
            Yield Tweet.from_db_row(row)

    def __repr__(self):
        """Representa un usuario con el formato:
        <usuario>: <bio>"""
        return f'{self.username}: {self.bio}'
        

    @classmethod
    def from_db_row(cls, row: sqlite3.Row):
        """Crea un objeto de tipo User a partir de una fila de consulta SQL"""
        user_id, username, password, bio = row 
        return User(username, password, bio, user_id)


class Tweet:
    def __init__(self, content: str = '', retweet_from: int = 0, tweet_id: int = 0):
        """Constructor de la clase Tweet.
        - Crea los atributos con y cur para la conexión a la base de datos (con factoría Row)
        - Crea los atributos _content, retweet_from e id.
        - retweet_from indica el id del tweet que se retuitea.
          Un id válido debe ser mayor o igual que 1.
        - Si es un retweet el contenido debe ser la cadena vacía.
        """
        self.con = sqlite3.connect('twitter.db')
        self.con.row_factory = sqlite3.Row
        self.cur = self.con.cursor()

        self.retweet_from = retweet_from
        self.tweet_id = tweet_id
        self.content = '' if self.is_retweet else content
        pass

    @property
    def is_retweet(self) -> bool:
        """Indica si el tweet es un retweet."""
        return self.retweet_from > 1

    @property
    def content(self) -> str:
        """Devuelve el contenido del tweet.
        - Si es un retweet el contenido habrá que buscarlo en el tweet retuiteado."""
        if self.is_retweet:
            return cur.execute('SELECT FROM tweet WHERE id=:retweet_from', dict(retweet_from=self.retweet_from)).fetchone()['content']
        return self.content

    def save(self, user: User) -> None:
        """Guarda el tweet en la base de datos.
        - El parámetro user es el usuario que escribe el tweet.
        Además actualiza el atributo "id" del objeto a partir de lo que devuelve la inserción."""
        sql = 'INSERT INTO tweet(content, user_id, retweet_from) VALUES(:content, :user_id, :retweet_from)'
        cur.execute(sql, dict(content=self.content, user_id=self.user_id, retweet_from=self.retweet_from))
        self.con.commit()
        self.tweet_id = self.cur.lastrowid

        pass

    def __repr__(self):
        """Representa un tweet con el formato:
        <emoji> <content> (id=<id>)"""
        emoji = RETWEET_EMOJI if self.is_retweet else TWEET_EMOJI
        f'{emoji} {self.content} id={self.tweet_id}'
        pass

    @classmethod
    def from_db_row(cls, row: sqlite3.Row) -> Tweet:
        """Crea un objeto de tipo Tweet a partir de una fila de consulta SQL"""
        tweet_id, content, user_id, retweet_from = row
        return Tweet(retweet_from, tweet_id, content)


class Twitter:
    def __init__(self):
        """Constructor de la clase Twitter.
        - Crea los atributos con y cur para la conexión a la base de datos (con factoría Row)
        """
        self.con = sqlite3.connect('twitter.db')
        self.con.row_factory = sqlite3.Row
        self.cur = self.con.cursor()
        pass

    def add_user(self, username: str, password: str, bio: str = '') -> User:
        """Crea un objeto de tipo User y lo guarda en la base de datos.
        - Haz uso de los métodos ya creados.
        - Hay que retornar el objeto creado.
        - La contraseña debe seguir el siguiente formato:
          * Empezar con una arroba o un signo igual.
          * Continuar con 2, 3 o 4 dígitos.
          * Continuar con 2, 3 o 4 letras de la A-Z (incluyendo minúsculas).
          * Terminar con una exclamación o un asterisco.
        Si no sigue este formato hay que elevar una excepción de tipo TwitterError
        con el mensaje: Password does not follow security rules!"""
        valid_password_type = r'[@=]/d{2,4}[a-z]{2,4}[!*]'
        if not re.fullmatch(valid_password_type, password, re.I):
            raise TwitterError('Password does not follow security rules!')
        user = User(username, password, bio)
        user.save(self)
        return user
        pass

    def get_user(self, user_id: int) -> User:
        """Devuelve el usuario con el user_id indicado.
        Si el usuario no existe hay elevar una excepción de tipo TwitterError con el mensaje:
        User with id <id> does not exist!"""
        get_username = cur.execute('SELECT * FROM user WHERE id=:user_id' dict(user_id=user_id)).fecthone()
        if not get_username: 
            raise TwitterError('User with id {id} does not exist!')
        return User.from_db_row(get_username)


class TwitterError(Exception):
    def __init__(self, message = ''):
        error_mssg = message
        super().__init__(error_mssg)
