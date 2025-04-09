# MicroK8s HA Kubernetes Cluster Deployment Guide

This guide explains how to use the Ansible playbooks to deploy a self-managed Kubernetes cluster using MicroK8s with high availability (HA) support.

## Prerequisites

- Ubuntu 20.04 or later on all nodes
- SSH access to all nodes
- Sudo privileges on all nodes
- Ansible 2.16+ installed on the control machine

## Directory Structure

```
microk8s-ha-cluster/
├── inventory.yml         # Inventory file with node definitions
├── site.yml              # Main playbook
├── group_vars/
│   └── all.yml           # Variables for all hosts
```

## Configuration Steps

### 1. Configure the Inventory

Edit `inventory.yml` to add your servers:

- Under `control_plane` section, add your control plane nodes (minimum 3 for HA)
- Under `workers` section, add your worker nodes
- Update the IP addresses to match your environment

### 2. Configure Variables

Edit `group_vars/all.yml` to customize your deployment:

- Update `control_plane_ip` with the virtual IP to use for your HA control plane
- Adjust `microk8s_channel` for your desired Kubernetes version
- Modify `microk8s_addons` to enable/disable specific MicroK8s features
- Update `ansible_user` and `ansible_ssh_private_key_file` for SSH access

### 3. Run the Playbook

Execute the playbook using:

```bash
ansible-playbook -i inventory.yml site.yml
```

This will:
1. Install required packages on all nodes
2. Install MicroK8s on all nodes
3. Configure the first control plane node
4. Join additional control plane nodes
5. Configure high availability across control plane nodes
6. Join worker nodes to the cluster
7. Verify the cluster is healthy

## Accessing the Cluster

After deployment, you can access your Kubernetes cluster from any control plane node:

```bash
ssh <user>@<control-plane-node>
microk8s kubectl get nodes
```

Or you can copy the kubeconfig to your local machine:

```bash
ssh <user>@<control-plane-node> 'microk8s config' > ~/.kube/config
kubectl get nodes
```

## Adding More Nodes

To add more nodes later, update your inventory file and run:

```bash
ansible-playbook -i inventory.yml site.yml --tags add_nodes
```

## Cluster Maintenance

### Upgrading MicroK8s

To upgrade MicroK8s on all nodes:

```bash
ansible all -i inventory.yml -m command -a "snap refresh microk8s --channel=<new-channel>" -b
```

### Backing Up the Cluster

Before major changes, back up the cluster state:

```bash
ansible control_plane[0] -i inventory.yml -m command -a "microk8s kubectl get all --all-namespaces -o yaml > cluster-backup.yaml" -b
```

## Troubleshooting

### Check Cluster Status

```bash
ansible control_plane[0] -i inventory.yml -m command -a "microk8s status" -b
```

### View Cluster Logs

```bash
ansible control_plane[0] -i inventory.yml -m command -a "journalctl -u snap.microk8s.daemon-kubelet" -b
```

### Verify Node Communication

```bash
ansible all -i inventory.yml -m ping
```

## Security Considerations

- The default configuration enables only essential services
- For production deployments, consider enabling:
  - Network policies
  - RBAC controls
  - TLS certificates for inter-node communication
  - Authentication for the Kubernetes API