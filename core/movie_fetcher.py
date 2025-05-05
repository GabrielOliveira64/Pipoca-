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
        # Adicionando URLs base para backdrops em alta resolução
        self.backdrop_1080p_url = "https://image.tmdb.org/t/p/w1920_and_h1080_multi_faces"
        self.backdrop_720p_url = "https://image.tmdb.org/t/p/w1280"
        # URL base para fotos de perfil
        self.profile_base_url = "https://image.tmdb.org/t/p/w185"
        
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
            "append_to_response": "credits,videos,images"
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
        
        # Certifique-se de que o diretório existe
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        response = requests.get(poster_url, stream=True)
        if response.status_code == 200:
            with open(local_path, 'wb') as f:
                shutil.copyfileobj(response.raw, f)
            return local_path
        return None
    
    def download_backdrop(self, backdrop_path, movie_id):
        """Baixa a imagem de fundo do filme em resolução alta (1080p ou 720p) e salva localmente."""
        if not backdrop_path:
            return None
        
        # Tenta primeiro com 1080p
        backdrop_url = f"{self.backdrop_1080p_url}{backdrop_path}"
        local_path = f"assets/backdrop_images/{movie_id}_backdrop.jpg"
        
        # Certifique-se de que o diretório existe
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        response = requests.get(backdrop_url, stream=True)
        if response.status_code != 200:
            # Se falhar, tenta com 720p
            backdrop_url = f"{self.backdrop_720p_url}{backdrop_path}"
            response = requests.get(backdrop_url, stream=True)
        
        if response.status_code == 200:
            with open(local_path, 'wb') as f:
                shutil.copyfileobj(response.raw, f)
            return local_path
        return None
    
    def download_person_profile(self, profile_path, person_id, role):
        """Baixa a foto de perfil de um membro do elenco ou equipe e salva localmente."""
        if not profile_path:
            return None
        
        profile_url = f"{self.profile_base_url}{profile_path}"
        local_path = f"assets/profile_images/{role}_{person_id}.jpg"
        
        # Certifique-se de que o diretório existe
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        response = requests.get(profile_url, stream=True)
        if response.status_code == 200:
            with open(local_path, 'wb') as f:
                shutil.copyfileobj(response.raw, f)
            return local_path
        return None
    
    def get_person_details(self, person_id):
        """Obtém detalhes completos de uma pessoa (ator/diretor) pelo ID."""
        endpoint = f"{self.base_url}/person/{person_id}"
        params = {
            "api_key": self.api_key,
            "language": "pt-BR",
            "append_to_response": "images"
        }
        
        response = requests.get(endpoint, params=params)
        if response.status_code == 200:
            return response.json()
        return None
        
    def extract_movie_info(self, movie_data):
        """Extrai informações relevantes do filme."""
        directors = []
        cast = []
        director_profiles = []
        cast_profiles = []
        
        if "credits" in movie_data:
            # Extrai informações dos diretores
            for person in movie_data["credits"].get("crew", []):
                if person["job"] == "Director":
                    directors.append({
                        "id": person["id"],
                        "name": person["name"],
                        "profile_path": person["profile_path"]
                    })
                    
                    if person["profile_path"]:
                        # Baixa a foto do diretor
                        profile_local_path = self.download_person_profile(
                            person["profile_path"], person["id"], "director"
                        )
                        director_profiles.append({
                            "id": person["id"],
                            "name": person["name"],
                            "local_path": profile_local_path
                        })
            
            # Extrai informações do elenco (top 5)
            for person in movie_data["credits"].get("cast", [])[:5]:
                cast.append({
                    "id": person["id"],
                    "name": person["name"],
                    "character": person.get("character", ""),
                    "profile_path": person["profile_path"]
                })
                
                if person["profile_path"]:
                    # Baixa a foto do ator/atriz
                    profile_local_path = self.download_person_profile(
                        person["profile_path"], person["id"], "cast"
                    )
                    cast_profiles.append({
                        "id": person["id"],
                        "name": person["name"],
                        "local_path": profile_local_path
                    })
        
        # Obter trailer do YouTube se disponível
        trailer_key = None
        if "videos" in movie_data and movie_data["videos"].get("results"):
            for video in movie_data["videos"]["results"]:
                if video["site"] == "YouTube" and video["type"] == "Trailer":
                    trailer_key = video["key"]
                    break
        
        # Baixa o backdrop (imagem de fundo) se disponível
        backdrop_local_path = None
        if movie_data.get("backdrop_path"):
            backdrop_local_path = self.download_backdrop(
                movie_data["backdrop_path"], movie_data["id"]
            )
        
        return {
            "id": movie_data["id"],
            "title": movie_data["title"],
            "original_title": movie_data["original_title"],
            "release_date": movie_data["release_date"],
            "overview": movie_data["overview"],
            "poster_path": movie_data["poster_path"],
            "backdrop_path": movie_data.get("backdrop_path"),
            "backdrop_local_path": backdrop_local_path,
            "genres": [genre["name"] for genre in movie_data.get("genres", [])],
            "runtime": movie_data.get("runtime"),
            "vote_average": movie_data.get("vote_average"),
            "directors": directors,
            "director_profiles": director_profiles,
            "cast": cast,
            "cast_profiles": cast_profiles,
            "trailer_key": trailer_key
        }