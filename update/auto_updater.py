import os
import json
import shutil
import zipfile
import requests
import subprocess
from packaging import version

class AutoUpdater:
    def __init__(self, repo_owner, repo_name, current_version, app_directory=None):
        """
        Inicializa o atualizador automático.
        
        :param repo_owner: Nome do proprietário do repositório no GitHub
        :param repo_name: Nome do repositório no GitHub
        :param current_version: Versão atual do software (ex: "1.0.0")
        :param app_directory: Diretório da aplicação (padrão: diretório atual)
        """
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.current_version = current_version
        self.app_directory = app_directory or os.getcwd()
        self.api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
        self.update_dir = os.path.join(self.app_directory, "update_temp")
        
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
    
    def install_update(self, zip_path):
        """
        Instala a atualização baixada.
        
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
            
            # Atualiza os arquivos (exemplo simples - você pode precisar personalizar esta parte)
            print("Instalando atualização...")
            
            # Opção 1: Copia os arquivos extraídos para o diretório da aplicação
            # (exclui alguns diretórios/arquivos especiais que não devem ser substituídos)
            for item in os.listdir(extract_dir):
                src_path = os.path.join(extract_dir, item)
                dst_path = os.path.join(self.app_directory, item)
                
                if os.path.isdir(src_path):
                    if os.path.exists(dst_path):
                        shutil.rmtree(dst_path)
                    shutil.copytree(src_path, dst_path)
                else:
                    if os.path.exists(dst_path):
                        os.remove(dst_path)
                    shutil.copy2(src_path, dst_path)
            
            # Atualiza o arquivo de versão
            with open(os.path.join(self.app_directory, "version.json"), "w") as f:
                json.dump({"version": release['tag_name'].lstrip('v')}, f)
            
            print("Atualização instalada com sucesso!")
            
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

# Exemplo de uso
if __name__ == "__main__":
    # Obtém a versão atual do arquivo version.json
    try:
        with open("version.json", "r") as f:
            current_version = json.load(f)["version"]
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        current_version = "0.0.1"  # Versão padrão caso não exista arquivo
    
    # Configuração do atualizador
    updater = AutoUpdater(
        repo_owner="gabrieloliveira64",
        repo_name="PipocaApp",
        current_version=current_version
    )
    
    # Executa a atualização
    if updater.update():
        print("Programa atualizado. Reiniciando...")
        # Reinicia o programa (opcional)
        python = sys.executable
        os.execl(python, python, *sys.argv)
    else:
        print("Nenhuma atualização foi instalada.")
