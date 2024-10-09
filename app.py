import pickle
import requests
import pandas as pd
import streamlit as st
from requests.exceptions import RequestException
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

# Load movie data and similarities
Movies_dict = pickle.load(open('movies_dict.pkl', 'rb'))
movies = pd.DataFrame(Movies_dict)

similarity = pickle.load(open('storyline_similarity.pkl', 'rb'))
similarity2 = pickle.load(open('director_similarity.pkl', 'rb'))
similarity3 = pickle.load(open('cast_similarity.pkl', 'rb'))

st.set_page_config(layout="wide", page_title="Movie Recommender Engine", page_icon="🎬")

default_poster = "https://via.placeholder.com/500x750?text=No+Poster+Available"

# Function to fetch main movie details including poster, homepage, overview, popularity, and genres
def fetch_main_poster(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=580057366f5ee50390833f77903bf462"
    retries = 15
    overview = "There is no Description Avialable"
    popularity = None
    genres = ["Unknown"]
    homepage = ""
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            overview = data.get('overview')
            popularity = data.get('popularity')
            genres = [i.get('name') for i in data.get('genres')]
            homepage = data.get('homepage')
            poster_path = data.get('poster_path')
        
            if poster_path:
                poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
            else:
                poster_url = default_poster
            return poster_url, overview, popularity, genres, homepage
        except requests.Timeout:
            logging.warning(f"Timeout occurred on attempt {attempt + 1}. Retrying...")
        except requests.ConnectionError as ce:
            logging.warning(f"Connection error on attempt {attempt + 1}. Retrying...")
        except RequestException as e:
            logging.warning(f"Request failed on attempt {attempt + 1}. Retrying...")

    return default_poster, overview, popularity, genres, homepage

# Function to fetch movie poster
def fetch_poster(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=580057366f5ee50390833f77903bf462"
    retries = 15
    homepage = ""
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            poster_path = data.get('poster_path')
            homepage = data.get('homepage')
        
            if poster_path:
                poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
            else:
                poster_url = None
            return poster_url, homepage
        
        except requests.Timeout:
            logging.warning(f"Timeout occurred on attempt {attempt + 1}. Retrying...")
        except requests.ConnectionError as ce:
            logging.warning(f"Connection error on attempt {attempt + 1}. Retrying...")
        except RequestException as e:
            logging.warning(f"Request failed on attempt {attempt + 1}. Retrying...")
        
    return None, homepage

# Function to recommend movies based on storyline similarity
def movie_recommend_storyline(movie):
    movie_index = movies[movies['title'] == movie].index[0]
    recommended_indices = similarity[movie_index][1:25]
    return recommended_indices

# Function to recommend movies based on director similarity
def movie_recommend_director(movie):
    movie_index = movies[movies['title'] == movie].index[0]
    recommended_indices = similarity2[movie_index][1:25]
    return recommended_indices

# Function to recommend movies based on cast similarity
def movie_recommend_cast(movie):
    movie_index = movies[movies['title'] == movie].index[0]
    recommended_indices = similarity3[movie_index][1:25]
    return recommended_indices

# Function to display recommendations with an expander for more items
def display_recommendations(names, posters, title):
    st.subheader(f"Recommended Movies {title}")
    
    # Ensure we have at least 5 movies for the top row
    top_recommendations = names[:5]  # Get top 5 recommendations
    top_posters = posters[:5]  # Get corresponding posters for top 5

    displayed_movies = 0  # Count of displayed movies in the top row
    cols = st.columns(5)
    
    for i in range(len(top_recommendations)):  # Iterate over the top recommendations
        poster_url, homepage_url = fetch_poster(top_posters[i])  # Fetch the poster URL
        
        if poster_url:  # Check if the poster URL is available
            with cols[displayed_movies]:  # Display movie in the column
                if homepage_url:
                    st.markdown(
                        f'<a href="{homepage_url}" target="_blank">'
                        f'<img src="{poster_url}" width="200" alt="{top_recommendations[i]}"/>'
                        '</a>',
                        unsafe_allow_html=True)
                else:
                    st.image(poster_url, width=200)  # Small poster size

                st.markdown(f'<p style="text-align: center; padding-right:50px;">{top_recommendations[i]}</p>', unsafe_allow_html=True)

            displayed_movies += 1  # Increment displayed movie count
            if displayed_movies >= 5:  # Stop after displaying 5 movies
                break
    
    index_skip = 0
    # # If not enough movies displayed, fill with additional recommendations
    for i in range(len(top_recommendations), len(names)):
        if displayed_movies >= 5:  # Break if we already displayed 5 movies
            break
        
        poster_url, homepage_url = fetch_poster(posters[i])  # Fetch the poster URL
        # if displayed_movies % 5 == 0:
        #     cols = st.columns(5)
        
        if poster_url:  # Check if the poster URL is available
            # with cols[displayed_movies]:  # Display movie in the column
            with cols[displayed_movies]:  # Display movie in the column
                if homepage_url:
                    st.markdown(
                        f'<a href="{homepage_url}" target="_blank">'
                        f'<img src="{poster_url}" width="200" alt="{names[i]}"/>'
                        '</a>',
                        unsafe_allow_html=True)
                else:
                    st.image(poster_url, width=200)  # Small poster size

                st.markdown(f'<p style="text-align: center; padding-right:50px;">{names[i]}</p>', unsafe_allow_html=True)
            displayed_movies += 1  # Increment displayed movie count
            index_skip += 1

    # Expander for the remaining recommendations, excluding top 5
    with st.expander("See More Movies " + title):
        expand_count = 0  # Count the number of movies in the expander
        for i in range(len(names)):  # Start from the 6th recommendation
            if i < displayed_movies:  # Skip the already displayed movies
                continue
            
            poster_url, homepage_url = fetch_poster(posters[i+index_skip])
            if expand_count % 5 == 0:
                cols = st.columns(5)
            if poster_url:
                with cols[expand_count % 5]:
                    if homepage_url:
                        st.markdown(
                            f'<a href="{homepage_url}" target="_blank">'
                            f'<img src="{poster_url}" width="200" alt="{names[i+index_skip]}"/>'
                            '</a>',
                            unsafe_allow_html=True
                        )
                    else:
                        st.image(poster_url, width=200)  # Small poster size

                    st.markdown(f'<p style="text-align: center; padding-right:50px;">{names[i+index_skip]}</p>', unsafe_allow_html=True)
                    expand_count += 1
            if expand_count >= 12:  # Stop after 20 movies
                break



# Streamlit UI
st.title('🎬 Movie Recommendation System')
st.divider()
movie_list = movies['title'].values
selected_movie_name = st.selectbox("Type or select a movie from the dropdown", movie_list, key='movie_selectbox')


def add_space_theme_css():
    st.markdown(
        """
        <style>
        /* Style for movie posters */
        img {
            border-radius: 10px;
            box-shadow: 0px 0px 15px rgba(255, 215, 0, 0.6); /* Glowing gold border */
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

# Call the function to apply space theme
add_space_theme_css()


if st.button('Recommend'):

    st.divider()
    movie_index = movies[movies['title'] == selected_movie_name].index[0]
    poster = movies.iloc[movie_index].id 
    poster_url, overview, popularity, genres, homepage_url = fetch_main_poster(poster)
    st.text(" ")
    col1, col2 = st.columns([2,3])
    with col1:
        if poster_url:
            if homepage_url:
                st.markdown(
                    f'<a href="{homepage_url}" target="_blank">'
                    f'<img src="{poster_url}" width="450" alt="{selected_movie_name}"/>'
                    '</a>',
                    unsafe_allow_html=True
                )
            else:
                st.image(poster_url, width=450) 
    with col2:
        st.text(" ")
        st.header(selected_movie_name)
        st.text(" ")
        st.text(" ")
        st.write(overview)
        st.text(" ")
        st.write("Genres: " + ", ".join(genres))
        st.text(" ")
        st.write("\nPopularity: " + str(popularity))


    # Storyline recommendations
    storyline_indices = movie_recommend_storyline(selected_movie_name)
    storyline_names = [movies.iloc[i].title for i in storyline_indices]
    storyline_posters = [movies.iloc[i].id for i in storyline_indices]

    # Display storyline recommendations
    st.divider()
    display_recommendations(storyline_names, storyline_posters, "Based on Storyline")

    # Director recommendations
    director_indices = movie_recommend_director(selected_movie_name)
    director_names = [movies.iloc[i].title for i in director_indices]
    director_posters = [movies.iloc[i].id for i in director_indices]

    # Display director recommendations
    st.divider()
    display_recommendations(director_names, director_posters, "Based on Director")

    # Cast recommendations
    cast_indices = movie_recommend_cast(selected_movie_name)
    cast_names = [movies.iloc[i].title for i in cast_indices]
    cast_posters = [movies.iloc[i].id for i in cast_indices]

    # Display cast recommendations
    st.divider()
    display_recommendations(cast_names, cast_posters, "Based on Cast")