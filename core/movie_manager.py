import os
import json
import shutil
from datetime import datetime
import mimetypes

class MovieManager:
    """Classe para gerenciar o catálogo de filmes."""
    
    def __init__(self, catalog_path="data/catalog.json"):
        self.catalog_path = catalog_path
        self.catalog = self.load_catalog()
        
    def load_catalog(self):
        """Carrega o catálogo de filmes do arquivo JSON."""
        if os.path.exists(self.catalog_path):
            try:
                with open(self.catalog_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {"movies": []}
        return {"movies": []}
    
    def save_catalog(self):
        """Salva o catálogo de filmes no arquivo JSON."""
        with open(self.catalog_path, 'w', encoding='utf-8') as f:
            json.dump(self.catalog, f, ensure_ascii=False, indent=2)
    
    def get_all_movies(self):
        """Retorna todos os filmes do catálogo."""
        return self.catalog.get("movies", [])
    
    def get_movie_by_id(self, movie_id):
        """Busca um filme pelo ID."""
        for movie in self.catalog.get("movies", []):
            if movie.get("id") == movie_id:
                return movie
        return None
    
    def add_movie(self, movie_info, file_path):
        """Adiciona um novo filme ao catálogo."""
        movies = self.catalog.get("movies", [])
        
        # Verifica se o filme já existe no catálogo
        for i, movie in enumerate(movies):
            if movie.get("tmdb_id") == movie_info.get("id"):
                # Atualiza o filme existente
                movies[i].update({
                    "tmdb_id": movie_info.get("id"),
                    "title": movie_info.get("title"),
                    "original_title": movie_info.get("original_title"),
                    "release_date": movie_info.get("release_date"),
                    "overview": movie_info.get("overview"),
                    "local_poster_path": movie_info.get("local_poster_path"),
                    "genres": movie_info.get("genres", []),
                    "runtime": movie_info.get("runtime"),
                    "vote_average": movie_info.get("vote_average"),
                    "directors": movie_info.get("directors", []),
                    "cast": movie_info.get("cast", []),
                    "trailer_key": movie_info.get("trailer_key"),
                    "file_path": file_path,
                    "date_added": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat(),
                })
                self.save_catalog()
                return movies[i]
        
        # Adiciona um novo filme
        new_movie = {
            "id": len(movies) + 1,  # ID local
            "tmdb_id": movie_info.get("id"),
            "title": movie_info.get("title"),
            "original_title": movie_info.get("original_title"),
            "release_date": movie_info.get("release_date"),
            "overview": movie_info.get("overview"),
            "local_poster_path": movie_info.get("local_poster_path"),
            "genres": movie_info.get("genres", []),
            "runtime": movie_info.get("runtime"),
            "vote_average": movie_info.get("vote_average"),
            "directors": movie_info.get("directors", []),
            "cast": movie_info.get("cast", []),
            "trailer_key": movie_info.get("trailer_key"),
            "file_path": file_path,
            "date_added": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
        }
        movies.append(new_movie)
        self.catalog["movies"] = movies
        self.save_catalog()
        return new_movie
    
    def update_movie(self, movie_id, updated_info):
        """Atualiza as informações de um filme existente."""
        movies = self.catalog.get("movies", [])
        for i, movie in enumerate(movies):
            if movie.get("id") == movie_id:
                movies[i].update(updated_info)
                movies[i]["last_updated"] = datetime.now().isoformat()
                self.save_catalog()
                return movies[i]
        return None
    
    def delete_movie(self, movie_id):
        """Remove um filme do catálogo."""
        movies = self.catalog.get("movies", [])
        for i, movie in enumerate(movies):
            if movie.get("id") == movie_id:
                removed = movies.pop(i)
                self.catalog["movies"] = movies
                self.save_catalog()
                
                # Remover o poster se existir
                if removed.get("local_poster_path") and os.path.exists(removed["local_poster_path"]):
                    try:
                        os.remove(removed["local_poster_path"])
                    except:
                        pass
                return True
        return False
    
    def is_video_file(self, file_path):
        """Verifica se o arquivo é um vídeo."""
        if not os.path.exists(file_path):
            return False
            
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type and mime_type.startswith('video/'):
            return True
        
        # Lista de extensões de vídeo comuns
        video_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm']
        file_ext = os.path.splitext(file_path)[1].lower()
        return file_ext in video_extensions
