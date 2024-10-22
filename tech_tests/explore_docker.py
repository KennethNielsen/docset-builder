from importlib.metadata import entry_points

import docker


def create_custom_docker_images(base_image, setup_commands, new_image_name):
    client = docker.from_env()

    # Pull the base image
    client.images.pull(base_image)

    # Create and start a container
    container = client.containers.run(base_image, command="sleep infinity", detach=True)

    try:
        for command in setup_commands:
            run_command_in_container(container, command)

        container.commit(
            repository=new_image_name.split(':')[0],
            tag=new_image_name.split(':')[1] if ':' in new_image_name else 'latest'
        )
    finally:
        # Clean up: stop and remove the container
        container.stop()
        container.remove()


def run_command_in_container(container, command) -> str:
    # exit_code, output = container.exec_run(command)
    print("\n### Running command in docker:", command)
    exec_id = container.client.api.exec_create(container.id, command, stdout=True, stderr=True)[
        "Id"]
    output = container.client.api.exec_start(exec_id, stream=True)
    #exec_result = container.exec_create(command, stream=True)
    for chunk in output:
        out = chunk.decode("utf-8")
        for line in out.splitlines():
            print(">>>", line)
    exit_code = container.client.api.exec_inspect(exec_id)['ExitCode']
    if exit_code != 0:
        raise Exception(f"Command '{command}' failed with exit code {exit_code}")
    print(f"Command '{command}' executed successfully")
    return


def start_container_and_run_commands(base_image, commands) -> str:
    client = docker.from_env()
    container = client.containers.run(base_image, command="sleep infinity", detach=True)
    for command in commands:
        output = run_command_in_container(container, command)
    container.stop()
    return output



def setup():
    # Example usage
    base_image = "ubuntu:22.04"
    setup_commands = [
        "apt-get update",
        "apt-get install -y --no-install-recommends make pipx",
        "env PIPX_BIN_DIR=/usr/local/bin pipx install uv",
    ]
    new_image_name = "my-custom-ubuntu:latest"

    create_custom_docker_images(base_image, setup_commands, new_image_name)


def main():
    commands = [
        # "/bin/bash -c 'echo ${PATH}'",
        "uv --version",
        "make --version",
        # "apt-cache search curl",
        # "apt-get update",
    ]
    start_container_and_run_commands("my-custom-ubuntu:latest", commands)


if __name__ == "__main__":
    # setup()
    main()
#
# # runc("python --version")
# runc("uname -a")
# #runc("pwd")
# # runc("touch jj")
# # runc("ls")
# runc("apt-get update")
# runc("apt-get install -y curl")
# runc("sh -c 'curl -LsSf https://astral.sh/uv/install.sh|sh'")
# #runc("ls -a root")
# runc("root/.cargo/bin/uv --version")
# # runc("pwd", workdir="/home")
# # runc("ls home")
# #runc("cd root")
# #runc("pwd")
# # runc("find / -iname uv")