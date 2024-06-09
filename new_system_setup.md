# New System Setup

This document will guide you through the process of setting up a new EC2 instance with our code and jupyter.

## Starting a fresh EC2 instance

1. Make sure you have `jupyter-key.pem` in your `~/.ssh` directory. If you don't have it, ask Mike for it.
2. Spin up an EC2 instance with the following settings:
    - AMI:
      - "Ubuntu Server 22.04 LTS (HVM), SSD Volume Type" `ami-03c983f9003cb9cd1` (64-bit (x86)) for development/free tier, or;
      - "Deep Learning Base OSS Nvidia Driver GPU AMI (Ubuntu 22.04)" `ami-0aff0c02a2d28cf71` (64-bit (x86)) for production
    - t2.micro (development/free tier), or g4dn.xlarge (production) -- actual instance type TBD
    - Key pair: `jupyter-key`
    - Security group: `jupyter-mk-sg`
    - Storage: 30GB (development/free tier), or 65GB (production) -- actual storage size TBD

3. SSH into the server and run the following commands:

    ```{bash}
    make remote_git_clone
    make ssh
    ```

    On the remote server:

    ```{bash}
    cd reco
    make new_setup
    ```

## After the setup, spinning up Jupyter

1. SSH into the server and run the following command:

    ```{bash}
    make ssh
    ```

    On the remote server:

    ```{bash}
    make jupyter
    ```
