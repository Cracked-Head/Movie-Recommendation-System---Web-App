import pandas as pd     # To manipulate dataframe
import streamlit as st      # To create the web app
import joblib       # To load the data
import requests     # To handle requests

# The API key
API_KEY = '69ffd6b40c8570d7299903e9ddbeba63'

# This is set the web page configuration
st.set_page_config(
     page_title="Movie Recommender"
 )


def get_movie_detail(movie_id):
    """
    :param movie_id: The movie id of the movie whose details need to be fetched
    :return: The movie details, stops the web app if there is a connection Error
    """

    # The Movie URL --> To fetch the movie detail like runtime,title etc
    movie_url = f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US'
    # The Credit URL --> To fetch the Cast and Crew of the movie
    credit_url = f'https://api.themoviedb.org/3/movie/{movie_id}/credits?api_key={API_KEY}&language=en-US'

    # This is a flag for successful https request, if error then success will be False
    success = True

    # To handle any exception they may arise during GET request
    try:
        # fetching the movie detail
        movie_response = requests.get(movie_url)
        # fetching the credit detail
        credit_response = requests.get(credit_url)

    # except block for catching the errors, Success is set to False
    # For connection related error
    except requests.exceptions.ConnectionError as conn_err:
        st.session_state.connection = False
        success = False

    # For other request errors
    except requests.exceptions.RequestException as e:
        st.session_state.connection = False
        success = False

    # Check for successful request
    if success:
        # storing the connection success/failure
        # --> This will help other function in responding to Request Fail situation
        st.session_state.connection = True

        # Converting to response to json format
        movie_data = movie_response.json()
        credit_data = credit_response.json()

        # The movie poster url
        poster = "https://image.tmdb.org/t/p/w500/{}".format(movie_data["poster_path"])
        # The overview of the movie
        overview = movie_data['overview']
        # The homepage of the movie
        homepage = movie_data['homepage']
        # The title of the movie
        title = movie_data['title']
        # The duration of the movie
        runtime = movie_data['runtime']

        # Fetching the first 3 actors' name of the movie and converting to list
        actor3_df = pd.DataFrame(credit_data['cast'])[:3]
        actor_list = list([actor3_df['name']])
        actors = list(actor_list[0])

        # Fetching the directors name and converting to list
        crew = pd.DataFrame(credit_data['crew'])
        director = list(crew[crew['job'] == 'Director']['name'])

        # The movie detail dictionary
        movie_detail = {
            "poster": poster,
            "title": title,
            "overview": overview,
            "homepage": homepage,
            "actors": actors,
            "director": director,
            "runtime": runtime
        }
        # returning the movie detail
        return movie_detail

    # success is False --> Error Occur, then inform the user
    st.info("Session Expire -- Please Try Another Time")
    # Web app stop
    st.stop()


def update_movie_detail(movies_list):
    """
    :param movies_list : A list containing the recommended movies
    :return: None, it updates the recommended movie list already in the users session
    """
    st.session_state.movies_list = movies_list


def recommender(movie_name):
    """
    :param movie_name: The movie name, by which similar movies will be recommended
    :return: None: The recommended movie list is updated in the session's movie list
    """

    # Getting index of the movie index so as it identify its row number in the movie dataset
    movie_index = st.session_state.movies_data[st.session_state.movies_data.title == movie_name].index[0]
    # The similarity distance of the movie with other movies
    distance = st.session_state.similarity_matrix[movie_index]
    # sorting the list based on highest similarity, and only extracting 5 movies
    movies_list = sorted(list(enumerate(distance)), key=lambda tup: tup[1], reverse=True)[1:6]

    # For storing the recommended movies
    recommended_movies = []
    # Iterating over each movie
    for movie_tuple in movies_list:
        # Extracting the movie ID the movie
        movie_id = st.session_state.movies_data.iloc[movie_tuple[0]].movie_id
        # Fetching the movie details
        movie_detail = get_movie_detail(movie_id)
        # Add to recommendation
        recommended_movies.append(movie_detail)

    # Update the sessions' recommended movie list
    update_movie_detail(recommended_movies)


def display_recommendations():
    """
    :return: None: It just displays the recommended movies
    """

    # Container to hold all the elements
    with st.container():
        # Retrieve the recommended movies
        movie_list = st.session_state.movies_list
        # For indexing the movie list
        index = 0
        # Loop to traverse the list
        for _ in range(5):

            # Get the movie detail from the movie list
            movie = movie_list[index]

            # create two column for movie poster and descriptions
            col1, col2 = st.columns([1, 2])

            # The poster of the movie
            col1.image(movie['poster'])

            # Title of the movie
            col2.subheader(movie['title'])

            # A collapsable element to display description, crew, and runtime.
            description = col2.expander("Description")
            description.write(movie['overview'])

            more_detail = col2.expander("More Detail")
            actors = ", ".join(movie['actors'])
            directors = ", ".join(movie['director'])
            more_detail.write("Actor: "+actors+".")
            more_detail.write("Director: "+directors+".")
            more_detail.write("Runtime: "+str(movie['runtime'])+" mins.")
            index += 1


# title should be displayed once and not need to be reloaded again
if 'title' not in st.session_state:
    # Store the title so as not to reload again
    st.session_state['title'] = "Movie Recommender System"
    # Since, at starting there will be no recommendation
    st.session_state['recommendations'] = False

# Display the title
st.title( st.session_state.title)

# Storing the movies' data in the session
# This is not required
if 'movies_data' not in st.session_state:
    st.session_state['movies_data'] = joblib.load('movies_data.pkl')

# Storing the movies' similarity data in the session
# This is not required
if 'similarity_matrix' not in st.session_state:
    st.session_state['similarity_matrix'] = joblib.load("similarity.pkl")

# Select box for choosing the movies
# Recommendations will be based on the selected movie
selected_movie = st.selectbox(
     'How would you like to be contacted?',
     st.session_state.movies_data['title'], key="selected_movie")

# Just to display the chosen movie. (Not required)
st.write('You selected:', selected_movie)

# A Recommendation button
recommend = st.button('Recommend')

# Button Clicked, then recommend
if recommend:
    # Session recommendation is True as recommendation exists.
    st.session_state.recommendations = True
    # Calling the recommendation function with the selected movie
    recommender(st.session_state.selected_movie)
    # If request is successful then display, otherwise do nothing
    if st.session_state.connection:
        display_recommendations()

# Display any recommendation if they are already in the session and Recommend button has not been clicked
if not recommend and st.session_state.recommendations:
    display_recommendations()
