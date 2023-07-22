from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SubmitField, HiddenField
from wtforms.validators import DataRequired
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = 'add_secret_key'
Bootstrap(app)

# db:
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///movies.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.app_context().push()
db = SQLAlchemy(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), nullable=True)
    year = db.Column(db.Integer, nullable=True)
    description = db.Column(db.String(750), nullable=True)
    rating = db.Column(db.Integer)
    ranking = db.Column(db.Integer)
    review = db.Column(db.String(250))
    img_url = db.Column(db.String(250))


db.create_all()


class EditForm(FlaskForm):
    rating = FloatField('Your Rating out of 10 eg: 7.5', validators=[DataRequired()])
    review = StringField('Your Review', validators=[DataRequired()])
    # id = HiddenField()
    submit = SubmitField('Submit')


class AddForm(FlaskForm):
    title = StringField('Movie Title', validators=[DataRequired()])
    submit = SubmitField("Add Movie")


@app.route("/")
def home():
    # all_movies = db.session.query(Movie).all()
    all_movies = Movie.query.order_by(Movie.rating).all()  # This line creates a list of all the movies sorted by rating

    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i  # This line gives each movie a new ranking reversed from their order in all_movies

    db.session.commit()

    return render_template("index.html", movies=all_movies)


@app.route("/edit", methods=["GET", "POST"])
def edit():
    form = EditForm()
    movie_id = request.args.get("id")
    movie_selected = Movie.query.get(movie_id)
    print(movie_selected)

    if form.validate_on_submit():  # this is much easier as we don't have to move id from one html file to another
        print("True")

        new_rating = form.rating.data
        new_review = form.review.data

        movie_selected.rating = new_rating
        movie_selected.review = new_review
        db.session.commit()

        return redirect(url_for("home"))

    return render_template("edit.html", form=form)


@app.route("/delete")
def delete():
    movie_id = request.args.get("id")
    movie_to_delete = Movie.query.get(movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()

    return redirect(url_for('home'))


api_key = "enter_your_api_key"


@app.route("/add", methods=["GET", "POST"])
def add():
    form = AddForm()
    if form.validate_on_submit():
        movie_title = form.title.data

        response = requests.get(
            url=f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&language=en-US&query={movie_title}&page=1&include_adult=false")
        data = response.json()

        return render_template("select.html", data=data, n=len(data["results"]))

    return render_template("add.html", form=form)


@app.route("/select")
def select():
    movie_api_id = request.args.get("id")

    response = requests.get(url=f"https://api.themoviedb.org/3/movie/{movie_api_id}?api_key={api_key}&language=en-US")
    data = response.json()

    new_movie = Movie(
        title=data['title'],
        year=data['release_date'],
        description=data['overview'],
        img_url=f"https://image.tmdb.org/t/p/w500{data['poster_path']}"
    )
    db.session.add(new_movie)
    db.session.commit()

    return redirect(url_for('edit', id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
