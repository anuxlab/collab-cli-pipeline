import docker
import os

def run_docker_container():
    client = docker.from_env()
    try:
        container = client.containers.run("deepseek-coder-v2-lite-16b-q4-0-local", detach=True)
        container_id = container.id
        with open(os.path.join("outputs/agent_runs/41135885167-1-deepseek-coder-v2-lite-16b-q4-0-local/notebook_benchmark/baseline/07_combinatorial_optimization/agent-container-21a1f42beedb47d189782286524057cb.cid"), "w") as cid_file:
            cid_file.write(container_id)
    except docker.errors.BuildError as e:
        print(f"Error building Docker image: {e}")
    except docker.errors.APIError as e:
        print(f"Error running Docker container: {e}")

run_docker_container()
