import os
import logging
import uvicorn
import argparse
import subprocess
from time import sleep
from dotenv import load_dotenv, find_dotenv


########################
# Arguments
########################
args = argparse.ArgumentParser()

# """Application, host, and port (eg: modules.search:app)"""
args.add_argument("--app", type=str, default="app.app:app")
args.add_argument("--host", type=str, default="0.0.0.0")
args.add_argument("--port", type=int, default=8000)

# """Development (reload + development domain)
#     * https://pypi.org/project/ngrok/0.7.0/ 
#     * https://ngrok.com/docs/using-ngrok-with/fastAPI/
# """
args.add_argument("--dev", action="store_true", default=False)
args.add_argument("--domain", type=str, default="nerdy.ngrok.io")


### Parse Arguments
args = args.parse_args()
logging.info(f"Runtime Arguments: {args}")
sleep(3)


############################
# Load Environment Variables
############################
load_dotenv(find_dotenv('.env'), override=True, verbose=True)


if args.dev:

    #####################################
    # Run Application in Development Mode
    #####################################

    logging.warning(f"""### Running in Development Mode\n\n>> https://{args.domain}\n\n""")

    CMD = ["poetry", "run", "ngrok-asgi", "uvicorn", args.app]
    ARGS = ["--port", str(args.port), "--domain", args.domain, "--reload"]

    try: subprocess.run(CMD + ARGS, check=True)
    except Exception as e: logging.error(f"An error occurred: {e}")
    finally: logging.info("Application shutdown complete.")


#####################################
# Main Application Runtime
#####################################

logging.info("### Running in Production Mode")

uvicorn.run(args.app, host=args.host, port=args.port)



