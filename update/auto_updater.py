import os
import json
import shutil
import zipfile
import fnmatch
import requests
import subprocess
import sys
from packaging import version

class AutoUpdater:
    def __init__(self, repo_owner, repo_name, current_version, app_directory=None, ignore_patterns=None):
        """
        Inicializa o atualizador automático.
        
        :param repo_owner: Nome do proprietário do repositório no GitHub
        :param repo_name: Nome do repositório no GitHub
        :param current_version: Versão atual do software (ex: "1.0.0")
        :param app_directory: Diretório da aplicação (padrão: diretório atual)
        :param ignore_patterns: Lista de padrões de arquivos/pastas a serem ignorados durante a atualização
        """
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.current_version = current_version
        self.app_directory = app_directory or os.getcwd()
        self.api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
        self.update_dir = os.path.join(self.app_directory, "update_temp")
        self.ignore_patterns = ignore_patterns or []
        
    def check_for_updates(self):
        """Verifica se há atualizações disponíveis."""
        try:
            print("Verificando atualizações...")
            response = requests.get(self.api_url)
            response.raise_for_status()
            
            latest_release = response.json()
            latest_version = latest_release['tag_name'].lstrip('v')
            
            if version.parse(latest_version) > version.parse(self.current_version):
                print(f"Nova versão disponível: {latest_version} (você tem: {self.current_version})")
                return latest_release
            else:
                print(f"Você já está usando a versão mais recente ({self.current_version}).")
                return None
                
        except requests.RequestException as e:
            print(f"Erro ao verificar atualizações: {e}")
            return None
    
    def download_update(self, release):
        """
        Baixa o arquivo da atualização.
        
        :param release: Informações do release mais recente
        :return: Caminho do arquivo baixado ou None em caso de falha
        """
        try:
            # Procura pelo asset .zip no release
            zip_asset = None
            for asset in release['assets']:
                if asset['name'].endswith('.zip'):
                    zip_asset = asset
                    break
            
            if not zip_asset:
                print("Nenhum arquivo .zip encontrado no release.")
                return None
            
            # Cria o diretório temporário se não existir
            if not os.path.exists(self.update_dir):
                os.makedirs(self.update_dir)
            
            # Baixa o arquivo
            download_url = zip_asset['browser_download_url']
            zip_path = os.path.join(self.update_dir, zip_asset['name'])
            
            print(f"Baixando atualização de {download_url}...")
            response = requests.get(download_url, stream=True)
            response.raise_for_status()
            
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"Download concluído: {zip_path}")
            return zip_path
            
        except (requests.RequestException, IOError) as e:
            print(f"Erro ao baixar atualização: {e}")
            return None
    
    def should_ignore_file(self, file_path):
        """
        Verifica se um arquivo deve ser ignorado durante a atualização.
        
        :param file_path: Caminho do arquivo relativo ao diretório da aplicação
        :return: True se o arquivo deve ser ignorado, False caso contrário
        """
        # Normaliza o caminho para usar separadores consistentes
        normalized_path = file_path.replace('\\', '/')
        
        # Verifica se o arquivo corresponde a algum dos padrões de ignorar
        for pattern in self.ignore_patterns:
            # Converte padrões glob para padrões fnmatch
            if fnmatch.fnmatch(normalized_path, pattern):
                print(f"Ignorando arquivo: {normalized_path} (corresponde ao padrão {pattern})")
                return True
                
        return False
    
    def install_update(self, zip_path):
        """
        Instala a atualização baixada, preservando arquivos específicos.
        
        :param zip_path: Caminho do arquivo .zip baixado
        :return: True se a atualização foi instalada com sucesso, False caso contrário
        """
        try:
            extract_dir = os.path.join(self.update_dir, "extracted")
            
            # Limpa o diretório de extração se já existir
            if os.path.exists(extract_dir):
                shutil.rmtree(extract_dir)
            
            os.makedirs(extract_dir)
            
            # Extrai o arquivo zip
            print(f"Extraindo arquivo {zip_path}...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # Cria um backup de segurança
            backup_dir = os.path.join(self.app_directory, "backup_before_update")
            if os.path.exists(backup_dir):
                shutil.rmtree(backup_dir)
            os.makedirs(backup_dir)
            
            # Faz backup dos arquivos importantes antes da atualização
            for root, dirs, files in os.walk(self.app_directory):
                # Pula os diretórios temporários e de backup
                if "update_temp" in root or "backup_before_update" in root:
                    continue
                
                # Caminho relativo dentro do diretório da aplicação
                rel_path = os.path.relpath(root, self.app_directory)
                if rel_path == ".":
                    rel_path = ""
                
                # Cria a estrutura de diretórios no backup
                if rel_path:
                    os.makedirs(os.path.join(backup_dir, rel_path), exist_ok=True)
                
                # Copia os arquivos importantes para o backup
                for file in files:
                    src_file = os.path.join(root, file)
                    rel_file_path = os.path.join(rel_path, file) if rel_path else file
                    
                    # Se for um arquivo que deve ser preservado, faz backup
                    if self.should_ignore_file(rel_file_path):
                        dst_file = os.path.join(backup_dir, rel_file_path)
                        shutil.copy2(src_file, dst_file)
            
            print("Instalando atualização...")
            
            # Atualiza os arquivos da aplicação
            for root, dirs, files in os.walk(extract_dir):
                # Caminho relativo dentro do diretório extraído
                rel_path = os.path.relpath(root, extract_dir)
                if rel_path == ".":
                    rel_path = ""
                
                # Diretório de destino na aplicação
                dst_dir = os.path.join(self.app_directory, rel_path) if rel_path else self.app_directory
                os.makedirs(dst_dir, exist_ok=True)
                
                # Copia os arquivos da atualização para a aplicação
                for file in files:
                    src_file = os.path.join(root, file)
                    rel_file_path = os.path.join(rel_path, file) if rel_path else file
                    dst_file = os.path.join(dst_dir, file)
                    
                    # Não sobrescreve arquivos que devem ser preservados
                    if not self.should_ignore_file(rel_file_path):
                        if os.path.exists(dst_file):
                            os.remove(dst_file)
                        shutil.copy2(src_file, dst_file)
            
            # Restaura os arquivos preservados do backup
            for root, dirs, files in os.walk(backup_dir):
                rel_path = os.path.relpath(root, backup_dir)
                if rel_path == ".":
                    rel_path = ""
                
                dst_dir = os.path.join(self.app_directory, rel_path) if rel_path else self.app_directory
                
                for file in files:
                    src_file = os.path.join(root, file)
                    rel_file_path = os.path.join(rel_path, file) if rel_path else file
                    
                    # Se for um arquivo que deve ser preservado, restaura do backup
                    if self.should_ignore_file(rel_file_path):
                        dst_file = os.path.join(dst_dir, file)
                        if os.path.exists(dst_file):
                            os.remove(dst_file)
                        shutil.copy2(src_file, dst_file)
            
            # Atualiza o arquivo de versão com a nova versão
            new_version = release['tag_name'].lstrip('v')
            with open(os.path.join(self.app_directory, "version.json"), "w") as f:
                json.dump({"version": new_version}, f)
            
            print(f"Atualização para a versão {new_version} instalada com sucesso!")
            
            # Limpa os arquivos temporários
            self.cleanup()
            
            return True
            
        except Exception as e:
            print(f"Erro ao instalar atualização: {e}")
            self.cleanup()
            return False
    
    def cleanup(self):
        """Remove os arquivos temporários de atualização."""
        try:
            if os.path.exists(self.update_dir):
                shutil.rmtree(self.update_dir)
        except Exception as e:
            print(f"Erro ao limpar arquivos temporários: {e}")
    
    def update(self):
        """Executa o processo completo de atualização."""
        release = self.check_for_updates()
        if not release:
            return False
        
        zip_path = self.download_update(release)
        if not zip_path:
            return False
        
        return self.install_update(zip_path)
