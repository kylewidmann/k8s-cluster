# K3s Kubernetes Cluster Ansible

This repository contains Ansible playbooks and configurations for deploying and managing a K3s Kubernetes cluster. These playbooks automate the setup of a lightweight Kubernetes environment suitable for home labs, edge computing, or production workloads with resource constraints.

## Overview

The playbooks in this repository provide:

- Automated deployment of K3s servers (control plane nodes)
- Automated deployment of K3s agents (worker nodes)
- High availability setup with multiple server nodes using embedded etcd
- Secure network configuration using WireGuard
- Controlled node reboot capabilities
- Upgrade functionality for K3s components
- Reset functionality to clean nodes if needed

## Prerequisites

- Ansible 2.14+
- SSH access to target hosts
- Python installed on the control node
- Target hosts running a supported Linux distribution (Ubuntu/Debian recommended)
- sudo/root access on target hosts

## Repository Structure

```
clusters/k3s/ansible/
├── ansible.cfg                 # Ansible configuration
├── inventory-sample.yml        # Sample inventory file
├── playbooks
│   ├── site.yml                # Main deployment playbook
│   ├── reset.yml               # K3s reset/cleanup playbook
│   ├── reboot.yml              # Controlled node reboot playbook
│   └── upgrade.yml             # K3s upgrade playbook
└── roles
    ├── k3s_agent               # K3s agent setup role
    ├── k3s_server              # K3s server setup role
    ├── k3s_upgrade             # K3s upgrade role
    ├── network                 # Network configuration role (WireGuard)
    └── prereq                  # Prerequisites installation role
```

## Configuration

### Inventory Setup

Create your inventory file based on the provided `inventory-sample.yml`:

```yaml
k3s_cluster:
  children:
    server:
      hosts:
        192.16.35.11:
    agent:
      hosts:
        192.16.35.12:
        192.16.35.13:

  # Required Vars
  vars:
    ansible_port: 22
    ansible_user: debian
    k3s_version: v1.31.7+k3s1
    token: "your-secure-token-here"  # Generate with: openssl rand -base64 64
    api_endpoint: "{{ hostvars[groups['server'][0]]['ansible_host'] | default(groups['server'][0]) }}"
    cross_network: true  # Set to true to enable WireGuard for cross-network connectivity
```

### Key Variables

The playbooks use a combination of default variables in roles and inventory variables:

- `k3s_version`: Specific K3s version to install (e.g., `v1.31.7+k3s1`)
- `token`: Cluster token for node authentication
- `api_endpoint`: API server endpoint (defaults to first server node)
- `cross_network`: Enable WireGuard network configuration for cross-network operation
- `server_config_yaml`: YAML configuration for K3s server nodes
- `agent_config_yaml`: YAML configuration for K3s agent nodes

## Usage

### Deploy K3s Cluster

To deploy the complete K3s cluster:

```bash
ansible-playbook -i inventory.yml playbooks/site.yml
```

This playbook will:
1. Configure networking with WireGuard (if `cross_network` is true)
2. Install prerequisites on all nodes
3. Deploy K3s servers and configure HA if multiple servers defined
4. Deploy K3s agents and join them to the cluster
5. Set up kubectl access for the ansible user

### Resetting the Cluster

To remove K3s from all nodes:

```bash
ansible-playbook -i inventory.yml playbooks/reset.yml
```

This will:
1. Run the K3s uninstall scripts
2. Remove kubeconfig files
3. Clean up K3s data directories

### Rebooting Nodes

For controlled reboots of cluster nodes:

```bash
ansible-playbook -i inventory.yml playbooks/reboot.yml
```

This playbook handles graceful node rebooting:
1. Reboots server nodes one at a time (serial: 1)
2. Verifies node functionality after reboot
3. Proceeds to agent nodes after all servers are rebooted

### Upgrading K3s

To upgrade your K3s installation:

```bash
ansible-playbook -i inventory.yml playbooks/upgrade.yml -e "k3s_version=v1.31.7+k3s1"
```

This playbook:
1. Checks the current installed version
2. Downloads and installs the new version if needed
3. Preserves existing service configuration
4. Upgrades server nodes one at a time
5. Upgrades agent nodes after all servers are updated

## Networking with WireGuard

The `network` role configures secure communication between nodes using WireGuard:

- Assigns each node a 10.10.10.x IP address within the WireGuard network
- Sets up encrypted tunnels between all nodes
- Configures Flannel to use the WireGuard interface (`wg0`)
- Ensures proper routing for K3s services

This allows K3s clusters to span different networks or cloud providers while maintaining secure communication.

## Role Details

### k3s_server Role

Responsible for:
- Installing K3s binary on server nodes
- Configuring the primary server node
- Joining additional server nodes to the cluster
- Setting up TLS certificates
- Configuring the embedded etcd database (when multiple servers are present)
- Setting up kubectl for the ansible user

### k3s_agent Role

Responsible for:
- Installing K3s binary on agent nodes
- Configuring agents to connect to the server
- Setting up the K3s agent service with proper configuration

### k3s_upgrade Role

Handles the K3s version upgrade process:
- Downloads new version binaries
- Preserves existing service configurations
- Ensures proper upgrade sequencing
- Restarts services after upgrade

### network Role

Manages the network configuration for the cluster:
- Sets up WireGuard for secure cross-network communication
- Configures IP forwarding and firewall rules
- Sets up proper hostnames and /etc/hosts entries
- Ensures connectivity between nodes

### prereq Role

Installs prerequisites including:
- Container runtime dependencies
- Network utilities and kernel modules
- System configuration for K3s (sysctl settings, etc.)
- Firewall configurations (UFW or firewalld)

## Maintenance

### Backing Up etcd Data

For clusters with multiple server nodes, etcd data should be backed up regularly:

```bash
sudo k3s etcd-snapshot save
```

Snapshots are stored in `/var/lib/rancher/k3s/server/db/snapshots/`

## Advanced Configuration

### Custom K3s Server Arguments

You can customize the K3s server configuration by modifying the `server_config_yaml` variable in your inventory:

```yaml
server_config_yaml: |
  write-kubeconfig-mode: "0644"
  disable:
    - traefik
    - servicelb
  node-ip: {{ wireguard_ip }}
  node-external-ip: {{ wireguard_ip }}
  advertise-address: {{ wireguard_ip }}
  flannel-iface: wg0
```

### Custom K3s Agent Arguments

Similarly, agent nodes can be customized:

```yaml
agent_config_yaml: |
  node-external-ip: {{ wireguard_ip }}
  node-ip: {{ wireguard_ip }}
  flannel-iface: wg0
```

### Additional Options

The playbooks support many additional configuration options:

- `extra_server_args`: Additional CLI arguments for K3s server
- `extra_agent_args`: Additional CLI arguments for K3s agent
- `cluster_context`: Kubernetes context name
- `api_port`: API server port (default: 6443)
- `extra_manifests`: List of manifests to apply to the cluster
- `registries_config_yaml`: Private registry configuration

## Troubleshooting

### Logs

- K3s server logs: `sudo journalctl -u k3s`
- K3s agent logs: `sudo journalctl -u k3s-agent`
- WireGuard logs: `sudo journalctl -u wg-quick@wg0`

### Common Issues

- **Node not joining the cluster**: 
  - Check WireGuard connectivity between nodes
  - Verify the node token is correct
  - Check firewall rules (ports 6443, 8472, and 10250 must be open)

- **Etcd cluster issues**:
  - When using embedded etcd (multiple servers), ensure odd number of servers
  - Check etcd status: `sudo k3s etcd-health`

## License

This project is licensed under the MIT License - see the LICENSE file for details.