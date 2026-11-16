# Cluster setup (Ubuntu, kubeadm, containerd, Calico)

Condensed from the installation lab. Repeat steps 1-5 on **every** node, then init the master and join workers.
Example IPs: master 192.168.82.10, workers .11/.12. Keep all nodes on the same Kubernetes minor version.

## 1. Hostnames and /etc/hosts
```bash
sudo hostnamectl set-hostname k8s-master   # k8s-worker1 / k8s-worker2 on the others
echo "192.168.82.10 k8s-master
192.168.82.11 k8s-worker1
192.168.82.12 k8s-worker2" | sudo tee -a /etc/hosts
```
## 2. Swap off, kernel modules, sysctl
```bash
sudo swapoff -a && sudo sed -i '/ swap / s/^/#/' /etc/fstab
printf 'overlay\nbr_netfilter\n' | sudo tee /etc/modules-load.d/k8s.conf
sudo modprobe overlay && sudo modprobe br_netfilter
printf 'net.bridge.bridge-nf-call-iptables = 1\nnet.bridge.bridge-nf-call-ip6tables = 1\nnet.ipv4.ip_forward = 1\n' | sudo tee /etc/sysctl.d/k8s.conf
sudo sysctl --system
```
## 3. containerd (systemd cgroups)
```bash
sudo apt update && sudo apt install -y containerd
sudo mkdir -p /etc/containerd
containerd config default | sudo tee /etc/containerd/config.toml
sudo sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml
sudo systemctl restart containerd && sudo systemctl enable containerd
```
## 4. kubeadm / kubelet / kubectl (v1.34 example)
```bash
sudo apt install -y apt-transport-https ca-certificates curl gpg
sudo mkdir -p -m 755 /etc/apt/keyrings
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.34/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.34/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list
sudo apt update && sudo apt install -y kubelet kubeadm kubectl
sudo apt-mark hold kubelet kubeadm kubectl && sudo systemctl enable kubelet
```
## 5. Ports to allow between nodes
6443, 2379-2380, 10250, 10257, 10259, 30000-32767/tcp and 4789/udp (Calico VXLAN).

## 6. Master only
```bash
sudo kubeadm init --apiserver-advertise-address=192.168.82.10 --pod-network-cidr=192.168.0.0/16
mkdir -p $HOME/.kube && sudo cp /etc/kubernetes/admin.conf $HOME/.kube/config && sudo chown $(id -u):$(id -g) $HOME/.kube/config
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.29.3/manifests/tigera-operator.yaml
curl -O https://raw.githubusercontent.com/projectcalico/calico/v3.29.3/manifests/custom-resources.yaml   # cidr must be 192.168.0.0/16
kubectl create -f custom-resources.yaml
kubeadm token create --print-join-command      # run the output on each worker
```
## 7. Verify
```bash
kubectl get nodes -o wide
kubectl get pods -A
```
## 8. Optional add-ons used by this project
- Default StorageClass for the MySQL PVC (the lab used `local-path`, i.e. Rancher local-path-provisioner).
- metrics-server (for HPA / `kubectl top`), an ingress controller, MetalLB for `LoadBalancer` services on bare metal.
- On **AWS Linux** the same flow applies with EC2 security groups opened for the ports above; on EKS skip kubeadm entirely
  and use the AWS-provided control plane, `gp3` StorageClass and the AWS Load Balancer Controller.

This is a single-control-plane training cluster, not HA. The 75-task admin lab describes a 2-control-plane layout
behind an NGINX TCP load balancer (note: etcd needs 3 members to tolerate a failure).
