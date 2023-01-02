from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Length
import requests

API_KEY = "the key"
SEARCH_URL = "https://api.themoviedb.org/3/search/movie"

# Creating the form using FlaskForm
class RateMovieForm(FlaskForm):
    rating = StringField("Your Rating Out of 10 e.g. 7.5", validators=[DataRequired("Required field")])
    review = StringField("Your Review", validators=[DataRequired(message="Required field"),
                                                    Length(max=250,
                                                           message="The length must be lower than 250 character")])
    # id = HiddenField(default='{{ book.id }}')
    submit = SubmitField("Done")


class AddMovieForm(FlaskForm):
    title = StringField("Movie Title", validators=[DataRequired("Set the movie title")])
    submit = SubmitField("Add Movie")
# -------------

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)

# Creating the database
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///top-movies.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)


app.app_context().push()
db.create_all()

# # Here bellow inseting first record to test
# new_movie = Movie(
#         title="Phone Booth",
#         year=2002,
#         description="Publicist Stuart Shepard finds himself trapped in a phone booth,"
#                     " pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help,"
#                     " Stuart's negotiation with the caller leads to a jaw-dropping climax.",
#         rating=7.3,
#         ranking=10,
#         review="My favourite character was the caller.",
#         img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
#     )
# db.session.add(new_movie)
# db.session.commit()


@app.route("/")
def home():
    all_movies = Movie.query.order_by(Movie.rating).all()

    for i in range(len(all_movies)):
        # This line gives each movie a new ranking reversed from their order in all_movies
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()
    return render_template("index.html", movies=all_movies)


@app.route("/edit", methods=["GET", "POST"])
def edit():
    edit_form = RateMovieForm()
    movie_id = request.args.get("id")
    if edit_form.validate_on_submit():
        movie = Movie.query.get(movie_id)
        movie.rating = edit_form.rating.data
        movie.review = edit_form.review.data
        db.session.commit()
        return redirect(url_for('home'))

    return render_template("edit.html", form=edit_form)


@app.route("/delete", methods=["GET", "POST"])
def delete():
    movie_id = request.args.get('id')
    movie_to_delete = Movie.query.get(movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/add", methods=["POST", "GET"])
def add():
    add_form = AddMovieForm()
    if add_form.validate_on_submit():
        # Here send a request api receiving data at json format
        parameters = {
            "api_key": API_KEY,
            "query": add_form.title.data
        }
        response = requests.get(SEARCH_URL, params=parameters)
        response.raise_for_status()
        data = response.json()
        results = data["results"]
        movies = []
        for result in results:
            movies.append(
                {
                    "title": result["title"],
                    "release_date": result["release_date"],
                    "id": result["id"]
                }
            )
        return render_template("select.html", movies=movies)
    return render_template("add.html", form=add_form)


def search_by_id(movie_id):
    parameters = {
        "api_key": API_KEY,
        "movie_id": movie_id
    }
    response = requests.get(f"https://api.themoviedb.org/3/movie/{movie_id}?", params=parameters)
    response.raise_for_status()
    data = response.json()
    return data


@app.route("/entry/<int:id>/<string:year>/<string:title>")
def entry(id, year, title):
    data = search_by_id(id)
    backdrop_path = data["backdrop_path"]
    overview = data["overview"]
    int(year[0:4])
    new_movie = Movie(
            title=title,
            year=year,
            description=overview,
            rating=0,
            ranking=0,
            review="NULL",
            img_url=f"https://image.tmdb.org/t/p/w500/{backdrop_path}"
        )
    db.session.add(new_movie)
    db.session.commit()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
