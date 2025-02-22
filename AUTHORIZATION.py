import sys
import requests

def check_status():
    url = "https://raw.githubusercontent.com/m1caelvr/m1caelvr/refs/heads/main/key.txt"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        lines = response.text.strip().split("\n")
        config = {}
        for line in lines:
            if "=" in line:
                key, value = line.split("=")
                config[key.strip()] = value.strip().lower()

        if config.get("BOT_PGRS_TELEFONICA") == "true":
            print("BOT_PGRS_TELEFONICA execução autorizada. Prosseguindo...")
        else:
            print("BOT_PGRS_TELEFONICA execução não autorizada. Encerrando.")
            sys.exit(0)

    except Exception as e:
        print(f"Erro ao verificar o status do bot: {e}")
        sys.exit(1)