import os
import requests
import shutil
import json
from urllib.parse import quote

class MovieFetcher:
    """Classe para buscar informações de filmes via API do TMDB."""
    
    def __init__(self, api_key=None):
        # Você precisará obter uma chave de API do TMDB
        self.api_key = api_key or os.environ.get("TMDB_API_KEY", "d4affd4cdfcd7bc2b5f5f27a2ca99b1e")
        self.base_url = "https://api.themoviedb.org/3"
        self.poster_base_url = "https://image.tmdb.org/t/p/w500"
        
    def search_movie(self, title):
        """Busca um filme pelo título."""
        endpoint = f"{self.base_url}/search/movie"
        params = {
            "api_key": self.api_key,
            "query": quote(title),
            "language": "pt-BR"
        }
        
        response = requests.get(endpoint, params=params)
        if response.status_code == 200:
            results = response.json().get("results", [])
            return results[:5] if results else []  # Retorna os primeiros 5 resultados
        return []
    
    def get_movie_details(self, movie_id):
        """Obtém detalhes completos de um filme pelo ID."""
        endpoint = f"{self.base_url}/movie/{movie_id}"
        params = {
            "api_key": self.api_key,
            "language": "pt-BR",
            "append_to_response": "credits,videos"
        }
        
        response = requests.get(endpoint, params=params)
        if response.status_code == 200:
            return response.json()
        return None
    
    def download_poster(self, poster_path, movie_id):
        """Baixa o poster do filme e salva localmente."""
        if not poster_path:
            return None
            
        poster_url = f"{self.poster_base_url}{poster_path}"
        local_path = f"assets/poster_images/{movie_id}.jpg"
        
        response = requests.get(poster_url, stream=True)
        if response.status_code == 200:
            with open(local_path, 'wb') as f:
                shutil.copyfileobj(response.raw, f)
            return local_path
        return None
        
    def extract_movie_info(self, movie_data):
        """Extrai informações relevantes do filme."""
        directors = []
        cast = []
        
        if "credits" in movie_data:
            directors = [person["name"] for person in movie_data["credits"].get("crew", []) 
                         if person["job"] == "Director"]
            cast = [person["name"] for person in movie_data["credits"].get("cast", [])[:5]]
        
        # Obter trailer do YouTube se disponível
        trailer_key = None
        if "videos" in movie_data and movie_data["videos"].get("results"):
            for video in movie_data["videos"]["results"]:
                if video["site"] == "YouTube" and video["type"] == "Trailer":
                    trailer_key = video["key"]
                    break
        
        return {
            "id": movie_data["id"],
            "title": movie_data["title"],
            "original_title": movie_data["original_title"],
            "release_date": movie_data["release_date"],
            "overview": movie_data["overview"],
            "poster_path": movie_data["poster_path"],
            "genres": [genre["name"] for genre in movie_data.get("genres", [])],
            "runtime": movie_data.get("runtime"),
            "vote_average": movie_data.get("vote_average"),
            "directors": directors,
            "cast": cast,
            "trailer_key": trailer_key
        }
