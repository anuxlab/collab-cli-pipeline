import os
import subprocess

# Define the Docker command
docker_command = ["docker", "run", "--cidfile", "outputs/agent_runs/41135885167-1-deepseek-coder-v2-lite-16b-q4-0-local/notebook_benchmark/baseline/06_nlp_text_classification/agent-container-05fa5cb8b19c4f59a925bc60a1d55b66.cid"]

# Run the Docker command
try:
    subprocess.run(docker_command, check=True)
except subprocess.CalledProcessError as e:
    print(f"Error: {e}")

# Check if the Docker command failed
if not os.path.exists("outputs/agent_runs/41135885167-1-deepseek-coder-v2-lite-16b-q4-0-local/notebook_benchmark/baseline/06_nlp_text_classification/agent-container-05fa5cb8b19c4f59a925bc60a1d55b66.cid"):
    print("Docker container ID file not found. Please check the Docker command and output.")
